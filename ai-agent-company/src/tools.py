"""Tool definitions and executors for AI agents."""
import json
from datetime import datetime
from sqlalchemy.orm import Session

from src.models import Agent, Ticket, TicketMessage, Goal, AgentEvent, Workspace, Booking
from src.database import SessionLocal

# ---------------------------------------------------------------------------
# Tool schemas for Claude API
# ---------------------------------------------------------------------------

AGENT_TOOLS = [
    {
        "name": "list_my_tickets",
        "description": (
            "List all open tickets currently assigned to you. "
            "Use this at the start of a heartbeat to understand what work is pending."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "read_ticket",
        "description": "Read the full details and message thread of a specific ticket.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticket_id": {
                    "type": "integer",
                    "description": "The ID of the ticket to read.",
                }
            },
            "required": ["ticket_id"],
        },
    },
    {
        "name": "delegate_task",
        "description": (
            "Create a new ticket and assign it to one of your direct reports. "
            "Use this to break work into sub-tasks and delegate them. "
            "You can only delegate to agents who report directly to you."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Clear, concise title for the task.",
                },
                "description": {
                    "type": "string",
                    "description": "Detailed description of what needs to be done and why.",
                },
                "subordinate_agent_id": {
                    "type": "integer",
                    "description": "The ID of the direct report to assign this task to.",
                },
            },
            "required": ["title", "description", "subordinate_agent_id"],
        },
    },
    {
        "name": "update_ticket_status",
        "description": (
            "Update the status of a ticket you own or are working on. "
            "Mark as 'completed' when done, 'blocked' if stuck, 'in_progress' while working."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticket_id": {
                    "type": "integer",
                    "description": "The ID of the ticket to update.",
                },
                "status": {
                    "type": "string",
                    "enum": ["open", "in_progress", "completed", "blocked"],
                    "description": "New status for the ticket.",
                },
                "notes": {
                    "type": "string",
                    "description": "Progress notes or completion summary (required when completing).",
                },
            },
            "required": ["ticket_id", "status"],
        },
    },
    {
        "name": "create_subgoal",
        "description": (
            "Break down a goal into smaller sub-goals or tasks. "
            "Use level='project' for workstreams, level='task' for individual action items."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Title of the sub-goal.",
                },
                "description": {
                    "type": "string",
                    "description": "What this sub-goal entails and how it contributes to the parent.",
                },
                "level": {
                    "type": "string",
                    "enum": ["project", "task"],
                    "description": "Use 'project' for multi-task workstreams, 'task' for single deliverables.",
                },
                "parent_goal_id": {
                    "type": "integer",
                    "description": "ID of the parent goal to nest this under.",
                },
            },
            "required": ["title", "description", "level", "parent_goal_id"],
        },
    },
    {
        "name": "escalate_to_boss",
        "description": (
            "Create a ticket for your boss, escalating a blocker or requesting a decision. "
            "Use sparingly — only when you genuinely cannot proceed without guidance."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Subject of the escalation.",
                },
                "message": {
                    "type": "string",
                    "description": "Detailed message explaining the blocker, what you've tried, and what decision is needed.",
                },
            },
            "required": ["title", "message"],
        },
    },
    # ── SME / Customer-facing tools ─────────────────────────────────────────
    {
        "name": "get_business_info",
        "description": (
            "Retrieve the business profile: opening hours, address, services, prices, and FAQs. "
            "ALWAYS call this before answering any customer question about the business."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "send_whatsapp_message",
        "description": (
            "Send a WhatsApp message to a customer phone number. "
            "Use this to respond to a customer inquiry or confirm a booking."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "to_phone": {
                    "type": "string",
                    "description": "Customer phone number in E.164 format, e.g. +34612345678",
                },
                "message": {
                    "type": "string",
                    "description": "The message text to send (max 1600 characters). Write in Spanish.",
                },
            },
            "required": ["to_phone", "message"],
        },
    },
    {
        "name": "send_email",
        "description": "Send an email to a customer.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to_email": {"type": "string", "description": "Recipient email address."},
                "subject": {"type": "string", "description": "Email subject line."},
                "body": {"type": "string", "description": "Email body text. Write in Spanish."},
            },
            "required": ["to_email", "subject", "body"],
        },
    },
    {
        "name": "check_availability",
        "description": (
            "Check whether a date/time slot is available for booking. "
            "Returns available slots near the requested time."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "Date in YYYY-MM-DD format."},
                "time": {"type": "string", "description": "Requested time in HH:MM format."},
                "service": {"type": "string", "description": "Name of the service/table/room requested."},
            },
            "required": ["date", "time"],
        },
    },
    {
        "name": "create_booking",
        "description": (
            "Create a confirmed booking/appointment for a customer. "
            "Call check_availability first to verify the slot is free."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_name": {"type": "string", "description": "Full name of the customer."},
                "date": {"type": "string", "description": "Date in YYYY-MM-DD format."},
                "time": {"type": "string", "description": "Time in HH:MM format."},
                "service": {"type": "string", "description": "Service, table, or room being booked."},
                "contact": {"type": "string", "description": "Customer phone or email for confirmation."},
                "notes": {"type": "string", "description": "Any special requests or notes."},
            },
            "required": ["customer_name", "date", "time", "service", "contact"],
        },
    },
]


