"""FastAPI app — WhatsApp webhook, email webhook, REST API, auth."""
import os
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Depends, Form, Header
from fastapi.responses import PlainTextResponse, JSONResponse
from pydantic import BaseModel

from src.database import SessionLocal, init_db
from src.models import Workspace, User, Conversation, Ticket, TicketMessage
from src.auth import authenticate_user, register_user, create_access_token, decode_token
from src.agents import run_agent_on_ticket
from src.scheduler import sync_agent_schedules
from src.channels.whatsapp import parse_inbound, validate_twilio_signature
from src.templates.loader import load_template, create_workspace, get_template_fields

app = FastAPI(title="GestorIA API", version="1.0.0")


# ---------------------------------------------------------------------------
# Dependency: DB session
# ---------------------------------------------------------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Dependency: authenticated user from Bearer token
# ---------------------------------------------------------------------------

def current_user(authorization: Optional[str] = Header(None), db=Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return user


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    workspace_name: str
    industry: str = "custom"


@app.post("/api/auth/login")
def login(body: LoginRequest, db=Depends(get_db)):
    user = authenticate_user(body.email, body.password, db)
    if not user:
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")
    token = create_access_token(user.id, user.workspace_id)
    return {"access_token": token, "token_type": "bearer", "workspace_id": user.workspace_id}


@app.post("/api/auth/register")
def register(body: RegisterRequest, db=Depends(get_db)):
    ws = create_workspace(body.workspace_name, body.industry, plan="trial")
    try:
        user = register_user(body.email, body.password, body.full_name, ws.id, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    token = create_access_token(user.id, ws.id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "workspace_id": ws.id,
        "message": "Cuenta creada. Completa el asistente de configuración.",
    }


# ---------------------------------------------------------------------------
# Workspace / setup endpoints
# ---------------------------------------------------------------------------

class SetupRequest(BaseModel):
    industry: str
    business_info: dict


@app.post("/api/workspace/setup")
def setup_workspace(body: SetupRequest, user: User = Depends(current_user)):
    result = load_template(user.workspace_id, body.industry, body.business_info)
    sync_agent_schedules()
    return {"message": result}


@app.get("/api/workspace/template-fields/{industry}")
def template_fields(industry: str):
    fields = get_template_fields(industry)
    return {"fields": [
        {"key": f[0], "label": f[1], "placeholder": f[2]}
        for f in fields
    ]}


@app.get("/api/workspace/me")
def workspace_info(user: User = Depends(current_user), db=Depends(get_db)):
    ws = db.query(Workspace).filter(Workspace.id == user.workspace_id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace no encontrado")
    return {
        "id": ws.id,
        "name": ws.name,
        "industry": ws.industry,
        "plan": ws.plan,
        "messages_used": ws.messages_used_this_month,
        "message_limit": ws.monthly_message_limit,
        "whatsapp_number": ws.whatsapp_number,
    }


# ---------------------------------------------------------------------------
# WhatsApp webhook
# ---------------------------------------------------------------------------

@app.post("/api/webhook/whatsapp", response_class=PlainTextResponse)
async def whatsapp_webhook(request: Request, db=Depends(get_db)):
    """
    Receives inbound WhatsApp messages from Twilio.
    Creates a Ticket and triggers the agent immediately.
    """
    form = dict(await request.form())

    # Validate Twilio signature (skip in dev if env var not set)
    twilio_sig = request.headers.get("X-Twilio-Signature", "")
    base_url = os.getenv("BASE_URL", str(request.url))
    if os.getenv("TWILIO_AUTH_TOKEN"):
        if not validate_twilio_signature(base_url, form, twilio_sig):
            raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    msg = parse_inbound(form)
    if not msg["body"]:
        return "ok"  # ignore empty/media-only messages

    to_phone = msg["to_phone"]
    from_phone = msg["from_phone"]
    body = msg["body"]
    profile_name = msg.get("profile_name", "")

    # Find workspace by WhatsApp number
    ws = (
        db.query(Workspace)
        .filter(Workspace.whatsapp_number == to_phone)
        .first()
    )
    if not ws:
        # Fallback: find by partial match
        ws = db.query(Workspace).filter(
            Workspace.whatsapp_number.like(f"%{to_phone[-9:]}")
        ).first()
    if not ws or not ws.company_id:
        return "ok"  # no workspace configured for this number

    # Check message limit
    if ws.messages_used_this_month >= ws.monthly_message_limit:
        return "ok"  # quota exceeded — silently drop (or send upgrade notice)

    # Find or create Conversation
    conv = (
        db.query(Conversation)
        .filter(
            Conversation.workspace_id == ws.id,
            Conversation.channel == "whatsapp",
            Conversation.customer_identifier == from_phone,
            Conversation.status == "active",
        )
        .first()
    )

    if conv and conv.ticket_id:
        # Continue existing conversation
        ticket = db.query(Ticket).filter(Ticket.id == conv.ticket_id).first()
        if ticket and ticket.status in ("completed", "blocked"):
            ticket = None  # start fresh if previous was closed

    else:
        ticket = None

    if not ticket:
        # Find the primary customer-facing agent for this workspace
        from src.models import Agent
        agent = (
            db.query(Agent)
            .filter(Agent.company_id == ws.company_id, Agent.boss_id == None)  # noqa: E711
            .first()
        )
        if not agent:
            return "ok"

        ticket = Ticket(
            company_id=ws.company_id,
            agent_id=agent.id,
            title=f"WhatsApp de {profile_name or from_phone}",
            description=(
                f"Canal: WhatsApp\nCliente: {profile_name or 'Desconocido'}\n"
                f"Teléfono: {from_phone}"
            ),
            status="open",
        )
        db.add(ticket)
        db.flush()

        if not conv:
            conv = Conversation(
                workspace_id=ws.id,
                channel="whatsapp",
                customer_identifier=from_phone,
                customer_name=profile_name or "",
                ticket_id=ticket.id,
                status="active",
            )
            db.add(conv)
        else:
            conv.ticket_id = ticket.id

    # Add customer message to ticket thread
    db.add(TicketMessage(ticket_id=ticket.id, role="user", content=body))

    # Increment usage counter
    ws.messages_used_this_month += 1
    conv.last_message_at = datetime.utcnow()

    db.commit()

    # Run agent asynchronously (fire-and-forget in a background thread)
    import threading
    ticket_id = ticket.id
    agent_id = ticket.agent_id

    def _run():
        run_agent_on_ticket(agent_id, ticket_id)

    threading.Thread(target=_run, daemon=True).start()

    return "ok"


# ---------------------------------------------------------------------------
# Email webhook (simple HTTP POST from email forwarding service)
# ---------------------------------------------------------------------------

class EmailWebhookBody(BaseModel):
    to_email: str
    from_email: str
    from_name: str = ""
    subject: str
    body: str


@app.post("/api/webhook/email")
def email_webhook(payload: EmailWebhookBody, db=Depends(get_db)):
    """
    Receives inbound emails (e.g. from SendGrid inbound parse or Mailgun).
    """
    ws = db.query(Workspace).filter(Workspace.email == payload.to_email).first()
    if not ws or not ws.company_id:
        return {"status": "no workspace"}

    if ws.messages_used_this_month >= ws.monthly_message_limit:
        return {"status": "quota exceeded"}

    from src.models import Agent
    agent = (
        db.query(Agent)
        .filter(Agent.company_id == ws.company_id, Agent.boss_id == None)  # noqa: E711
        .first()
    )
    if not agent:
        return {"status": "no agent"}

    ticket = Ticket(
        company_id=ws.company_id,
        agent_id=agent.id,
        title=f"Email: {payload.subject[:80]}",
        description=(
            f"Canal: Email\nDe: {payload.from_name} <{payload.from_email}>\n"
            f"Asunto: {payload.subject}"
        ),
        status="open",
    )
    db.add(ticket)
    db.flush()

    db.add(TicketMessage(ticket_id=ticket.id, role="user", content=payload.body))

    conv = Conversation(
        workspace_id=ws.id,
        channel="email",
        customer_identifier=payload.from_email,
        customer_name=payload.from_name,
        ticket_id=ticket.id,
    )
    db.add(conv)
    ws.messages_used_this_month += 1
    db.commit()

    import threading
    tid, aid = ticket.id, agent.id

    def _run():
        run_agent_on_ticket(aid, tid)

    threading.Thread(target=_run, daemon=True).start()
    return {"status": "processing"}


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "service": "GestorIA"}


# ---------------------------------------------------------------------------
# Init on startup
# ---------------------------------------------------------------------------

@app.on_event("startup")
def on_startup():
    init_db()
