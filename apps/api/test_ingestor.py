import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import os

# Set dummy env vars
os.environ["OPENAI_API_KEY"] = "sk-dummy"
os.environ["PINECONE_API_KEY"] = "dummy"

# Need to make sure we can import from apps.api and models
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../packages/shared')))

from apps.api.services.ingestor import IngestorService
from models import KnowledgeNode

@pytest.mark.asyncio
async def test_ingestor_flow():
    with patch("apps.api.services.ingestor.Session") as mock_session:

        service = IngestorService()

        # Mock the heavy lifting methods
        service.fetch_posts = AsyncMock(return_value=[
            {"source": "Meta", "url": "http://fb.com/1", "title": "T1", "content": "Content 1"}
        ])

        service.extract_data = AsyncMock(return_value={
            "summary": "Summary 1",
            "design_primitives": ["Primitive A", "Primitive B"]
        })

        service.find_related_concepts = AsyncMock(return_value=[101, 102])

        # Mock DB Session
        mock_db_session = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db_session

        # Execute the flow (simulating run_ingestor.py logic)
        posts = await service.fetch_posts()
        drafts = []
        for post in posts:
            ext = await service.extract_data(post['content'])
            ids = await service.find_related_concepts(ext['summary'])
            for p in ext['design_primitives']:
                drafts.append(KnowledgeNode(
                    label=p,
                    summary=ext['summary'],
                    source_url=post['url'],
                    extracted_primitives=[p],
                    linked_concept_ids=ids,
                    status="draft"
                ))

        # Call save
        count = service.save_drafts(drafts)

        # Verify
        assert len(drafts) == 2
        assert drafts[0].label == "Primitive A"
        assert drafts[1].label == "Primitive B"
        assert drafts[0].linked_concept_ids == [101, 102]

        # Verify DB calls
        assert mock_db_session.add.call_count == 2
        mock_db_session.commit.assert_called_once()
        assert count == 2