# ---------------------------------------------------------------------------
# Tool executors
# ---------------------------------------------------------------------------

def execute_tool(
    tool_name: str,
    tool_input: dict,
    agent: Agent,
    current_ticket: Ticket,
    db: Session,
) -> str:
    """Execute a named tool and return a string result."""
    try:
        if tool_name == "list_my_tickets":
            return _list_my_tickets(agent, db)
        elif tool_name == "read_ticket":
            return _read_ticket(int(tool_input["ticket_id"]), db)
        elif tool_name == "delegate_task":
            return _delegate_task(
                tool_input["title"],
                tool_input["description"],
                int(tool_input["subordinate_agent_id"]),
                agent, current_ticket, db,
            )
        elif tool_name == "update_ticket_status":
            return _update_ticket_status(
                int(tool_input["ticket_id"]),
                tool_input["status"],
                tool_input.get("notes", ""),
                agent, db,
            )
        elif tool_name == "create_subgoal":
            return _create_subgoal(
                tool_input["title"],
                tool_input["description"],
                tool_input["level"],
                int(tool_input["parent_goal_id"]),
                agent, db,
            )
        elif tool_name == "escalate_to_boss":
            return _escalate_to_boss(
                tool_input["title"],
                tool_input["message"],
                agent, current_ticket, db,
            )
        # ── SME tools ──────────────────────────────────────────────────────
        elif tool_name == "get_business_info":
            return _get_business_info(agent, db)
        elif tool_name == "send_whatsapp_message":
            return _send_whatsapp(
                tool_input["to_phone"],
                tool_input["message"],
                agent, current_ticket, db,
            )
        elif tool_name == "send_email":
            return _send_email(
                tool_input["to_email"],
                tool_input["subject"],
                tool_input["body"],
                agent, current_ticket, db,
            )
        elif tool_name == "check_availability":
            return _check_availability(
                tool_input["date"],
                tool_input["time"],
                tool_input.get("service", ""),
                agent, db,
            )
        elif tool_name == "create_booking":
            return _create_booking(
                tool_input["customer_name"],
                tool_input["date"],
                tool_input["time"],
                tool_input["service"],
                tool_input["contact"],
                tool_input.get("notes", ""),
                agent, current_ticket, db,
            )
        else:
            return f"Unknown tool: {tool_name}"
    except KeyError as e:
        return f"Missing required parameter: {e}"
    except Exception as e:
        return f"Tool error ({tool_name}): {e}"


def _list_my_tickets(agent: Agent, db: Session) -> str:
    tickets = (
        db.query(Ticket)
        .filter(Ticket.agent_id == agent.id, Ticket.status.in_(["open", "in_progress"]))
        .all()
    )
    if not tickets:
        return "No open tickets assigned to you. You are idle."
    lines = [f"Your open tickets ({len(tickets)}):"]
    for t in tickets:
        goal_str = f" [goal #{t.goal_id}]" if t.goal_id else ""
        lines.append(f"  #{t.id} [{t.status}] {t.title}{goal_str}")
    return "\n".join(lines)


def _read_ticket(ticket_id: int, db: Session) -> str:
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        return f"Ticket #{ticket_id} not found."
    parts = [
        f"Ticket #{ticket.id}: {ticket.title}",
        f"Status: {ticket.status}",
        f"Description: {ticket.description or 'N/A'}",
        "--- Message Thread ---",
    ]
    for m in ticket.messages:
        parts.append(f"[{m.role.upper()}] {m.content}")
    return "\n".join(parts)


