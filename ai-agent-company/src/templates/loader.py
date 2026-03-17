"""Apply an industry template to a Workspace — creates Company + Agents + Goals."""
import importlib
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from src.models import Company, Agent, Goal, Workspace
from src.database import SessionLocal


TEMPLATE_MAP = {
    "restaurante": "src.templates.restaurante",
    "clinica": "src.templates.clinica",
    "tienda": "src.templates.tienda",
}

PLAN_LIMITS = {
    "trial": 200,        # 14-day trial — generous enough to demo value
    "basico": 500,
    "profesional": 2000,
    "empresa": 999_999,
}


def load_template(workspace_id: int, industry: str, business_info: dict) -> str:
    """
    Instantiate a template for a workspace.
    Idempotent: safe to call multiple times (won't duplicate agents/goals).
    Returns a human-readable summary string.
    """
    if industry not in TEMPLATE_MAP:
        return (
            f"Plantilla '{industry}' no encontrada. "
            f"Opciones: {list(TEMPLATE_MAP.keys())}"
        )

    mod = importlib.import_module(TEMPLATE_MAP[industry])

    db: Session = SessionLocal()
    try:
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not workspace:
            return "Workspace no encontrado."

        nombre = business_info.get("nombre", "Mi Negocio")

        # Create or reuse company
        if workspace.company_id:
            company = db.query(Company).filter(Company.id == workspace.company_id).first()
        else:
            company = Company(
                name=nombre,
                mission=(
                    f"Proporcionar la mejor atención al cliente a los clientes de {nombre}, "
                    "respondiendo rápidamente y resolviendo sus necesidades."
                ),
            )
            db.add(company)
            db.flush()
            workspace.company_id = company.id

        # Store business info on workspace
        workspace.business_info = business_info
        workspace.industry = industry

        # ── IDEMPOTENCY: skip agents/goals if already created ──────────────
        existing_agents = (
            db.query(Agent).filter(Agent.company_id == company.id).all()
        )
        existing_names = {a.name for a in existing_agents}

        name_to_agent: dict[str, Agent] = {a.name: a for a in existing_agents}
        created_agents = 0

        for spec in mod.AGENTS:
            if spec["name"] in existing_names:
                continue  # already exists — skip

            system_prompt = (spec.get("system_prompt") or "").replace("{nombre}", nombre)
            boss_id = None
            if spec.get("boss") and spec["boss"] in name_to_agent:
                boss_id = name_to_agent[spec["boss"]].id

            agent = Agent(
                company_id=company.id,
                name=spec["name"],
                title=spec["title"],
                role_description=spec.get("role_description"),
                system_prompt=system_prompt,
                boss_id=boss_id,
                heartbeat_interval=spec.get("heartbeat_interval", 120),
                monthly_budget_usd=10.0,
                is_active=True,
            )
            db.add(agent)
            db.flush()
            name_to_agent[spec["name"]] = agent
            created_agents += 1

        existing_goals = db.query(Goal).filter(Goal.company_id == company.id).all()
        existing_goal_titles = {g.title for g in existing_goals}
        title_to_goal: dict[str, Goal] = {g.title: g for g in existing_goals}
        created_goals = 0

        for spec in mod.GOALS:
            if spec["title"] in existing_goal_titles:
                continue

            parent_id = None
            if spec.get("parent") and spec["parent"] in title_to_goal:
                parent_id = title_to_goal[spec["parent"]].id

            goal = Goal(
                company_id=company.id,
                title=spec["title"],
                description=spec.get("description"),
                level=spec.get("level", "task"),
                parent_id=parent_id,
            )
            db.add(goal)
            db.flush()
            title_to_goal[spec["title"]] = goal
            created_goals += 1

        db.commit()

        if created_agents == 0 and created_goals == 0:
            return (
                f"✅ Información actualizada para '{nombre}'.\n"
                "Los agentes ya estaban configurados — no se crearon duplicados."
            )

        agent_names = ", ".join(
            a["name"] for a in mod.AGENTS if a["name"] in name_to_agent
        )
        return (
            f"✅ Plantilla '{industry}' aplicada para '{nombre}'.\n"
            f"Agentes creados: {agent_names}.\n"
            f"Metas configuradas: {created_goals}.\n"
            "Tu equipo de IA está listo para recibir mensajes."
        )

    except Exception as e:
        db.rollback()
        return f"Error al aplicar la plantilla: {e}"
    finally:
        db.close()


def create_workspace(name: str, industry: str, plan: str = "trial") -> Workspace:
    """Create a new bare workspace (before template is applied)."""
    db = SessionLocal()
    try:
        trial_ends = datetime.now(timezone.utc) + timedelta(days=14)
        ws = Workspace(
            name=name,
            industry=industry,
            plan=plan,
            monthly_message_limit=PLAN_LIMITS.get(plan, PLAN_LIMITS["trial"]),
            trial_ends_at=trial_ends if plan == "trial" else None,
        )
        db.add(ws)
        db.commit()
        db.refresh(ws)
        return ws
    finally:
        db.close()


def get_template_fields(industry: str) -> list:
    """Return the business info fields for a given industry template."""
    if industry not in TEMPLATE_MAP:
        return []
    mod = importlib.import_module(TEMPLATE_MAP[industry])
    return getattr(mod, "BUSINESS_INFO_FIELDS", [])
