"""Avtomatika: Example Worker 3 (CPU, Reliable)

This script simulates another cheaper, CPU-only worker. It is reliable
and is used along with worker 2 to demonstrate the 'round_robin' dispatch strategy.

To run this worker:
1. Make sure the orchestrator from `full_example.py` is running.
2. Set the required environment variables:
   export WORKER_ID="cpu-worker-02"
   export WORKER_TOKEN="super-secret-cpu-worker-token-2"
   export ORCHESTRATOR_URL="http://localhost:8080"
3. Run this script in a separate terminal:
   `python workers/cpu_reliable.py`
"""

import asyncio
import logging
import random

from avtomatika_worker import Worker
from avtomatika_worker.config import WorkerConfig

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
    A reliable handler for the 'analyze_file' task.
    """
    logging.info(
        f"Task {task_id} (Job: {job_id}): starting 'analyze_file' with params {params}"
    )
    await asyncio.sleep(random.uniform(0.5, 1.5))

    analysis_data = {
        "file_name": params.get("file_name"),
        "size_kb": random.randint(100, 5000),
        "codec": "cpu_analyzed_by_worker_2",
    }
    logging.info(f"Task {task_id} finished successfully.")
    return {"status": "success", "data": {"analysis": analysis_data}}


if __name__ == "__main__":
    worker.run_with_health_check()
