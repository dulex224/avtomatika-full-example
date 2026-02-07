"""
Avtomatika Example Client

This script demonstrates how an external application interacts with the Orchestrator:
1. Authenticates using a Client Token.
2. Creates a new Job.
3. Polls for status updates and displays a real-time Progress Bar.
"""

from asyncio import run, sleep
from os import environ
from sys import stdout

from aiohttp import ClientSession, ClientConnectorError

# Configuration from environment variables with defaults
API_URL = environ.get("ORCHESTRATOR_URL", "http://localhost:8080")
CLIENT_TOKEN = environ.get("CLIENT_TOKEN", "user_token_vip")  # Must match example_clients.toml
BLUEPRINT = environ.get("BLUEPRINT_NAME", "full_showcase")


async def main():
    async with ClientSession() as session:
        # 1. Create Job
        print(f"🔌 Connecting to {API_URL}...")

        initial_data = {
            "path": "/s3/bucket/input.mp4",
            "quality": "high",
            "use_advanced_dispatch": True,
        }

        # In Docker Compose, the orchestrator can reach the webhook-receiver service by its name.
        webhook_url = environ.get("WEBHOOK_URL", "http://webhook-receiver:8000/webhook")

        headers = {"X-Client-Token": CLIENT_TOKEN}

        try:
            # Blueprint endpoint is /api/v1/jobs/full_showcase
            async with session.post(
                f"{API_URL}/api/v1/jobs/{BLUEPRINT}",
                json={"initial_data": initial_data, "webhook_url": webhook_url},
                headers=headers,
            ) as resp:
                if resp.status != 202:
                    print(f"❌ Failed to create job: {resp.status} {await resp.text()}")
                    return

                data = await resp.json()
                job_id = data["job_id"]
                print(f"✅ Job created! ID: {job_id}")
                print("-" * 50)

        except ClientConnectorError:
            print(f"❌ Could not connect to Orchestrator at {API_URL}.")
            print("Is the orchestrator running?")
            return

        # 2. Poll Status (Monitor Progress)
        while True:
            async with session.get(
                f"{API_URL}/api/v1/jobs/{job_id}", headers=headers
            ) as resp:
                if resp.status != 200:
                    print(f"\n❌ Error polling status: {resp.status}")
                    break

                state = await resp.json()
                status = state["status"]
                progress = state.get("progress", 0.0)
                msg = state.get("progress_message", "")

                # Draw Progress Bar
                bar_len = 30
                filled_len = int(bar_len * progress)
                bar = "█" * filled_len + "░" * (bar_len - filled_len)

                # Clear line and print info
                stdout.write(
                    f"\r[{bar}] {progress * 100:5.1f}% | {status.upper()} | {msg[:40]:<40}"
                )
                stdout.flush()

                if status in ["finished", "failed", "quarantined", "cancelled"]:
                    print(f"\n{'-' * 50}")
                    print(f"🏁 Final Status: {status}")
                    if status == "finished":
                        print(
                            f"🎉 Result: {state.get('state_history', {}).get('analysis_summary')}"
                        )
                    else:
                        print(f"⚠️ Error: {state.get('error_message')}")
                    break

            await sleep(0.5)


if __name__ == "__main__":
    try:
        run(main())
    except KeyboardInterrupt:
        print("\n👋 Client stopped.")