def _delegate_task(
    title: str,
    description: str,
    subordinate_agent_id: int,
    agent: Agent,
    current_ticket: Ticket,
    db: Session,
) -> str:
    sub = db.query(Agent).filter(
        Agent.id == subordinate_agent_id,
        Agent.boss_id == agent.id,
    ).first()
    if not sub:
        # List actual subordinates to help the agent correct itself
        subs = db.query(Agent).filter(Agent.boss_id == agent.id).all()
        names = ", ".join(f"{s.name} (#{s.id})" for s in subs) or "none"
        return (
            f"Agent #{subordinate_agent_id} is not your direct report. "
            f"Your direct reports are: {names}"
        )

    ticket = Ticket(
        company_id=agent.company_id,
        agent_id=subordinate_agent_id,
        title=title,
        description=f"[Delegated by {agent.name} ({agent.title})]\n\n{description}",
        goal_id=current_ticket.goal_id if current_ticket else None,
    )
    db.add(ticket)
    db.flush()

    _log_event(
        db, agent, "delegation",
        f"Delegated '{title}' → {sub.name} ({sub.title}) as ticket #{ticket.id}",
        current_ticket.id if current_ticket else None,
    )
    db.commit()
    return f"Task delegated to {sub.name}: ticket #{ticket.id} created."


def _update_ticket_status(
    ticket_id: int,
    status: str,
    notes: str,
    agent: Agent,
    db: Session,
) -> str:
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        return f"Ticket #{ticket_id} not found."

    old_status = ticket.status
    ticket.status = status
    ticket.updated_at = datetime.utcnow()

    note_text = notes or f"Status changed to {status}."
    db.add(TicketMessage(
        ticket_id=ticket_id,
        role="assistant",
        content=f"[{old_status} → {status}] {note_text}",
    ))
    _log_event(
        db, agent, "status_change",
        f"Ticket #{ticket_id} '{ticket.title}': {old_status} → {status}",
        ticket_id,
    )
    db.commit()
    return f"Ticket #{ticket_id} updated to '{status}'."


def _create_subgoal(
    title: str,
    description: str,
    level: str,
    parent_goal_id: int,
    agent: Agent,
    db: Session,
) -> str:
    parent = db.query(Goal).filter(Goal.id == parent_goal_id).first()
    if not parent:
        return f"Parent goal #{parent_goal_id} not found."

    goal = Goal(
        company_id=agent.company_id,
        title=title,
        description=description,
        level=level,
        parent_id=parent_goal_id,
    )
    db.add(goal)
    db.flush()

    _log_event(
        db, agent, "goal_created",
        f"Created {level} goal '#{goal.id} {title}' under '{parent.title}'",
    )
    db.commit()
    return f"Sub-goal created: #{goal.id} '{title}' ({level}) under '{parent.title}'."


def _escalate_to_boss(
    title: str,
    message: str,
    agent: Agent,
    current_ticket: Ticket,
    db: Session,
) -> str:
    if not agent.boss_id:
        return "You have no boss (you are the top of the org chart). Escalation not possible."

    boss = db.query(Agent).filter(Agent.id == agent.boss_id).first()
    ticket = Ticket(
        company_id=agent.company_id,
        agent_id=agent.boss_id,
        title=f"[Escalation from {agent.name}] {title}",
        description=f"Escalated by {agent.name} ({agent.title}):\n\n{message}",
    )
    db.add(ticket)
    db.flush()

    _log_event(
        db, agent, "escalation",
        f"Escalated to {boss.name}: '{title}' → ticket #{ticket.id}",
        current_ticket.id if current_ticket else None,
    )
    db.commit()
    return f"Escalated to {boss.name}: ticket #{ticket.id} created."


def _log_event(
    db: Session,
    agent: Agent,
    event_type: str,
    summary: str,
    ticket_id: int = None,
):
    db.add(AgentEvent(
        company_id=agent.company_id,
        agent_id=agent.id,
        ticket_id=ticket_id,
        event_type=event_type,
        summary=summary,
    ))


# ---------------------------------------------------------------------------
# SME tool executors
# ---------------------------------------------------------------------------

