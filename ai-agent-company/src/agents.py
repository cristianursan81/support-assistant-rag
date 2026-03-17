"""Agent execution — agentic loop with tool use."""
import os
import anthropic
from datetime import datetime
from sqlalchemy.orm import Session

from src.models import Agent, Ticket, TicketMessage, TokenUsage, Company, AgentEvent
from src.database import SessionLocal
from src.tools import AGENT_TOOLS, execute_tool, _log_event

# Model selection:
#   - Customer-facing tickets (WhatsApp/email replies): Haiku — fast + cheap
#   - Orchestration / auto-decompose: Sonnet — smarter planning
MODEL_CUSTOMER = "claude-haiku-4-5-20251001"   # ~20x cheaper than Opus
MODEL_ORCHESTRATOR = "claude-sonnet-4-6"        # used only for auto_decompose

# Pricing per 1M tokens (approximate, update if Anthropic changes rates)
_PRICES = {
    "claude-haiku-4-5-20251001":  (0.80,  4.00),   # input, output
    "claude-sonnet-4-6":          (3.00, 15.00),
    "claude-opus-4-6":            (15.0, 75.00),
}
MAX_TOOL_ITERATIONS = 8   # hard cap per run (customer replies rarely need >4)


def _cost(input_tokens: int, output_tokens: int, model: str) -> float:
    inp_price, out_price = _PRICES.get(model, (3.00, 15.00))
    return (
        input_tokens / 1_000_000 * inp_price
        + output_tokens / 1_000_000 * out_price
    )


def _get_client() -> anthropic.Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set. Add it to your .env file.")
    return anthropic.Anthropic(api_key=api_key)


def _build_system(agent: Agent, company: Company) -> str:
    boss_line = (
        f"\nYou report to: {agent.boss.name} ({agent.boss.title})"
        if agent.boss else "\nYou are the top of the org chart — no boss to escalate to."
    )
    subs = agent.subordinates
    subs_line = (
        "\nYour direct reports: " + ", ".join(f"{s.name} ({s.title}) #{s.id}" for s in subs)
        if subs else "\nYou have no direct reports."
    )
    return f"""You are {agent.name}, {agent.title} at {company.name}.

Company Mission: {company.mission}

Your Role: {agent.role_description or 'Handle assigned tasks efficiently and effectively.'}{boss_line}{subs_line}

{agent.system_prompt or ''}

## How to work
- Start by calling list_my_tickets to see what's pending.
- For each ticket: read it, think, then act — delegate sub-tasks, update status, or complete the work.
- When you finish a ticket, call update_ticket_status with status="completed" and a clear summary.
- Delegate to direct reports when work falls under their domain. Include full context.
- If you are stuck on something that requires a decision above your pay grade, escalate to boss.
- Be decisive. Move work forward. Don't ask clarifying questions — make reasonable assumptions.
"""


def run_agent_on_ticket(
    agent_id: int,
    ticket_id: int,
    model: str = MODEL_CUSTOMER,
) -> str:
    """
    Run an agent on a specific ticket using a full agentic tool-use loop.
    Returns the agent's final text response.

    model: which Claude model to use. Default is Haiku (cheap, fast).
           Pass MODEL_ORCHESTRATOR for complex orchestration tasks.
    """
    db = SessionLocal()
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

        if not agent:
            return "Agent not found."
        if not ticket:
            return "Ticket not found."
        if not agent.is_active:
            return f"{agent.name} is inactive."
        if agent.spent_this_month_usd >= agent.monthly_budget_usd:
            return (
                f"Budget exceeded: ${agent.spent_this_month_usd:.4f}"
                f" / ${agent.monthly_budget_usd:.2f}"
            )

        company = db.query(Company).filter(Company.id == agent.company_id).first()
        system = _build_system(agent, company)
        client = _get_client()

        # Seed the conversation from the ticket
        history = []
        for m in ticket.messages:
            if m.role in ("user", "assistant"):
                history.append({"role": m.role, "content": m.content})

        if not history:
            history = [{
                "role": "user",
                "content": (
                    f"You have been assigned a ticket.\n\n"
                    f"Ticket #{ticket.id}: {ticket.title}\n\n"
                    f"{ticket.description or 'No description provided.'}\n\n"
                    "Please work on this now."
                ),
            }]

        _log_event(db, agent, "heartbeat_start",
                   f"Started working on ticket #{ticket.id}: {ticket.title}", ticket.id)
        db.commit()

        total_input_tokens = 0
        total_output_tokens = 0
        final_text = ""
        iterations = 0

        # Extended thinking only for models that support it (not Haiku)
        use_thinking = model not in (MODEL_CUSTOMER,)

        # ── Agentic tool-use loop ────────────────────────────────────────
        while iterations < MAX_TOOL_ITERATIONS:
            iterations += 1

            create_kwargs = dict(
                model=model,
                max_tokens=2048,
                system=system,
                tools=AGENT_TOOLS,
                messages=history,
            )
            if use_thinking:
                create_kwargs["thinking"] = {"type": "adaptive"}

            response = client.messages.create(**create_kwargs)

            total_input_tokens += response.usage.input_tokens
            total_output_tokens += response.usage.output_tokens

            # Append full response (preserves thinking blocks for next turn)
            history.append({"role": "assistant", "content": response.content})

            # Collect text from this turn
            turn_text = " ".join(
                b.text for b in response.content if b.type == "text"
            )
            if turn_text:
                final_text = turn_text  # keep the last meaningful text

            if response.stop_reason == "end_turn":
                break

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type != "tool_use":
                        continue

                    _log_event(db, agent, "tool_call",
                               f"Called {block.name}({block.input})", ticket.id)
                    db.commit()

                    result = execute_tool(
                        block.name, block.input, agent, ticket, db
                    )
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

                history.append({"role": "user", "content": tool_results})
                continue

            # max_tokens or other stop reason — bail out
            break

        # ── Persist usage & final message ───────────────────────────────
        cost = _cost(total_input_tokens, total_output_tokens, model)
        db.add(TokenUsage(
            agent_id=agent.id,
            ticket_id=ticket.id,
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            cost_usd=cost,
        ))
        agent.spent_this_month_usd += cost
        agent.last_heartbeat = datetime.utcnow()

        if final_text:
            db.add(TicketMessage(
                ticket_id=ticket.id,
                role="assistant",
                content=final_text,
            ))

        if ticket.status == "open":
            ticket.status = "in_progress"
        ticket.updated_at = datetime.utcnow()

        db.commit()
        return final_text or "(Agent completed work using tools — see ticket for details.)"

    except anthropic.AuthenticationError:
        return "Invalid ANTHROPIC_API_KEY."
    except anthropic.RateLimitError:
        return "Rate limit hit. Please wait and retry."
    except RuntimeError as e:
        return str(e)
    except Exception as e:
        db.rollback()
        return f"Error: {e}"
    finally:
        db.close()


