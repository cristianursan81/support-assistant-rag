"""Apply an industry template to a Workspace — creates Company + Agents + Goals."""
from datetime import datetime
from sqlalchemy.orm import Session

from src.models import Company, Agent, Goal, Workspace
from src.database import SessionLocal


TEMPLATE_MAP = {
    "restaurante": "src.templates.restaurante",
    "clinica": "src.templates.clinica",
    "tienda": "src.templates.tienda",
}

PLAN_LIMITS = {
    "trial": 100,
    "basico": 500,
    "profesional": 2000,
    "empresa": 999_999,
}


def load_template(workspace_id: int, industry: str, business_info: dict) -> str:
    """
    Instantiate a template for a workspace.
    Creates the Company, Agents and Goals; links them to the workspace.
    Returns a summary string.
    """
    if industry not in TEMPLATE_MAP:
        return f"Plantilla '{industry}' no encontrada. Opciones: {list(TEMPLATE_MAP.keys())}"

    import importlib
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

        # Create agents
        name_to_agent: dict[str, Agent] = {}
        for spec in mod.AGENTS:
            system_prompt = (spec.get("system_prompt") or "").replace(
                "{nombre}", nombre
            )
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

        # Create goals
        title_to_goal: dict[str, Goal] = {}
        for spec in mod.GOALS:
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

        db.commit()

        agent_names = ", ".join(a["name"] for a in mod.AGENTS)
        return (
            f"✅ Plantilla '{industry}' aplicada para '{nombre}'.\n"
            f"Agentes creados: {agent_names}.\n"
            f"Metas configuradas: {len(mod.GOALS)}.\n"
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
        ws = Workspace(
            name=name,
            industry=industry,
            plan=plan,
            monthly_message_limit=PLAN_LIMITS.get(plan, 100),
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
    import importlib
    mod = importlib.import_module(TEMPLATE_MAP[industry])
    return getattr(mod, "BUSINESS_INFO_FIELDS", [])
