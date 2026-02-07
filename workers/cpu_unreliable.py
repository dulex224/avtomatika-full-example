"""Avtomatika: Example Worker 2 (CPU, Unreliable)

This script simulates a cheaper, CPU-only worker that has a high chance of failure.
It is used to demonstrate the 'best_value' (reputation) dispatch strategy.

To run this worker:
1. Make sure the orchestrator from `full_example.py` is running.
2. Set the required environment variables:
   export WORKER_ID="cpu-worker-01"
   export WORKER_TOKEN="super-secret-cpu-worker-token"
   export ORCHESTRATOR_URL="http://localhost:8080"
3. Run this script in a separate terminal:
   `python workers/cpu_unreliable.py`
"""

import asyncio
import logging
import random

from avtomatika_worker import Worker
from avtomatika_worker.config import WorkerConfig
from avtomatika_worker.types import PERMANENT_ERROR

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logging.getLogger("asyncio").setLevel(logging.WARNING)

# Configure the worker
config = WorkerConfig()
config.COST_PER_SECOND = 0.0001
config.MAX_CONCURRENT_TASKS = 4
config.RESOURCES["cpu_cores"] = 4
config.RESOURCES["gpu_info"] = None  # Explicitly a non-GPU worker

# Create a worker instance
worker = Worker(
    worker_type="cpu_worker",
    config=config,
)


@worker.task("analyze_file")
async def analyze_file(params: dict, task_id: str, job_id: str, **kwargs):
    """
    A handler that is intentionally unreliable to test reputation scoring.
    """
    logging.info(
        f"Task {task_id} (Job: {job_id}): starting 'analyze_file' with params {params}"
    )
    await asyncio.sleep(random.uniform(0.5, 1.5))

    # This worker is unreliable and has a 50% chance of failing any task
    if random.random() < 0.5:
        logging.error(f"  -> SIMULATING UNRELIABLE FAILURE for task {task_id}")
        return {
            "status": "failure",
            "error": {
                "code": PERMANENT_ERROR,
                "message": "Simulated unreliable hardware",
            },
        }
    else:
        analysis_data = {
            "file_name": params.get("file_name"),
            "size_kb": random.randint(100, 5000),
            "codec": "cpu_analyzed",
        }
        logging.info(f"Task {task_id} finished successfully.")
        return {"status": "success", "data": {"analysis": analysis_data}}


if __name__ == "__main__":
    worker.run_with_health_check()
