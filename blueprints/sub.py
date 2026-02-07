import logging
from asyncio import sleep
from os import environ
from random import random
from avtomatika import StateMachineBlueprint

logger = logging.getLogger("blueprints.sub")

# --- Child Blueprint Definition ---
# This blueprint will be run as a sub-process of the main one.
sub_blueprint = StateMachineBlueprint(name="metadata_enrichment")


@sub_blueprint.handler_for("start", is_start=True)
async def sub_start(context, actions):
    """Starts the sub-blueprint and might fail."""
    logger.info(
        f"[{context.job_id}] SUB-BLUEPRINT: Starting enrichment for {context.initial_data.get('video_id')}"
    )
    await sleep(0.5)  # Simulate work

    # Introduce a chance of failure (unless in deterministic mode)
    is_deterministic = environ.get("DETERMINISTIC_BLUEPRINT") == "true"
    if not is_deterministic and random() < 0.3:  # 30% chance to fail
        logger.warning(f"[{context.job_id}] SUB-BLUEPRINT: SIMULATING FAILURE.")
        actions.transition_to("sub_failed")
    else:
        actions.transition_to("finished")


@sub_blueprint.handler_for("finished", is_end=True)
async def sub_finished(context, actions):
    """Completes the sub-blueprint."""
    logger.info(f"[{context.job_id}] SUB-BLUEPRINT: Finished enrichment.")


@sub_blueprint.handler_for("sub_failed", is_end=True)
async def sub_failed(context, actions):
    """A terminal state for the failed sub-blueprint."""
    logger.info(f"[{context.job_id}] SUB-BLUEPRINT: Failed enrichment.")