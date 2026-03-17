from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.agents import run_heartbeat
from src.database import SessionLocal
from src.models import Agent

scheduler = BackgroundScheduler()


def _heartbeat_job(agent_id: int):
    result = run_heartbeat(agent_id)
    print(f"[Scheduler] Agent {agent_id}: {result}")


def sync_agent_schedules():
    """Register or update heartbeat jobs for all active agents."""
    db = SessionLocal()
    try:
        active_agents = db.query(Agent).filter(Agent.is_active == True).all()  # noqa: E712
        registered_ids = {
            int(job.id.split("_")[1])
            for job in scheduler.get_jobs()
            if job.id.startswith("agent_")
        }

        current_ids = set()
        for agent in active_agents:
            current_ids.add(agent.id)
            job_id = f"agent_{agent.id}"
            interval = max(agent.heartbeat_interval, 60)  # minimum 60s

            if agent.id not in registered_ids:
                scheduler.add_job(
                    _heartbeat_job,
                    trigger=IntervalTrigger(seconds=interval),
                    id=job_id,
                    args=[agent.id],
                    replace_existing=True,
                )
            else:
                # Update interval if changed
                scheduler.reschedule_job(
                    job_id,
                    trigger=IntervalTrigger(seconds=interval),
                )

        # Remove jobs for deactivated agents
        for old_id in registered_ids - current_ids:
            try:
                scheduler.remove_job(f"agent_{old_id}")
            except Exception:
                pass
    finally:
        db.close()


def start_scheduler():
    if not scheduler.running:
        scheduler.start()
    sync_agent_schedules()


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
