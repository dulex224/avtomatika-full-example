from os import environ
from os.path import abspath, dirname, join
from avtomatika.config import Config

# Build absolute paths to config files relative to the project root
# Assuming this file is in the root or imported such that we can resolve paths correctly.
# If config.py is in root:
script_dir = dirname(abspath(__file__))

config = Config()
# Allow overriding configuration via environment variables, with sensible defaults
config.API_PORT = int(environ.get("API_PORT", 8080))
config.CLIENTS_CONFIG_PATH = environ.get(
    "CLIENTS_CONFIG_PATH", join(script_dir, "example_clients.toml")
)
config.GLOBAL_WORKER_TOKEN = environ.get(
    "GLOBAL_WORKER_TOKEN", "super-secret-worker-token"
)
config.WORKERS_CONFIG_PATH = environ.get(
    "WORKERS_CONFIG_PATH", join(script_dir, "example_workers.toml")
)
config.HISTORY_DATABASE_URI = environ.get(
    "HISTORY_DATABASE_URI", "sqlite:avtomatika_history.db"
)
config.SCHEDULES_CONFIG_PATH = environ.get(
    "SCHEDULES_CONFIG_PATH", join(script_dir, "schedules.toml")
)
