import logging
from typing import Any
from types import SimpleNamespace
from avtomatika import StateMachineBlueprint
from avtomatika.context import ActionFactory

logger = logging.getLogger("blueprints.main")

# --- Main Blueprint Definition ---
main_bp = StateMachineBlueprint(
    name="full_showcase",
    api_endpoint="/jobs/full_showcase",
    api_version="v1",
    data_stores={"user_prefs": {"user-123": "dark_mode"}},
)


# 1. Start State (New Handler Style)
@main_bp.handler_for("start", is_start=True)
async def start_handler(
    job_id: str,
    initial_data: dict[str, Any],
    state_history: dict[str, Any],
    actions: ActionFactory,
):
    """Initial state for each new job, demonstrating dependency injection."""
    logger.info(f"[{job_id}] START: Received job with data: {initial_data}")
    # Add some data to the state history for later steps
    state_history["video_id"] = "vid_" + job_id[:8]
    actions.transition_to("check_user_preferences")


# 2. DataStore Usage (New Handler Style)
@main_bp.handler_for("check_user_preferences")
async def check_user_prefs(
    job_id: str,
    initial_data: dict[str, Any],
    data_stores: "SimpleNamespace",
    actions: ActionFactory,
):
    """Demonstrates using the DataStore to access shared resources."""
    user_id = initial_data.get("user_id", "default_user")
    preference = await data_stores.user_prefs.get(user_id)
    logger.info(f"[{job_id}] PREFS: User '{user_id}' preference is '{preference}'.")
    actions.transition_to("pre_processing_decision")


# 3. Conditional Transitions
@main_bp.handler_for("pre_processing_decision")
async def pre_processing_decision(context, actions):
    """
    This is a dummy state. The actual logic is in the conditional handlers below,
    which are evaluated by the engine before executing a handler.
    """
    # This default handler runs if no 'when' condition is met.
    logger.info(f"[{context.job_id}] DECISION: Default pre-processing path.")
    actions.transition_to("dispatch_transcoding")


@main_bp.handler_for("pre_processing_decision").when(
    "context.initial_data.quality == 'low'"
)
async def pre_process_fast(context, actions):
    """This handler only runs if the initial data contains 'quality: 'low''."""
    logger.info(f"[{context.job_id}] DECISION: Taking FAST path for low quality video.")
    actions.transition_to("dispatch_transcoding")


@main_bp.handler_for("pre_processing_decision").when(
    "context.initial_data.needs_approval == True"
)
async def pre_process_approval(context, actions):
    """This handler only runs if the job needs manual approval first."""
    logger.info(f"[{context.job_id}] DECISION: Pausing for manual approval.")
    actions.transition_to("awaiting_approval")


@main_bp.handler_for("pre_processing_decision").when(
    "context.initial_data.use_round_robin == True"
)
async def pre_process_round_robin(context, actions):
    """This handler demonstrates the 'round_robin' dispatch strategy."""
    logger.info(
        f"[{context.job_id}] DECISION: Using 'round_robin' dispatch to cycle through workers."
    )
    actions.dispatch_task(
        task_type="analyze_file",
        params={"file_name": "round_robin_test.txt"},
        transitions={
            "success": "dispatch_transcoding",
            "failure": "transcoding_failed",
        },
        dispatch_strategy="round_robin",
    )


@main_bp.handler_for("pre_processing_decision").when(
    "context.initial_data.use_reputation == True"
)
async def pre_process_reputation(context, actions):
    """This handler demonstrates the 'best_value' dispatch strategy."""
    logger.info(
        f"[{context.job_id}] DECISION: Using 'best_value' dispatch to find the most reputable worker."
    )
    # The 'analyze_file' task can be handled by both the expensive, reliable GPU worker
    # and the cheap, unreliable CPU worker. Over time, the CPU worker's reputation will drop,
    # and the 'best_value' strategy will start preferring the GPU worker despite its higher cost.
    actions.dispatch_task(
        task_type="analyze_file",
        params={"file_name": "reputation_test.txt"},
        transitions={
            "success": "dispatch_transcoding",
            "failure": "transcoding_failed",
        },
        dispatch_strategy="best_value",
    )


@main_bp.handler_for("pre_processing_decision").when(
    "context.initial_data.use_advanced_dispatch == True"
)
async def pre_process_advanced_dispatch(context, actions):
    """This handler demonstrates advanced dispatch options."""
    logger.info(
        f"[{context.job_id}] DECISION: Using advanced dispatch to find the cheapest worker."
    )
    actions.dispatch_task(
        task_type="analyze_file",
        params={"file_name": "special_analysis.txt"},
        # Note: both workers can handle this, but cheapest should be chosen
        transitions={
            "success": "dispatch_transcoding",
            "failure": "transcoding_failed",
        },
        dispatch_strategy="cheapest",
        priority=10,  # Higher number means higher priority
        max_cost=0.0002,  # Max cost per second for the worker
        timeout_seconds=10,  # Task-specific timeout
    )


