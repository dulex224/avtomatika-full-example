"""Avtomatika: Example Worker (using the SDK)

This script shows how to create a worker using the avtomatika-worker SDK.
It connects to the orchestrator, polls for tasks, and executes them.

To run this worker:
1. Make sure the orchestrator from `full_example.py` is running.
2. Set the required environment variables:
   export WORKER_ID="gpu-worker-01"
   export WORKER_TOKEN="super-secret-gpu-worker-token"
   export ORCHESTRATOR_URL="http://localhost:8080"
3. Run this script in a separate terminal:
   `python workers/gpu.py`
"""

from asyncio import sleep

from logging import basicConfig, getLogger, INFO, WARNING

from random import random, uniform

from os import environ


from avtomatika_worker import Worker, TaskFiles

from avtomatika_worker.config import WorkerConfig

from avtomatika_worker.types import (
    PERMANENT_ERROR,
    RESOURCE_EXHAUSTED_ERROR,
    SECURITY_ERROR,
    TRANSIENT_ERROR,
)


# Configure basic logging to see worker messages

basicConfig(level=INFO)

getLogger("asyncio").setLevel(WARNING)

logger = getLogger(__name__)


# 1. Create a config object. It automatically reads from environment variables.

#    We can override or supplement it programmatically.

config = WorkerConfig()


# --- Programmatic Configuration Overrides ---

# In a real scenario, these would likely be set by environment variables,

# but we set them here for example clarity.

config.COST_PER_SKILL = {"transcode_video": 0.0005, "analyze_file": 0.0001}

config.RESOURCES["gpu_info"] = {"model": "NVIDIA T4", "vram_gb": 16}

config.RESOURCES["cpu_cores"] = 8

config.INSTALLED_SOFTWARE = {"ffmpeg": "5.1"}

config.INSTALLED_MODELS = [{"name": "stable-diffusion-1.5", "version": "1.0"}]

config.MAX_CONCURRENT_TASKS = 2

config.ENABLE_WEBSOCKETS = True


# 2. Create a worker instance

# The worker_type and config are passed during initialization.

worker = Worker(
    worker_type="gpu_worker",
    config=config,
)


# 3. Define task handlers using the @worker.task decorator


@worker.task("transcode_video")
async def transcode_video(
    params: dict, task_id: str, job_id: str, send_progress, **kwargs
):
    """

    A handler that simulates video transcoding. It can fail in different ways

    based on the 'trigger' parameter and sends progress updates.

    """

    logger.info(
        f"Task {task_id} (Job: {job_id}): starting 'transcode_video' with params {params}"
    )

    # Simulate work with progress updates

    for i in range(1, 6):
        # The SDK automatically handles cancellation. If a cancel command is received,

        # this `asyncio.sleep` will raise a `CancelledError`.

        await sleep(uniform(0.5, 1))

        progress = i / 5

        logger.info(f"  -> Task {task_id} progress: {progress:.0%}")

        # Use the injected `send_progress` function

        await send_progress(task_id, job_id, progress, f"Step {i} of 5 complete.")

    # --- Task-specific logic for returning results ---

    trigger = params.get("trigger")

    if trigger == "transient":
        logger.warning(f"  -> SIMULATING TRANSIENT ERROR for task {task_id}")

        return {
            "status": "failure",
            "error": {"code": TRANSIENT_ERROR, "message": "Simulated network glitch"},
        }

    elif trigger == "security":
        logger.warning(f"  -> SIMULATING SECURITY ERROR for task {task_id}")

        return {
            "status": "failure",
            "error": {
                "code": SECURITY_ERROR,
                "message": "Simulated security violation",
            },
        }

    elif trigger == "resource":
        logger.warning(f"  -> SIMULATING RESOURCE EXHAUSTED for task {task_id}")

        return {
            "status": "failure",
            "error": {"code": RESOURCE_EXHAUSTED_ERROR, "message": "Simulated OOM"},
        }

    # Support deterministic mode for tests

    if environ.get("DETERMINISTIC_WORKER") == "true":
        logger.info(f"Task {task_id} completed successfully (deterministic).")

        return {
            "status": "success",
            "data": {"output_path": "/path/to/transcoded.mp4", "duration": 120},
        }

    rand = random()

    if rand < 0.1:
        logger.error(f"  -> SIMULATING PERMANENT ERROR for task {task_id}")

        return {
            "status": "failure",
            "error": {"code": PERMANENT_ERROR, "message": "Random transcoding error"},
        }

    elif rand < 0.2:
        logger.warning(f"  -> SIMULATING 'needs_review' status for task {task_id}")

        return {
            "status": "needs_review",
            "data": {"reason": "Low quality source detected"},
        }

    else:
        logger.info(f"Task {task_id} completed successfully.")

        return {
            "status": "success",
            "data": {"output_path": "/path/to/transcoded.mp4", "duration": 120},
        }


@worker.task("analyze_file")
async def analyze_file(params: dict, task_id: str, job_id: str, **kwargs):
    """A simple handler for analyzing a file, supporting S3 offloading."""

    logger.info(
        f"Task {task_id} (Job: {job_id}): starting 'analyze_file' with params {params}"
    )

    # Check if we got an S3 path (SDK automatically downloads it if configured)

    input_file = params.get("file_name") or params.get("s3_path")

    await sleep(1)

    analysis_data = {
        "file_name": input_file,
        "size_kb": int(random() * 4900 + 100),
        "codec": "aac",  # Simplified for example
        "location": "local" if not str(input_file).startswith("s3://") else "s3",
    }

    logger.info(f"Task {task_id} finished with analysis: {analysis_data}")

    return {"status": "success", "data": {"analysis": analysis_data}}


@worker.task("process_blobs")
async def process_blobs(params: dict, files: "TaskFiles", **kwargs):
    """Demonstrates using TaskFiles helper for manual S3/Local file management."""

    logger.info(f"Task {kwargs['task_id']}: processing blobs...")

    # Create a local file

    await files.write("report.txt", "This is a simulated analysis report.")

    report_path = await files.path_to("report.txt")

    # Returning this path will trigger automatic S3 upload if S3 is configured

    return {"status": "success", "data": {"report_file": report_path}}


# 4. Run the worker

if __name__ == "__main__":
    # This is a blocking call that starts the worker's main loop,

    # including registration, heartbeats, and task polling.

    # It also includes a /health endpoint.

    worker.run_with_health_check()
