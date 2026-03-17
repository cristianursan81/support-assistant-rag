"""AI Agent Company — Gradio Dashboard"""
import gradio as gr
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from src.database import SessionLocal, init_db
from src.models import Agent, AgentEvent, Company, Goal, Ticket, TicketMessage, TokenUsage
from src.agents import run_agent_on_ticket, run_heartbeat, auto_decompose_goal
from src.scheduler import start_scheduler, stop_scheduler, sync_agent_schedules

# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _db() -> Session:
    return SessionLocal()


def _company_choices(db: Session):
    return [(f"{c.name} (#{c.id})", c.id) for c in db.query(Company).all()]


def _agent_choices(db: Session, company_id: int = None):
    q = db.query(Agent)
    if company_id:
        q = q.filter(Agent.company_id == company_id)
    return [(f"{a.name} — {a.title} (#{a.id})", a.id) for a in q.all()]


def _ticket_choices(db: Session, company_id: int = None):
    q = db.query(Ticket)
    if company_id:
        q = q.filter(Ticket.company_id == company_id)
    return [(f"#{t.id} {t.title} [{t.status}]", t.id) for t in q.order_by(Ticket.id.desc()).all()]


def _goal_choices(db: Session, company_id: int = None):
    q = db.query(Goal)
    if company_id:
        q = q.filter(Goal.company_id == company_id)
    return [(f"{g.title} [{g.level}]", g.id) for g in q.all()]


# ---------------------------------------------------------------------------
# Company tab
# ---------------------------------------------------------------------------

def create_company(name: str, mission: str):
    if not name.strip():
        return "Company name is required.", refresh_dashboard()
    db = _db()
    try:
        c = Company(name=name.strip(), mission=mission.strip())
        db.add(c)
        db.commit()
        db.refresh(c)
        return f"Company '{c.name}' created (ID #{c.id}).", refresh_dashboard()
    finally:
        db.close()


def list_companies():
    db = _db()
    try:
        companies = db.query(Company).all()
        if not companies:
            return "No companies yet."
        rows = []
        for c in companies:
            agent_count = len(c.agents)
            rows.append(f"**#{c.id} {c.name}** — {agent_count} agents\n> {c.mission or 'No mission set'}")
        return "\n\n".join(rows)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Org Chart tab
# ---------------------------------------------------------------------------

def hire_agent(company_id, name, title, role_desc, boss_id, budget, heartbeat_interval, system_prompt):
    if not company_id:
        return "Select a company first.", org_chart_md(None)
    if not name.strip() or not title.strip():
        return "Name and title are required.", org_chart_md(None)

    db = _db()
    try:
        agent = Agent(
            company_id=int(company_id),
            name=name.strip(),
            title=title.strip(),
            role_description=role_desc.strip() if role_desc else None,
            boss_id=int(boss_id) if boss_id else None,
            system_prompt=system_prompt.strip() if system_prompt else None,
            monthly_budget_usd=float(budget) if budget else 10.0,
            heartbeat_interval=int(heartbeat_interval) if heartbeat_interval else 3600,
        )
        db.add(agent)
        db.commit()
        db.refresh(agent)
        sync_agent_schedules()
        return f"Agent '{agent.name}' hired as {agent.title}.", org_chart_md(int(company_id))
    finally:
        db.close()


def org_chart_md(company_id):
    if not company_id:
        return "Select a company to view its org chart."
    db = _db()
    try:
        company = db.query(Company).filter(Company.id == int(company_id)).first()
        if not company:
            return "Company not found."

        agents = db.query(Agent).filter(Agent.company_id == int(company_id)).all()
        if not agents:
            return "No agents hired yet."

        # Build tree
        id_to_agent = {a.id: a for a in agents}
        roots = [a for a in agents if a.boss_id is None]

        def render_node(agent, depth=0):
            indent = "  " * depth
            budget_pct = (
                (agent.spent_this_month_usd / agent.monthly_budget_usd * 100)
                if agent.monthly_budget_usd > 0 else 0
            )
            status = "🟢" if agent.is_active else "🔴"
            last_hb = (
                agent.last_heartbeat.strftime("%H:%M:%S")
                if agent.last_heartbeat else "never"
            )
            line = (
                f"{indent}{status} **{agent.name}** — *{agent.title}* (#{agent.id})\n"
                f"{indent}   Budget: ${agent.spent_this_month_usd:.4f} / ${agent.monthly_budget_usd:.2f}"
                f" ({budget_pct:.1f}%) | Last heartbeat: {last_hb}"
            )
            subordinates = [a for a in agents if a.boss_id == agent.id]
            sub_lines = [render_node(sub, depth + 1) for sub in subordinates]
            return line + ("\n" + "\n".join(sub_lines) if sub_lines else "")

        return f"## {company.name} Org Chart\n\n" + "\n\n".join(render_node(r) for r in roots)
    finally:
        db.close()