def _get_workspace_for_agent(agent: Agent, db: Session):
    """Find the Workspace linked to an agent's company."""
    return db.query(Workspace).filter(Workspace.company_id == agent.company_id).first()


def _get_business_info(agent: Agent, db: Session) -> str:
    workspace = _get_workspace_for_agent(agent, db)
    if not workspace or not workspace.business_info:
        return (
            "No business information configured yet. "
            "Ask the business owner to complete the setup wizard."
        )
    info = workspace.business_info
    parts = [f"## Información de {info.get('nombre', 'el negocio')}"]
    for key, label in [
        ("horarios", "Horarios"), ("direccion", "Dirección"),
        ("telefono", "Teléfono"), ("servicios", "Servicios"),
        ("precios", "Precios"), ("faqs", "Preguntas frecuentes"),
    ]:
        if info.get(key):
            val = info[key]
            if isinstance(val, list):
                val = "\n  - " + "\n  - ".join(str(v) for v in val)
            parts.append(f"**{label}**: {val}")
    return "\n".join(parts)


def _send_whatsapp(
    to_phone: str,
    message: str,
    agent: Agent,
    current_ticket: Ticket,
    db: Session,
) -> str:
    from src.channels.whatsapp import send_whatsapp
    ok = send_whatsapp(to_phone, message)
    result = "enviado" if ok else "error al enviar (revisa las credenciales de Twilio)"
    _log_event(
        db, agent, "whatsapp_sent",
        f"WhatsApp a {to_phone}: {message[:80]}... [{result}]",
        current_ticket.id if current_ticket else None,
    )
    db.commit()
    return f"WhatsApp {result} a {to_phone}."


def _send_email(
    to_email: str,
    subject: str,
    body: str,
    agent: Agent,
    current_ticket: Ticket,
    db: Session,
) -> str:
    from src.channels.email_channel import send_email
    ok = send_email(to_email, subject, body)
    result = "enviado" if ok else "error al enviar (revisa la configuración SMTP)"
    _log_event(
        db, agent, "email_sent",
        f"Email a {to_email}: {subject} [{result}]",
        current_ticket.id if current_ticket else None,
    )
    db.commit()
    return f"Email {result} a {to_email}."


def _check_availability(
    date: str,
    time: str,
    service: str,
    agent: Agent,
    db: Session,
) -> str:
    workspace = _get_workspace_for_agent(agent, db)
    if not workspace:
        return "Workspace not found."

    # Check existing bookings for conflicts
    conflict = (
        db.query(Booking)
        .filter(
            Booking.workspace_id == workspace.id,
            Booking.booking_date == date,
            Booking.booking_time == time,
            Booking.status == "confirmed",
        )
        .first()
    )

    if conflict:
        # Suggest nearby slots
        h, m = map(int, time.split(":"))
        alternatives = []
        for delta in [-60, -30, 30, 60]:
            total = h * 60 + m + delta
            if 0 <= total < 24 * 60:
                alternatives.append(f"{total // 60:02d}:{total % 60:02d}")
        alts = ", ".join(alternatives) if alternatives else "ninguna disponible"
        return (
            f"El horario {time} del {date} ya está ocupado. "
            f"Horas alternativas disponibles: {alts}."
        )

    return f"El horario {time} del {date} está disponible para '{service or 'reserva'}'."


def _create_booking(
    customer_name: str,
    date: str,
    time: str,
    service: str,
    contact: str,
    notes: str,
    agent: Agent,
    current_ticket: Ticket,
    db: Session,
) -> str:
    workspace = _get_workspace_for_agent(agent, db)
    if not workspace:
        return "Workspace not found."

    booking = Booking(
        workspace_id=workspace.id,
        ticket_id=current_ticket.id if current_ticket else None,
        customer_name=customer_name,
        customer_contact=contact,
        service=service,
        booking_date=date,
        booking_time=time,
        notes=notes or "",
        status="confirmed",
    )
    db.add(booking)
    db.flush()

    _log_event(
        db, agent, "booking_created",
        f"Reserva #{booking.id}: {customer_name} — {service} {date} {time}",
        current_ticket.id if current_ticket else None,
    )
    db.commit()
    return (
        f"Reserva confirmada (#{booking.id}): {customer_name}, "
        f"{service}, {date} a las {time}. Contacto: {contact}."
    )
