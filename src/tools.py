"""Tool definitions and executors for AI agents."""
from datetime import datetime
from sqlalchemy.orm import Session

from src.models import Agent, Ticket, TicketMessage, Goal, AgentEvent
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