def toggle_agent(agent_id):
    if not agent_id:
        return "Select an agent."
    db = _db()
    try:
        agent = db.query(Agent).filter(Agent.id == int(agent_id)).first()
        if not agent:
            return "Agent not found."
        agent.is_active = not agent.is_active
        db.commit()
        sync_agent_schedules()
        state = "activated" if agent.is_active else "deactivated"
        return f"{agent.name} {state}."
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Goals tab
# ---------------------------------------------------------------------------

def create_goal(company_id, title, description, level, parent_id):
    if not company_id or not title.strip():
        return "Company and title are required.", list_goals(company_id)
    db = _db()
    try:
        goal = Goal(
            company_id=int(company_id),
            title=title.strip(),
            description=description.strip() if description else None,
            level=level or "task",
            parent_id=int(parent_id) if parent_id else None,
        )
        db.add(goal)
        db.commit()
        return f"Goal '{goal.title}' created.", list_goals(company_id)
    finally:
        db.close()


def list_goals(company_id):
    if not company_id:
        return "Select a company."
    db = _db()
    try:
        goals = (
            db.query(Goal)
            .filter(Goal.company_id == int(company_id))
            .order_by(Goal.level, Goal.id)
            .all()
        )
        if not goals:
            return "No goals defined yet."

        level_icons = {"company": "🏢", "project": "📁", "task": "✅"}
        status_icons = {"active": "🟢", "completed": "✔️", "paused": "⏸️"}
        lines = []
        for g in goals:
            icon = level_icons.get(g.level, "•")
            sicon = status_icons.get(g.status, "")
            parent = f" ↳ parent #{g.parent_id}" if g.parent_id else ""
            lines.append(
                f"{icon} **#{g.id} {g.title}** {sicon} `{g.level}`{parent}\n"
                f"  {g.description or ''}"
            )
        return "\n\n".join(lines)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tickets tab
# ---------------------------------------------------------------------------

def create_ticket(company_id, title, description, agent_id, goal_id):
    if not company_id or not title.strip():
        return "Company and title are required.", list_tickets(company_id)
    db = _db()
    try:
        ticket = Ticket(
            company_id=int(company_id),
            title=title.strip(),
            description=description.strip() if description else None,
            agent_id=int(agent_id) if agent_id else None,
            goal_id=int(goal_id) if goal_id else None,
        )
        db.add(ticket)
        db.commit()
        return f"Ticket '#{ticket.id} {ticket.title}' created.", list_tickets(company_id)
    finally:
        db.close()


def list_tickets(company_id):
    if not company_id:
        return "Select a company."
    db = _db()
    try:
        tickets = (
            db.query(Ticket)
            .options(joinedload(Ticket.assigned_agent))
            .filter(Ticket.company_id == int(company_id))
            .order_by(Ticket.id.desc())
            .all()
        )
        if not tickets:
            return "No tickets yet."

        status_icons = {
            "open": "🔵", "in_progress": "🟡",
            "completed": "🟢", "blocked": "🔴"
        }
        lines = []
        for t in tickets:
            icon = status_icons.get(t.status, "•")
            agent_str = f" → {t.assigned_agent.name}" if t.assigned_agent else ""
            lines.append(
                f"{icon} **#{t.id} {t.title}** `{t.status}`{agent_str}\n"
                f"  {t.description or ''}"
            )
        return "\n\n".join(lines)
    finally:
        db.close()


def view_ticket_thread(ticket_id):
    if not ticket_id:
        return "Select a ticket."
    db = _db()
    try:
        ticket = db.query(Ticket).filter(Ticket.id == int(ticket_id)).first()
        if not ticket:
            return "Ticket not found."

        header = (
            f"## #{ticket.id} — {ticket.title}\n"
            f"**Status:** {ticket.status} | "
            f"**Agent:** {ticket.assigned_agent.name if ticket.assigned_agent else 'unassigned'}\n\n"
            f"**Description:** {ticket.description or 'N/A'}\n\n---\n"
        )

        if not ticket.messages:
            return header + "*No messages yet.*"

        msgs = []
        for m in ticket.messages:
            role_label = "🧑 User" if m.role == "user" else "🤖 Agent"
            ts = m.created_at.strftime("%Y-%m-%d %H:%M")
            msgs.append(f"**{role_label}** `{ts}`\n{m.content}")

        return header + "\n\n---\n\n".join(msgs)
    finally:
        db.close()


