"""FastAPI app — WhatsApp webhook, email webhook, REST API, auth."""
import os
import time
import threading
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, JSONResponse
from pydantic import BaseModel

from src.database import SessionLocal, init_db
from src.models import Workspace, User, Conversation, Ticket, TicketMessage, Agent
from src.auth import authenticate_user, create_access_token, decode_token, hash_password
from src.agents import run_agent_on_ticket, MODEL_CUSTOMER
from src.scheduler import sync_agent_schedules
from src.channels.whatsapp import parse_inbound, validate_twilio_signature
from src.templates.loader import load_template, PLAN_LIMITS, get_template_fields


# ---------------------------------------------------------------------------
# Simple in-process rate limiter for auth endpoints
# ---------------------------------------------------------------------------

_login_attempts: dict[str, list[float]] = defaultdict(list)
_login_lock = threading.Lock()
_RATE_WINDOW = 300   # 5 minutes
_RATE_MAX = 10       # max attempts per window per IP


def _check_rate_limit(ip: str):
    now = time.time()
    with _login_lock:
        attempts = [t for t in _login_attempts[ip] if now - t < _RATE_WINDOW]
        attempts.append(now)
        _login_attempts[ip] = attempts
        if len(attempts) > _RATE_MAX:
            raise HTTPException(
                status_code=429,
                detail="Demasiados intentos. Espera 5 minutos.",
            )


# ---------------------------------------------------------------------------
# Lifespan (replaces deprecated @app.on_event)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="GestorIA API", version="1.1.0", lifespan=lifespan)

# CORS — tighten origins in production via ALLOWED_ORIGINS env var
_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
def login(body: LoginRequest, request: Request, db=Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    _check_rate_limit(client_ip)
    user = authenticate_user(body.email, body.password, db)
    if not user:
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")
    token = create_access_token(user.id, user.workspace_id)
    return {"access_token": token, "token_type": "bearer", "workspace_id": user.workspace_id}


@app.post("/api/auth/register")
def register(body: RegisterRequest, db=Depends(get_db)):
    """Register a new SME customer. Creates Workspace + User in one transaction."""
    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="La contraseña debe tener mínimo 8 caracteres.")

    # Check email not already taken
    existing = db.query(User).filter(User.email == body.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Este email ya está registrado.")

    # Create Workspace + User atomically in the same DB session
    trial_ends = datetime.now(timezone.utc) + timedelta(days=14)
    ws = Workspace(
        name=body.workspace_name,
        industry=body.industry,
        plan="trial",
        monthly_message_limit=PLAN_LIMITS["trial"],
        trial_ends_at=trial_ends,
    )
    db.add(ws)
    db.flush()  # get ws.id without committing

    user = User(
        workspace_id=ws.id,
        email=body.email.lower(),
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, ws.id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "workspace_id": ws.id,
        "trial_ends_at": trial_ends.isoformat(),
        "message": "Cuenta creada. Tienes 14 días de prueba gratuita. Completa el asistente de configuración.",
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
        "trial_ends_at": ws.trial_ends_at.isoformat() if ws.trial_ends_at else None,
    }


# ---------------------------------------------------------------------------
# WhatsApp webhook
# ---------------------------------------------------------------------------

@app.post("/api/webhook/whatsapp", response_class=PlainTextResponse)
async def whatsapp_webhook(request: Request, db=Depends(get_db)):
    """
    Receives inbound WhatsApp messages from Twilio.
    Creates a Ticket and triggers the agent immediately in a background thread.
    Must return quickly (<5 s) to satisfy Twilio's webhook timeout.
    """
    form = dict(await request.form())

    # Validate Twilio signature (skip if env var not set — dev only)
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

    # Find workspace by WhatsApp number (indexed column — fast)
    ws = db.query(Workspace).filter(Workspace.whatsapp_number == to_phone).first()
    if not ws:
        # Fallback: partial match (in case user stored number without country prefix)
        ws = db.query(Workspace).filter(
            Workspace.whatsapp_number.like(f"%{to_phone[-9:]}")
        ).first()
    if not ws or not ws.company_id:
        return "ok"

    # Enforce message quota
    if ws.messages_used_this_month >= ws.monthly_message_limit:
        # Inform customer instead of silently dropping
        from src.channels.whatsapp import send_whatsapp as _send
        _send(from_phone,
              "Lo sentimos, hemos alcanzado el límite mensual de mensajes. "
              "Contacta con nosotros por teléfono.")
        return "ok"

    # Find or continue active conversation (uses composite index)
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

    ticket = None
    if conv and conv.ticket_id:
        ticket = db.query(Ticket).filter(Ticket.id == conv.ticket_id).first()
        if ticket and ticket.status in ("completed", "blocked"):
            ticket = None  # start a fresh thread

    if not ticket:
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

    # Append customer message
    db.add(TicketMessage(ticket_id=ticket.id, role="user", content=body))
    ws.messages_used_this_month += 1
    conv.last_message_at = datetime.utcnow()
    db.commit()

    # Fire-and-forget agent run — use Haiku for speed + cost
    ticket_id = ticket.id
    agent_id = ticket.agent_id

    def _run():
        run_agent_on_ticket(agent_id, ticket_id, model=MODEL_CUSTOMER)

    threading.Thread(target=_run, daemon=True).start()
    return "ok"


# ---------------------------------------------------------------------------
# Email webhook
# ---------------------------------------------------------------------------

class EmailWebhookBody(BaseModel):
    to_email: str
    from_email: str
    from_name: str = ""
    subject: str
    body: str


@app.post("/api/webhook/email")
def email_webhook(payload: EmailWebhookBody, db=Depends(get_db)):
    """Receives inbound emails from SendGrid / Mailgun inbound parse."""
    ws = db.query(Workspace).filter(Workspace.email == payload.to_email).first()
    if not ws or not ws.company_id:
        return {"status": "no workspace"}

    if ws.messages_used_this_month >= ws.monthly_message_limit:
        return {"status": "quota exceeded"}

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

    tid, aid = ticket.id, agent.id

    def _run():
        run_agent_on_ticket(aid, tid, model=MODEL_CUSTOMER)

    threading.Thread(target=_run, daemon=True).start()
    return {"status": "processing"}


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health")
def health(db=Depends(get_db)):
    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    return {"status": "ok", "service": "GestorIA", "db": db_ok}
