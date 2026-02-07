import asyncio
import os
import sys
import pytest
import aiohttp

# Add parent dir to path to import full_example if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration for test
API_URL = os.environ.get("API_URL", "http://localhost:8080")
CLIENT_TOKEN = "user_token_vip"


@pytest.mark.asyncio
async def test_full_flow_execution():
    """
    End-to-End test:
    1. Checks if Orchestrator is healthy.
    2. Creates a job.
    3. Polls until completion.
    4. Asserts success.
    """
    async with aiohttp.ClientSession() as session:
        # 1. Health Check
        async with session.get(f"{API_URL}/_public/status") as resp:
            if resp.status != 200:
                pytest.skip(
                    "Orchestrator is not running. Start it with 'docker-compose up' to run this test."
                )

        # 2. Create Job
        headers = {"X-Client-Token": CLIENT_TOKEN}
        payload = {
            "initial_data": {
                "path": "test_video.mp4",
                "quality": "high",
                "use_advanced_dispatch": True,
            }
        }

        async with session.post(
            f"{API_URL}/api/v1/jobs/full_showcase", json=payload, headers=headers
        ) as resp:
            assert resp.status == 202, f"Failed to create job: {await resp.text()}"
            data = await resp.json()
            job_id = data["job_id"]
            print(f"Test Job ID: {job_id}")

        # 3. Poll for result (max 30 seconds)
        status = "unknown"
        state = {}
        for i in range(60):
            await asyncio.sleep(0.5)
            async with session.get(
                f"{API_URL}/api/v1/jobs/{job_id}", headers=headers
            ) as resp:
                assert resp.status == 200
                state = await resp.json()
                status = state["status"]
                current_state = state.get("current_state")
                if i % 10 == 0:
                    print(
                        f"Polling Job {job_id}: status={status}, state={current_state}"
                    )

                if status in ["finished", "failed", "quarantined", "cancelled"]:
                    print(f"Job {job_id} reached terminal status: {status}")
                    break
        else:
            print(f"Final state before timeout: {state}")
            pytest.fail(
                f"Job timed out (did not finish in 30s). Last status: {status}, state: {state.get('current_state')}"
            )

        # 4. Assertions
        assert status == "finished", (
            f"Job failed with error: {state.get('error_message')}"
        )
        assert "analysis_summary" in state.get("state_history", {}), (
            f"Missing summary in history: {state.get('state_history')}"
        )
        print("Test passed successfully!")
