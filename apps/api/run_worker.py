import asyncio
import logging
import os
import sys

# Ensure repo root is in path so we can import apps.api...
sys.path.append(os.getcwd())

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from apps.api.worker import start_scheduler
except ImportError as e:
    logger.error(f"Failed to import worker: {e}. Make sure you run this script from the repository root.")
    sys.exit(1)

def main():
    logger.info("Starting Background Worker Process...")
    start_scheduler()

    # Keep the process alive
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Stopping worker...")

if __name__ == "__main__":
    main()
