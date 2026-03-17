import os
import anthropic
from datetime import datetime
from sqlalchemy.orm import Session

from src.models import Agent, Ticket, TicketMessage, TokenUsage, Company
from src.database import SessionLocal

# claude-opus-4-6 pricing per 1M tokens
INPUT_PRICE_PER_1M = 5.00
OUTPUT_PRICE_PER_1M = 25.00


def calculate_cost(input_tokens: int, output_tokens: int) -> float:
    return (
        input_tokens / 1_000_000 * INPUT_PRICE_PER_1M
        + output_tokens / 1_000_000 * OUTPUT_PRICE_PER_1M
    )


def build_system_prompt(agent: Agent, company: Company) -> str:
    boss_info = ""
    if agent.boss:
        boss_info = f"\nYou report to: {agent.boss.name} ({agent.boss.title})"

    subordinate_info = ""
    if agent.subordinates:
        names = ", ".join(f"{s.name} ({s.title})" for s in agent.subordinates)
        subordinate_info = f"\nYour direct reports: {names}"

    return f"""You are {agent.name}, {agent.title} at {company.name}.

Company Mission: {company.mission}

Your Role: {agent.role_description or 'Handle assigned tasks efficiently and effectively.'}{boss_info}{subordinate_info}

{agent.system_prompt or ''}

Work on the assigned ticket thoroughly. Provide clear, actionable output.
When you complete a task, summarize what was accomplished and any next steps."""


def run_agent_on_ticket(agent_id: int, ticket_id: int) -> str:
    """Run an agent on a specific ticket. Returns the agent's response."""
    db = SessionLocal()
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

        if not agent or not ticket:
            return "Agent or ticket not found."

        if not agent.is_active:
            return f"Agent {agent.name} is not active."

        if agent.spent_this_month_usd >= agent.monthly_budget_usd:
            return (
                f"Budget exceeded: ${agent.spent_this_month_usd:.4f}"
                f" / ${agent.monthly_budget_usd:.2f}"
            )

        company = db.query(Company).filter(Company.id == agent.company_id).first()
        system = build_system_prompt(agent, company)

        # Build conversation from ticket message history
        messages = []
        for msg in ticket.messages:
            if msg.role in ("user", "assistant"):
                messages.append({"role": msg.role, "content": msg.content})

        # If no prior messages, seed from ticket description
        if not messages:
            messages = [{
                "role": "user",
                "content": (
                    f"Please work on this task:\n\n"
                    f"Title: {ticket.title}\n\n"
                    f"Description: {ticket.description or 'No description provided.'}"
                )
            }]

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return "ANTHROPIC_API_KEY not set. Please configure your .env file."

        client = anthropic.Anthropic(api_key=api_key)

        with client.messages.stream(
            model="claude-opus-4-6",
            max_tokens=4096,
            thinking={"type": "adaptive"},
            system=system,
            messages=messages,
        ) as stream:
            response = stream.get_final_message()

        response_text = next(
            (b.text for b in response.content if b.type == "text"), ""
        )

        # Record token usage
        usage = response.usage
        cost = calculate_cost(usage.input_tokens, usage.output_tokens)

        db.add(TokenUsage(
            agent_id=agent.id,
            ticket_id=ticket.id,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            cost_usd=cost,
        ))

        # Update agent spending and heartbeat
        agent.spent_this_month_usd += cost
        agent.last_heartbeat = datetime.utcnow()

        # Save agent response as ticket message
        db.add(TicketMessage(
            ticket_id=ticket.id,
            role="assistant",
            content=response_text,
        ))

        # Advance ticket status
        if ticket.status == "open":
            ticket.status = "in_progress"
        ticket.updated_at = datetime.utcnow()

        db.commit()
        return response_text

    except anthropic.AuthenticationError:
        return "Invalid ANTHROPIC_API_KEY. Check your .env file."
    except anthropic.RateLimitError:
        return "Rate limit reached. Please wait and try again."
    except Exception as e:
        db.rollback()
        return f"Error: {e}"
    finally:
        db.close()


def run_heartbeat(agent_id: int) -> str:
    """Heartbeat: agent wakes up, processes its pending tickets."""
    db = SessionLocal()
    try:
        agent = db.query(Agent).filter(
            Agent.id == agent_id, Agent.is_active == True  # noqa: E712
        ).first()

        if not agent:
            return "Agent not found or inactive."

        if agent.spent_this_month_usd >= agent.monthly_budget_usd:
            return (
                f"{agent.name} budget exhausted:"
                f" ${agent.spent_this_month_usd:.4f} / ${agent.monthly_budget_usd:.2f}"
            )

        open_tickets = (
            db.query(Ticket)
            .filter(
                Ticket.agent_id == agent_id,
                Ticket.status.in_(["open", "in_progress"]),
            )
            .limit(3)
            .all()
        )

        if not open_tickets:
            agent.last_heartbeat = datetime.utcnow()
            db.commit()
            return f"{agent.name} heartbeat: no pending tickets — idle."

        ticket_ids = [t.id for t in open_tickets]
        db.close()

        results = []
        for tid in ticket_ids:
            result = run_agent_on_ticket(agent_id, tid)
            results.append(f"  • Ticket #{tid}: processed")

        return (
            f"{agent.name} heartbeat complete.\n"
            + "\n".join(results)
        )
    except Exception as e:
        return f"Heartbeat error: {e}"
    finally:
        try:
            db.close()
        except Exception:
            pass
