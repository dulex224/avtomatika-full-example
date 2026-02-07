from aiohttp.web import Application, Response, Request, run_app
from json import dumps
from logging import basicConfig, getLogger, INFO

# Configure logging
basicConfig(level=INFO, format="%(asctime)s [%(levelname)s] WEBHOOK: %(message)s")
logger = getLogger(__name__)


async def handle_webhook(request: Request):
    """
    Handles incoming webhook notifications from the Avtomatika Orchestrator.
    Expected payload format:
    {
        "event": "job_finished" | "job_failed" | "job_quarantined",
        "job_id": "uuid",
        "status": "finished" | "failed" | ...,
        "result": { ... },
        "error": "string or null"
    }
    """
    try:
        data = await request.json()
        event = data.get("event")
        job_id = data.get("job_id")
        status = data.get("status")

        logger.info("-" * 50)
        logger.info(f"🔔 Received notification for Job: {job_id}")
        logger.info(f"📅 Event: {event}")
        logger.info(f"📊 Status: {status}")

        if data.get("error"):
            logger.error(f"⚠️ Error details: {data['error']}")

        if data.get("result"):
            # Pretty print the result
            result_str = dumps(data["result"], indent=2)
            logger.info(f"📦 Result Data:\n{result_str}")

        logger.info("-" * 50)

        return Response(text="OK", status=200)
    except Exception as e:
        logger.error(f"Failed to process webhook: {e}")
        return Response(text=str(e), status=400)


app = Application()
app.router.add_post("/webhook", handle_webhook)

if __name__ == "__main__":
    logger.info("🚀 Webhook Receiver started on http://0.0.0.0:8000/webhook")
    run_app(app, host="0.0.0.0", port=8000)