# 4. Human Approval
@main_bp.handler_for("awaiting_approval")
async def wait_for_approval(context, actions):
    """Demonstrates pausing a workflow to wait for an external signal."""
    logger.info(f"[{context.job_id}] AWAIT: Waiting for human approval...")
    actions.await_human_approval(
        integration="webhook",
        message="Please review the video before transcoding.",
        transitions={"approved": "dispatch_transcoding", "rejected": "human_rejected"},
    )


# 5. Dispatch a Single Task
@main_bp.handler_for("dispatch_transcoding")
async def dispatch_transcode(context, actions):
    """Delegates a task to a worker and defines transitions based on the worker's result."""
    logger.info(f"[{context.job_id}] DISPATCH: Sending 'transcode_video' task to a worker.")
    actions.dispatch_task(
        task_type="transcode_video",
        params={
            "input_path": context.initial_data.get("path"),
            "trigger": context.initial_data.get(
                "trigger"
            ),  # Pass the trigger to the worker
        },
        transitions={
            "success": "run_sub_blueprint",  # On success, move to the next step
            "failure": "transcoding_failed",  # On failure, move to a failure state
            "needs_review": "manual_review",  # Custom status from worker
        },
        # You can also specify resource requirements for the worker
        resource_requirements={"gpu_info": {"vram_gb": 4}},
    )


# 6. Run a Sub-Blueprint
@main_bp.handler_for("run_sub_blueprint")
async def run_child_blueprint(
    job_id: str,
    state_history: dict,
    actions: ActionFactory,
    # These are injected from the previous worker's result (in state_history)
    output_path: str,
    duration: int,
):
    """Demonstrates running a nested workflow and injecting worker results."""
    logger.info(
        f"[{job_id}] SUB-BLUEPRINT: Previous step produced '{output_path}' with duration {duration}s."
    )
    logger.info(f"[{job_id}] SUB-BLUEPRINT: Starting child blueprint for metadata.")
    actions.run_blueprint(
        blueprint_name="metadata_enrichment",
        initial_data={"video_id": state_history["video_id"]},
        transitions={"success": "fan_out_analysis", "failure": "enrichment_failed"},
    )


# 7. Fan-Out (Parallel Dispatch)
@main_bp.handler_for("fan_out_analysis")
async def fan_out_handler(context, actions):
    """Dispatches multiple tasks to be run in parallel."""
    files_to_analyze = ["audio_track.aac", "video_track.h264", "subtitles.srt"]
    logger.info(
        f"[{context.job_id}] FAN-OUT: Dispatching {len(files_to_analyze)} analysis tasks in parallel."
    )
    tasks = [
        {"type": "analyze_file", "params": {"file_name": f}} for f in files_to_analyze
    ]
    actions.dispatch_parallel(tasks=tasks, aggregate_into="aggregate_analysis_results")


# 8. Fan-In (Aggregator)
@main_bp.aggregator_for("aggregate_analysis_results")
async def aggregator_handler(context, actions):
    """
    This handler runs ONLY after all tasks from the 'fan_out_analysis' step
    have successfully completed.
    """
    logger.info(
        f"[{context.job_id}] FAN-IN: All analysis tasks completed. Aggregating results."
    )
    all_results = context.aggregation_results
    # all_results is a dict of {task_id: worker_result}
    summary = {
        task_id: result.get("data", {}).get("analysis")
        for task_id, result in all_results.items()
    }
    logger.info(f"[{context.job_id}] FAN-IN: Aggregated Summary: {summary}")
    context.state_history["analysis_summary"] = summary
    actions.transition_to("finished")


# --- Terminal States ---


@main_bp.handler_for("finished", is_end=True)
async def end_handler(context, actions):
    """The final state for a successful job."""
    logger.info(f"[{context.job_id}] FINISHED: Job completed successfully.")
    logger.info(f"Final state history: {context.state_history}")


@main_bp.handler_for("transcoding_failed", is_end=True)
async def transcoding_failed_handler(context, actions):
    """A terminal state for a specific failure mode."""
    logger.info(f"[{context.job_id}] FAILED: Video transcoding failed.")


@main_bp.handler_for("enrichment_failed", is_end=True)
async def enrichment_failed_handler(context, actions):
    """A terminal state for a specific failure mode."""
    logger.info(f"[{context.job_id}] FAILED: Metadata enrichment sub-blueprint failed.")


@main_bp.handler_for("manual_review", is_end=True)
async def manual_review_handler(context, actions):
    """A terminal state for jobs that need manual review."""
    logger.info(f"[{context.job_id}] FAILED: Job requires manual review.")


@main_bp.handler_for("human_rejected", is_end=True)
async def human_rejected_handler(context, actions):
    """A terminal state for jobs rejected by a human."""
    logger.info(f"[{context.job_id}] FAILED: Job was rejected by manual approval.")