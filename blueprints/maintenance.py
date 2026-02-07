import logging
from asyncio import sleep
from avtomatika import StateMachineBlueprint

logger = logging.getLogger("blueprints.maintenance")

# --- Periodic Maintenance Blueprint Definition ---
maintenance_bp = StateMachineBlueprint(name="periodic_maintenance")


@maintenance_bp.handler_for("start", is_start=True)
async def maintenance_start(context, actions):
    """Starts the maintenance task."""
    logger.info(f"[{context.job_id}] MAINTENANCE: Starting scheduled maintenance task...")
    # Simulate some cleanup work
    await sleep(0.2)
    actions.transition_to("generate_report")


@maintenance_bp.handler_for("generate_report")
async def generate_report(context, actions):
    """Generates a system report."""
    logger.info(f"[{context.job_id}] MAINTENANCE: Generating system report...")
    # In a real scenario, this might query the DB and email admins
    actions.transition_to("finished")


@maintenance_bp.handler_for("finished", is_end=True)
async def maintenance_finished(context, actions):
    """Completes the maintenance task."""
    logger.info(f"[{context.job_id}] MAINTENANCE: Maintenance task completed successfully.")