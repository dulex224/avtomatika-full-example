"""
Avtomatika: Full Feature Demonstration

For instructions on how to run this example, please see the README.md file
in the `avtomatika_full_example` directory.
"""

import logging
from asyncio import CancelledError, Event, run
from os import environ, remove
from os.path import exists

from redis.asyncio import Redis
from avtomatika import OrchestratorEngine
from avtomatika.storage.memory import MemoryStorage
from avtomatika.storage.redis import RedisStorage

# Import extracted configuration and blueprints
from config import config
from blueprints import main_bp, sub_blueprint, maintenance_bp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("orchestrator")


# --- Engine Setup and Run ---
async def main():
    """Initializes and runs the orchestrator engine."""
    # Clean up old SQLite DB file if it's being used and exists
    if config.HISTORY_DATABASE_URI.startswith("sqlite:") and exists(
        "avtomatika_history.db"
    ):
        remove("avtomatika_history.db")
        logger.info("Removed old history database.")

    # --- Storage Setup ---
    redis_host = environ.get("REDIS_HOST")
    if redis_host:
        logger.info(f"Connecting to Redis at {redis_host}...")
        # NOTE: RedisStorage handles its own encoding/decoding via msgpack,
        # so we must NOT use decode_responses=True here.
        redis_client = Redis(host=redis_host, decode_responses=False)
        storage = RedisStorage(redis_client)
    else:
        logger.info("Using MemoryStorage (REDIS_HOST not set).")
        storage = MemoryStorage()

    engine = OrchestratorEngine(storage, config)

    # Register all the blueprints
    engine.register_blueprint(main_bp)
    engine.register_blueprint(sub_blueprint)
    engine.register_blueprint(maintenance_bp)

    logger.info(f"Starting Avtomatika Orchestrator on port {config.API_PORT}...")
    await engine.start()

    logger.info("--- Orchestrator is READY ---")
    logger.info(
        f"Public API: http://localhost:{config.API_PORT}/api/v1/jobs/full_showcase"
    )
    logger.info(f"Health Check: http://localhost:{config.API_PORT}/_public/status")
    logger.info(f"Metrics: http://localhost:{config.API_PORT}/_public/metrics")

    try:
        # Keep the server running until interrupted
        await Event().wait()
    except (KeyboardInterrupt, CancelledError):
        pass
    finally:
        logger.info("Shutting down orchestrator...")
        await engine.stop()


if __name__ == "__main__":
    try:
        run(main())
    except KeyboardInterrupt:
        pass