def add_user_message(ticket_id, message):
    if not ticket_id or not message.strip():
        return "Ticket and message are required.", view_ticket_thread(ticket_id)
    db = _db()
    try:
        db.add(TicketMessage(
            ticket_id=int(ticket_id),
            role="user",
            content=message.strip(),
        ))
        db.commit()
        return "Message added.", view_ticket_thread(int(ticket_id))
    finally:
        db.close()


def run_agent_now(ticket_id):
    if not ticket_id:
        return "Select a ticket.", ""
    db = _db()
    try:
        ticket = db.query(Ticket).filter(Ticket.id == int(ticket_id)).first()
        if not ticket:
            return "Ticket not found.", ""
        if not ticket.agent_id:
            return "No agent assigned to this ticket.", view_ticket_thread(int(ticket_id))
        agent_id = ticket.agent_id
    finally:
        db.close()

    result = run_agent_on_ticket(agent_id, int(ticket_id))
    return result[:500] + "..." if len(result) > 500 else result, view_ticket_thread(int(ticket_id))


def close_ticket(ticket_id):
    if not ticket_id:
        return "Select a ticket.", view_ticket_thread(ticket_id)
    db = _db()
    try:
        ticket = db.query(Ticket).filter(Ticket.id == int(ticket_id)).first()
        if not ticket:
            return "Ticket not found.", ""
        ticket.status = "completed"
        ticket.updated_at = datetime.utcnow()
        db.commit()
        return f"Ticket #{ticket_id} closed.", view_ticket_thread(int(ticket_id))
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Budget tab
# ---------------------------------------------------------------------------

def budget_report(company_id):
    if not company_id:
        return "Select a company."
    db = _db()
    try:
        agents = (
            db.query(Agent)
            .filter(Agent.company_id == int(company_id))
            .all()
        )
        if not agents:
            return "No agents found."

        lines = [f"## Budget Report\n"]
        total_spent = 0.0
        for a in agents:
            pct = (
                (a.spent_this_month_usd / a.monthly_budget_usd * 100)
                if a.monthly_budget_usd > 0 else 0
            )
            bar_filled = int(pct / 5)
            bar = "█" * bar_filled + "░" * (20 - bar_filled)
            status = "⚠️ OVER BUDGET" if pct >= 100 else ("🟡 HIGH" if pct >= 80 else "🟢 OK")
            lines.append(
                f"**{a.name}** ({a.title})\n"
                f"`{bar}` {pct:.1f}%\n"
                f"Spent: ${a.spent_this_month_usd:.4f} / Budget: ${a.monthly_budget_usd:.2f} {status}"
            )
            total_spent += a.spent_this_month_usd

        lines.append(f"\n**Total spent this month: ${total_spent:.4f}**")
        return "\n\n".join(lines)
    finally:
        db.close()


def reset_agent_budget(agent_id):
    if not agent_id:
        return "Select an agent."
    db = _db()
    try:
        agent = db.query(Agent).filter(Agent.id == int(agent_id)).first()
        if not agent:
            return "Agent not found."
        agent.spent_this_month_usd = 0.0
        db.commit()
        return f"{agent.name}'s budget reset to $0."
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Dashboard (overview)
# ---------------------------------------------------------------------------

def refresh_dashboard():
    db = _db()
    try:
        companies = db.query(Company).count()
        agents = db.query(Agent).filter(Agent.is_active == True).count()  # noqa: E712
        open_tickets = db.query(Ticket).filter(Ticket.status.in_(["open", "in_progress"])).count()
        # Use aggregate — avoids loading every row into RAM
        total_cost = db.query(func.sum(TokenUsage.cost_usd)).scalar() or 0.0

        recent_tickets = (
            db.query(Ticket)
            .options(joinedload(Ticket.assigned_agent))
            .order_by(Ticket.updated_at.desc())
            .limit(5)
            .all()
        )
        recent_lines = []
        for t in recent_tickets:
            agent_name = t.assigned_agent.name if t.assigned_agent else "unassigned"
            recent_lines.append(f"• #{t.id} **{t.title}** `{t.status}` → {agent_name}")

        return (
            f"## 🏢 AI Agent Company — Dashboard\n\n"
            f"| Metric | Value |\n"
            f"|--------|-------|\n"
            f"| Companies | {companies} |\n"
            f"| Active Agents | {agents} |\n"
            f"| Open Tickets | {open_tickets} |\n"
            f"| Total Spent | ${total_cost:.4f} |\n\n"
            f"### Recent Activity\n"
            + ("\n".join(recent_lines) if recent_lines else "*No tickets yet.*")
        )
    finally:
        db.close()


def trigger_heartbeat(agent_id):
    if not agent_id:
        return "Select an agent."
    result = run_heartbeat(int(agent_id))
    return result


# ---------------------------------------------------------------------------
# Activity Feed
# ---------------------------------------------------------------------------

