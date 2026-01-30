import os
import httpx
import logging

logger = logging.getLogger(__name__)

async def send_slack_notification(message: str):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        logger.warning("SLACK_WEBHOOK_URL not set. Skipping notification.")
        # For development/debugging, let's print the message to stdout so we can see it in logs
        print(f"DEBUG: Notification Message (not sent): {message}")
        return

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(webhook_url, json={"text": message})
            response.raise_for_status()
            logger.info("Notification sent successfully.")
        except httpx.HTTPError as e:
            logger.error(f"Failed to send notification: {e}")