def run_heartbeat(agent_id: int) -> str:
    """
    Agent heartbeat: wake up, process all pending tickets.
    Returns a summary of what was done.
    """
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
            return f"{agent.name}: no pending tickets — idle."

        ticket_ids = [t.id for t in open_tickets]
    finally:
        db.close()

    results = []
    for tid in ticket_ids:
        result = run_agent_on_ticket(agent_id, tid)
        snippet = result[:120].replace("\n", " ")
        results.append(f"  • Ticket #{tid}: {snippet}{'...' if len(result) > 120 else ''}")

    return f"{agent.name} heartbeat — processed {len(results)} ticket(s):\n" + "\n".join(results)


def auto_decompose_goal(goal_id: int, orchestrator_agent_id: int) -> str:
    """
    Ask the orchestrator agent to decompose a goal into sub-goals/tasks
    and delegate them to appropriate direct reports.
    """
    db = SessionLocal()
    try:
        from src.models import Goal
        goal = db.query(Goal).filter(Goal.id == goal_id).first()
        agent = db.query(Agent).filter(Agent.id == orchestrator_agent_id).first()

        if not goal:
            return "Goal not found."
        if not agent:
            return "Orchestrator agent not found."

        company = db.query(Company).filter(Company.id == agent.company_id).first()
        subs = agent.subordinates
        subs_desc = (
            "\n".join(f"  - {s.name} ({s.title}) #{s.id}: {s.role_description or 'no description'}"
                      for s in subs)
            if subs else "  (no direct reports)"
        )

        system = _build_system(agent, company)
        client = _get_client()

        prompt = (
            f"You have been asked to decompose and delegate the following company goal:\n\n"
            f"Goal #{goal.id}: {goal.title}\n"
            f"Level: {goal.level}\n"
            f"Description: {goal.description or 'No description.'}\n\n"
            f"Your direct reports and their domains:\n{subs_desc}\n\n"
            "Please:\n"
            "1. Use create_subgoal to break this into 2-5 sub-goals or tasks.\n"
            "2. For each task, use delegate_task to assign it to the most suitable direct report.\n"
            "3. Summarize what you've set up and why.\n\n"
            "Be concrete and decisive. Do it now."
        )

        history = [{"role": "user", "content": prompt}]

        # Create a synthetic ticket so tools have context
        synth_ticket = Ticket(
            company_id=agent.company_id,
            agent_id=agent.id,
            title=f"[Auto-decompose] {goal.title}",
            description=prompt,
            goal_id=goal.id,
            status="in_progress",
        )
        db.add(synth_ticket)
        db.flush()

        _log_event(db, agent, "decompose_start",
                   f"Auto-decomposing goal #{goal.id}: {goal.title}", synth_ticket.id)
        db.commit()

    finally:
        db.close()

    # Run the agentic loop for decomposition — use smarter model for planning
    result = run_agent_on_ticket(orchestrator_agent_id, synth_ticket.id, model=MODEL_ORCHESTRATOR)
    return result
