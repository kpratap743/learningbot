import logging
import random
from datetime import datetime
from typing import List, Dict

from sqlmodel import Session, select, text
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Assumes packages/shared is installed in the environment
from models import KnowledgeNode

from .database import engine
from .agents.challenge_agent import generate_system_design_challenge
from .services.notification import send_slack_notification

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def run_daily_challenge():
    logger.info("Starting daily challenge generation...")
    try:
        with Session(engine) as session:
            # Use SQL filtering for efficiency
            # We assume recall_half_life is in days.
            query = text("""
                SELECT * FROM knowledgenode
                WHERE last_recalled IS NULL
                OR last_recalled < (NOW() - (recall_half_life * INTERVAL '1 day'))
            """)

            stmt = select(KnowledgeNode).from_statement(query)
            expired_nodes = session.exec(stmt).all()

            logger.info(f"Found {len(expired_nodes)} expired nodes.")

            if not expired_nodes:
                return

            # Collect primitives
            primitive_map: Dict[str, List[KnowledgeNode]] = {}

            for node in expired_nodes:
                for primitive in node.extracted_primitives:
                    if primitive not in primitive_map:
                        primitive_map[primitive] = []
                    primitive_map[primitive].append(node)

            unique_primitives = list(primitive_map.keys())

            if not unique_primitives:
                logger.info("No primitives found in expired nodes.")
                return

            # Select 3 primitives
            selected_primitives = []
            if len(unique_primitives) <= 3:
                selected_primitives = unique_primitives
            else:
                selected_primitives = random.sample(unique_primitives, 3)

            logger.info(f"Selected primitives: {selected_primitives}")

            # Generate Challenge
            challenge_text = await generate_system_design_challenge(selected_primitives)

            # Send Notification
            await send_slack_notification(challenge_text)

            # Update last_recalled for involved nodes
            involved_nodes = set()
            for p in selected_primitives:
                for node in primitive_map[p]:
                    involved_nodes.add(node)

            now = datetime.utcnow()
            for node in involved_nodes:
                node.last_recalled = now
                session.add(node)

            session.commit()
            logger.info(f"Updated last_recalled for {len(involved_nodes)} nodes.")

    except Exception as e:
        logger.error(f"Error in run_daily_challenge: {e}", exc_info=True)

def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(run_daily_challenge, 'cron', hour=8, minute=0)
        scheduler.start()
        logger.info("Scheduler started.")