_EVENT_ICONS = {
    "heartbeat_start": "💓",
    "tool_call": "🔧",
    "delegation": "📤",
    "goal_created": "🎯",
    "status_change": "🔄",
    "escalation": "🚨",
    "decompose_start": "🧩",
    "budget_exceeded": "💸",
    "error": "❌",
}


def activity_feed(company_id, limit=50):
    if not company_id:
        return "Select a company."
    db = _db()
    try:
        events = (
            db.query(AgentEvent)
            .options(joinedload(AgentEvent.agent))
            .filter(AgentEvent.company_id == int(company_id))
            .order_by(AgentEvent.created_at.desc())
            .limit(int(limit))
            .all()
        )
        if not events:
            return "*No agent activity yet. Run an agent to see events here.*"

        lines = [f"## Activity Feed (last {len(events)} events)\n"]
        for e in events:
            icon = _EVENT_ICONS.get(e.event_type, "•")
            ts = e.created_at.strftime("%m-%d %H:%M:%S")
            agent_name = e.agent.name if e.agent else f"#{e.agent_id}"
            ticket_ref = f" [ticket #{e.ticket_id}]" if e.ticket_id else ""
            lines.append(
                f"{icon} `{ts}` **{agent_name}** — {e.summary}{ticket_ref}"
            )
        return "\n\n".join(lines)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Goal auto-decompose
# ---------------------------------------------------------------------------

def do_auto_decompose(goal_id, agent_id, company_id):
    if not goal_id or not agent_id:
        return "Select both a goal and an orchestrator agent.", ""
    result = auto_decompose_goal(int(goal_id), int(agent_id))
    return result, list_goals(company_id)


# ---------------------------------------------------------------------------
# Setup Wizard (GestorIA)
# ---------------------------------------------------------------------------

def setup_wizard_apply(workspace_id, industry, business_info_json, whatsapp_number, email_address):
    """Apply an industry template to an explicitly selected workspace."""
    from src.templates.loader import load_template
    from src.models import Workspace
    from datetime import timezone
    import json as _json

    if not industry:
        return "Selecciona un sector."

    try:
        info = _json.loads(business_info_json) if business_info_json.strip() else {}
    except Exception:
        return "El JSON de información del negocio no es válido. Verifica la sintaxis."

    db = _db()
    try:
        # Use the explicitly selected workspace — never .first()
        if workspace_id:
            ws = db.query(Workspace).filter(Workspace.id == int(workspace_id)).first()
        else:
            # No workspaces exist yet — create a demo one
            from src.templates.loader import PLAN_LIMITS
            from datetime import timedelta
            ws = Workspace(
                name=info.get("nombre", "Mi Negocio"),
                industry=industry,
                plan="trial",
                monthly_message_limit=PLAN_LIMITS["trial"],
                trial_ends_at=datetime.now(timezone.utc) + timedelta(days=14),
            )
            db.add(ws)
            db.flush()

        if not ws:
            return "Workspace no encontrado. Crea una cuenta primero."

        if whatsapp_number.strip():
            ws.whatsapp_number = whatsapp_number.strip()
        if email_address.strip():
            ws.email = email_address.strip()
        db.commit()
        ws_id = ws.id
    finally:
        db.close()

    result = load_template(ws_id, industry, info)
    from src.scheduler import sync_agent_schedules
    sync_agent_schedules()
    return result


def _workspace_choices():
    """Return (label, id) list of all workspaces for the wizard selector."""
    from src.models import Workspace
    db = _db()
    try:
        workspaces = db.query(Workspace).order_by(Workspace.id).all()
        return [(f"{ws.name} (#{ws.id}) [{ws.plan}]", ws.id) for ws in workspaces]
    finally:
        db.close()


def get_template_fields_md(industry):
    """Return a markdown guide for what to include in the business_info JSON."""
    from src.templates.loader import get_template_fields
    fields = get_template_fields(industry)
    if not fields:
        return "Selecciona un sector para ver los campos recomendados."
    lines = ["**Campos recomendados para `business_info` (JSON):**\n```json\n{"]
    for key, label, placeholder in fields:
        lines.append(f'  "{key}": "{placeholder}",  // {label}')
    lines.append("}\n```")
    return "\n".join(lines)


def conversations_list():
    """List recent customer conversations across all workspaces."""
    db = _db()
    try:
        from src.models import Conversation
        convs = (
            db.query(Conversation)
            .order_by(Conversation.last_message_at.desc())
            .limit(30)
            .all()
        )
        if not convs:
            return "No hay conversaciones todavía."
        icons = {"whatsapp": "📱", "email": "📧", "web": "🌐"}
        lines = []
        for c in convs:
            icon = icons.get(c.channel, "•")
            name = c.customer_name or c.customer_identifier
            ts = c.last_message_at.strftime("%d/%m %H:%M")
            status_icon = "🟢" if c.status == "active" else "⚫"
            lines.append(
                f"{status_icon} {icon} **{name}** `{c.channel}` — "
                f"último mensaje: {ts}"
                + (f" [ticket #{c.ticket_id}]" if c.ticket_id else "")
            )
        return "\n\n".join(lines)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Build Gradio UI
# ---------------------------------------------------------------------------

def build_app():
    init_db()
    start_scheduler()

    with gr.Blocks(
        title="GestorIA — IA para PYMEs",
        theme=gr.themes.Soft(primary_hue="indigo"),
        css=".gradio-container { max-width: 1100px !important; }",
    ) as demo:
        gr.Markdown("# 🤖 GestorIA")
        gr.Markdown(
            "Tu equipo de IA que atiende clientes 24/7 — por WhatsApp, email y más. "
            "Configuración en 5 minutos."
        )

        # ── Dashboard ───────────────────────────────────────────────────────
        with gr.Tab("📊 Dashboard"):
            dashboard_md = gr.Markdown(refresh_dashboard())
            with gr.Row():
                refresh_btn = gr.Button("🔄 Refresh", variant="secondary")
            refresh_btn.click(refresh_dashboard, outputs=dashboard_md)

        # ── Company ─────────────────────────────────────────────────────────
        with gr.Tab("🏢 Company"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Create Company")
                    co_name = gr.Textbox(label="Company Name", placeholder="Acme AI Corp")
                    co_mission = gr.Textbox(
                        label="Mission",
                        placeholder="Build an AI note-taking app to $1M MRR",
                        lines=2,
                    )
                    co_btn = gr.Button("Create Company", variant="primary")
                    co_status = gr.Textbox(label="Status", interactive=False)
                with gr.Column():
                    gr.Markdown("### All Companies")
                    co_list_md = gr.Markdown(list_companies())
                    co_list_btn = gr.Button("Refresh List", variant="secondary")

            co_btn.click(
                create_company,
                inputs=[co_name, co_mission],
                outputs=[co_status, dashboard_md],
            ).then(list_companies, outputs=co_list_md)
            co_list_btn.click(list_companies, outputs=co_list_md)

        # ── Org Chart ───────────────────────────────────────────────────────
        with gr.Tab("🗂️ Org Chart"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Hire Agent")
                    oc_company = gr.Dropdown(label="Company", choices=[], interactive=True)
                    ag_name = gr.Textbox(label="Agent Name", placeholder="Alice")
                    ag_title = gr.Textbox(label="Title", placeholder="CEO")
                    ag_role = gr.Textbox(label="Role Description", lines=2)
                    ag_boss = gr.Dropdown(label="Reports To (Boss)", choices=[], interactive=True)
                    ag_budget = gr.Number(label="Monthly Budget ($)", value=10.0)
                    ag_interval = gr.Number(label="Heartbeat Interval (seconds)", value=3600)
                    ag_system = gr.Textbox(label="Custom System Prompt (optional)", lines=3)
                    ag_hire_btn = gr.Button("Hire Agent", variant="primary")
                    ag_status = gr.Textbox(label="Status", interactive=False)

                with gr.Column(scale=2):
                    gr.Markdown("### Org Chart")
                    oc_chart_md = gr.Markdown("Select a company to view the org chart.")
                    oc_refresh_btn = gr.Button("Refresh Chart", variant="secondary")

                    gr.Markdown("### Agent Control")
                    ag_toggle_select = gr.Dropdown(label="Select Agent", choices=[], interactive=True)
                    ag_toggle_btn = gr.Button("Toggle Active/Inactive")
                    ag_toggle_status = gr.Textbox(label="Result", interactive=False)

            def load_org_tab():
                db = _db()
                try:
                    companies = _company_choices(db)
                    return (
                        gr.update(choices=companies, value=companies[0][1] if companies else None),
                        gr.update(choices=[]),
                        gr.update(choices=[]),
                    )
                finally:
                    db.close()

            def on_oc_company_change(company_id):
                if not company_id:
                    return gr.update(choices=[]), gr.update(choices=[]), "Select a company."
                db = _db()
                try:
                    agents = _agent_choices(db, int(company_id))
                    chart = org_chart_md(int(company_id))
                    return (
                        gr.update(choices=[("— none —", None)] + agents),
                        gr.update(choices=agents),
                        chart,
                    )
                finally:
                    db.close()

            oc_company.change(
                on_oc_company_change,
                inputs=oc_company,
                outputs=[ag_boss, ag_toggle_select, oc_chart_md],
            )
            ag_hire_btn.click(
                hire_agent,
                inputs=[oc_company, ag_name, ag_title, ag_role, ag_boss,
                        ag_budget, ag_interval, ag_system],
                outputs=[ag_status, oc_chart_md],
            )
            oc_refresh_btn.click(org_chart_md, inputs=oc_company, outputs=oc_chart_md)
            ag_toggle_btn.click(toggle_agent, inputs=ag_toggle_select, outputs=ag_toggle_status)

        # ── Goals ───────────────────────────────────────────────────────────
        with gr.Tab("🎯 Goals"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Define Goal")
                    gl_company = gr.Dropdown(label="Company", choices=[], interactive=True)
                    gl_title = gr.Textbox(label="Goal Title")
                    gl_desc = gr.Textbox(label="Description", lines=2)
                    gl_level = gr.Radio(
                        ["company", "project", "task"],
                        label="Level",
                        value="task",
                    )
                    gl_parent = gr.Dropdown(
                        label="Parent Goal (optional)", choices=[], interactive=True
                    )
                    gl_btn = gr.Button("Create Goal", variant="primary")
                    gl_status = gr.Textbox(label="Status", interactive=False)

                with gr.Column():
                    gr.Markdown("### Goals Hierarchy")
                    gl_list_md = gr.Markdown("Select a company.")
                    gl_refresh_btn = gr.Button("Refresh", variant="secondary")

                    gr.Markdown("### 🤖 Auto-Decompose")
                    gr.Markdown(
                        "Select a goal and an orchestrator agent (e.g. CEO). "
                        "Claude will break the goal into sub-goals, create tasks, and delegate them."
                    )
                    gl_decomp_goal = gr.Dropdown(
                        label="Goal to decompose", choices=[], interactive=True
                    )
                    gl_decomp_agent = gr.Dropdown(
                        label="Orchestrator Agent", choices=[], interactive=True
                    )
                    gl_decomp_btn = gr.Button("🧩 Auto-Decompose Goal", variant="primary")
                    gl_decomp_output = gr.Textbox(
                        label="Agent Output", lines=6, interactive=False
                    )

            def on_gl_company_change(company_id):
                if not company_id:
                    return (
                        gr.update(choices=[]),
                        gr.update(choices=[]),
                        gr.update(choices=[]),
                        "Select a company.",
                    )
                db = _db()
                try:
                    goals = _goal_choices(db, int(company_id))
                    agents = _agent_choices(db, int(company_id))
                    return (
                        gr.update(choices=[("— none —", None)] + goals),
                        gr.update(choices=goals),
                        gr.update(choices=agents),
                        list_goals(int(company_id)),
                    )
                finally:
                    db.close()

            gl_company.change(
                on_gl_company_change,
                inputs=gl_company,
                outputs=[gl_parent, gl_decomp_goal, gl_decomp_agent, gl_list_md],
            )
            gl_btn.click(
                create_goal,
                inputs=[gl_company, gl_title, gl_desc, gl_level, gl_parent],
                outputs=[gl_status, gl_list_md],
            ).then(
                lambda c: (
                    gr.update(choices=_goal_choices(_db(), int(c)))
                    if c else gr.update()
                ),
                inputs=gl_company,
                outputs=gl_decomp_goal,
            )
            gl_refresh_btn.click(list_goals, inputs=gl_company, outputs=gl_list_md)
            gl_decomp_btn.click(
                do_auto_decompose,
                inputs=[gl_decomp_goal, gl_decomp_agent, gl_company],
                outputs=[gl_decomp_output, gl_list_md],
            ).then(list_goals, inputs=gl_company, outputs=gl_list_md)

        # ── Tickets ─────────────────────────────────────────────────────────
        with gr.Tab("🎫 Tickets"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### New Ticket")
                    tk_company = gr.Dropdown(label="Company", choices=[], interactive=True)
                    tk_title = gr.Textbox(label="Title")
                    tk_desc = gr.Textbox(label="Description", lines=3)
                    tk_agent = gr.Dropdown(label="Assign Agent", choices=[], interactive=True)
                    tk_goal = gr.Dropdown(label="Related Goal", choices=[], interactive=True)
                    tk_create_btn = gr.Button("Create Ticket", variant="primary")
                    tk_create_status = gr.Textbox(label="Status", interactive=False)

                with gr.Column(scale=2):
                    gr.Markdown("### Ticket List")
                    tk_list_md = gr.Markdown("Select a company.")
                    tk_refresh_list_btn = gr.Button("Refresh List", variant="secondary")

                    gr.Markdown("### Ticket Thread")
                    tk_select = gr.Dropdown(label="Select Ticket", choices=[], interactive=True)
                    tk_thread_md = gr.Markdown()

                    with gr.Row():
                        tk_msg = gr.Textbox(label="Add Message", placeholder="Type instruction...")
                        tk_msg_btn = gr.Button("Send")

                    with gr.Row():
                        tk_run_btn = gr.Button("▶ Run Agent Now", variant="primary")
                        tk_close_btn = gr.Button("✅ Close Ticket")

                    tk_action_status = gr.Textbox(label="Agent Output", interactive=False, lines=3)

            def on_tk_company_change(company_id):
                if not company_id:
                    return (
                        gr.update(choices=[]),
                        gr.update(choices=[]),
                        gr.update(choices=[]),
                        "Select a company.",
                    )
                db = _db()
                try:
                    agents = _agent_choices(db, int(company_id))
                    goals = _goal_choices(db, int(company_id))
                    tickets = _ticket_choices(db, int(company_id))
                    return (
                        gr.update(choices=[("— unassigned —", None)] + agents),
                        gr.update(choices=[("— none —", None)] + goals),
                        gr.update(choices=tickets),
                        list_tickets(int(company_id)),
                    )
                finally:
                    db.close()

            tk_company.change(
                on_tk_company_change,
                inputs=tk_company,
                outputs=[tk_agent, tk_goal, tk_select, tk_list_md],
            )
            tk_create_btn.click(
                create_ticket,
                inputs=[tk_company, tk_title, tk_desc, tk_agent, tk_goal],
                outputs=[tk_create_status, tk_list_md],
            ).then(
                lambda c: gr.update(choices=_ticket_choices(_db(), int(c)) if c else []),
                inputs=tk_company,
                outputs=tk_select,
            )
            tk_select.change(view_ticket_thread, inputs=tk_select, outputs=tk_thread_md)
            tk_msg_btn.click(
                add_user_message,
                inputs=[tk_select, tk_msg],
                outputs=[tk_action_status, tk_thread_md],
            )
            tk_run_btn.click(
                run_agent_now,
                inputs=tk_select,
                outputs=[tk_action_status, tk_thread_md],
            )
            tk_close_btn.click(
                close_ticket,
                inputs=tk_select,
                outputs=[tk_action_status, tk_thread_md],
            )
            tk_refresh_list_btn.click(list_tickets, inputs=tk_company, outputs=tk_list_md)

        # ── Budget ──────────────────────────────────────────────────────────
        with gr.Tab("💰 Budget"):
            with gr.Row():
                bg_company = gr.Dropdown(label="Company", choices=[], interactive=True)
                bg_refresh_btn = gr.Button("Refresh Report", variant="secondary")
            bg_report_md = gr.Markdown("Select a company.")
            gr.Markdown("### Reset Agent Budget (new month)")
            with gr.Row():
                bg_agent_select = gr.Dropdown(label="Agent", choices=[], interactive=True)
                bg_reset_btn = gr.Button("Reset to $0", variant="stop")
            bg_reset_status = gr.Textbox(label="Status", interactive=False)

            def on_bg_company_change(company_id):
                if not company_id:
                    return gr.update(choices=[]), "Select a company."
                db = _db()
                try:
                    agents = _agent_choices(db, int(company_id))
                    return gr.update(choices=agents), budget_report(int(company_id))
                finally:
                    db.close()

            bg_company.change(
                on_bg_company_change,
                inputs=bg_company,
                outputs=[bg_agent_select, bg_report_md],
            )
            bg_refresh_btn.click(budget_report, inputs=bg_company, outputs=bg_report_md)
            bg_reset_btn.click(
                reset_agent_budget, inputs=bg_agent_select, outputs=bg_reset_status
            ).then(budget_report, inputs=bg_company, outputs=bg_report_md)

        # ── Heartbeat ───────────────────────────────────────────────────────
        with gr.Tab("💓 Heartbeat"):
            gr.Markdown(
                "Agents automatically run on their configured interval. "
                "Use this tab to trigger a heartbeat manually."
            )
            with gr.Row():
                hb_company = gr.Dropdown(label="Company", choices=[], interactive=True)
                hb_agent = gr.Dropdown(label="Agent", choices=[], interactive=True)
            hb_run_btn = gr.Button("▶ Run Heartbeat Now", variant="primary")
            hb_output = gr.Textbox(label="Output", lines=6, interactive=False)

            def on_hb_company_change(company_id):
                if not company_id:
                    return gr.update(choices=[])
                db = _db()
                try:
                    agents = _agent_choices(db, int(company_id))
                    return gr.update(choices=agents)
                finally:
                    db.close()

            hb_company.change(on_hb_company_change, inputs=hb_company, outputs=hb_agent)
            hb_run_btn.click(trigger_heartbeat, inputs=hb_agent, outputs=hb_output)

        # ── Activity Feed ────────────────────────────────────────────────────
        with gr.Tab("🔊 Activity Feed"):
            gr.Markdown(
                "Live audit log of every action taken by your agents — "
                "tool calls, delegations, goal creation, escalations, and more."
            )
            with gr.Row():
                af_company = gr.Dropdown(label="Company", choices=[], interactive=True)
                af_limit = gr.Slider(
                    minimum=10, maximum=200, value=50, step=10,
                    label="Events to show",
                )
                af_refresh_btn = gr.Button("🔄 Refresh", variant="secondary")
            af_feed_md = gr.Markdown("Select a company.")

            def on_af_company_change(company_id, limit):
                return activity_feed(company_id, limit)

            af_company.change(
                on_af_company_change,
                inputs=[af_company, af_limit],
                outputs=af_feed_md,
            )
            af_refresh_btn.click(
                activity_feed,
                inputs=[af_company, af_limit],
                outputs=af_feed_md,
            )

        # ── Conversaciones (clientes) ────────────────────────────────────────
        with gr.Tab("💬 Conversaciones"):
            gr.Markdown(
                "Historial de conversaciones con clientes por WhatsApp y email."
            )
            conv_refresh_btn = gr.Button("🔄 Actualizar", variant="secondary")
            conv_list_md = gr.Markdown(conversations_list())
            conv_refresh_btn.click(conversations_list, outputs=conv_list_md)

        # ── Asistente de Configuración ───────────────────────────────────────
        with gr.Tab("⚙️ Configuración"):
            gr.Markdown(
                "## Asistente de Configuración\n"
                "Configura tu equipo de IA en 4 pasos. "
                "El sistema creará los agentes y los pondrá a trabajar automáticamente."
            )

            gr.Markdown("### 0️⃣ Workspace")
            wz_workspace = gr.Dropdown(
                label="Selecciona tu workspace",
                choices=_workspace_choices(),
                interactive=True,
                info="Si acabas de registrarte, tu workspace aparece aquí. Si está vacío, primero crea una cuenta vía /api/auth/register.",
            )
            wz_ws_refresh = gr.Button("🔄 Actualizar lista", variant="secondary", size="sm")
            wz_ws_refresh.click(_workspace_choices, outputs=wz_workspace)

            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 1️⃣ Sector de tu negocio")
                    wz_industry = gr.Radio(
                        choices=[
                            ("🍽️ Restaurante", "restaurante"),
                            ("🏥 Clínica / Centro médico", "clinica"),
                            ("🛍️ Tienda / Retail", "tienda"),
                        ],
                        label="¿A qué se dedica tu negocio?",
                        value="restaurante",
                    )
                    wz_fields_md = gr.Markdown(get_template_fields_md("restaurante"))
                    wz_industry.change(
                        get_template_fields_md,
                        inputs=wz_industry,
                        outputs=wz_fields_md,
                    )

                with gr.Column():
                    gr.Markdown("### 2️⃣ Canales de comunicación")
                    wz_whatsapp = gr.Textbox(
                        label="Número WhatsApp Business (E.164)",
                        placeholder="+34612345678",
                    )
                    wz_email = gr.Textbox(
                        label="Email de atención al cliente",
                        placeholder="info@tunegocio.es",
                    )

            gr.Markdown("### 3️⃣ Información del negocio (JSON)")
            gr.Markdown(
                "Copia el template de arriba, rellena los valores y pégalo aquí. "
                "Esta información la usarán los agentes para responder a tus clientes."
            )
            wz_info_json = gr.Textbox(
                label="Información del negocio (JSON)",
                placeholder='{"nombre": "Mi Restaurante", "horarios": "..."}',
                lines=8,
            )

            gr.Markdown("### 4️⃣ Activar")
            wz_activate_btn = gr.Button(
                "🚀 Activar mi equipo de IA", variant="primary", scale=1
            )
            wz_result = gr.Textbox(
                label="Resultado", lines=5, interactive=False
            )

            wz_activate_btn.click(
                setup_wizard_apply,
                inputs=[wz_workspace, wz_industry, wz_info_json, wz_whatsapp, wz_email],
                outputs=wz_result,
            ).then(refresh_dashboard, outputs=dashboard_md)

        # ── Populate all dropdowns on load ───────────────────────────────────
        def load_all_companies():
            db = _db()
            try:
                choices = _company_choices(db)
                dd_update = gr.update(choices=choices, value=choices[0][1] if choices else None)
                # co_list_md is Markdown — return its content, not a dropdown update
                companies_text = list_companies()
                return dd_update, dd_update, dd_update, dd_update, dd_update, dd_update, companies_text
            finally:
                db.close()

        demo.load(
            load_all_companies,
            outputs=[oc_company, gl_company, tk_company, bg_company, hb_company, af_company, co_list_md],
        ).then(refresh_dashboard, outputs=dashboard_md)

    return demo


def main():
    demo = build_app()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7861,
        show_error=True,
    )


if __name__ == "__main__":
    main()
