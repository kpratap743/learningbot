import sys
import os
import asyncio
import json
from unittest.mock import MagicMock, patch

# Ensure imports work
sys.path.append(os.getcwd())

# Mock models before importing aggregator if necessary, but we handled imports in aggregator.py
# However, we want to ensure we don't crash on import.

from apps.api.agents.aggregator import EngineeringBlogAggregator, BlogAnalysisResult

async def async_return(val):
    return val

async def test_aggregator():
    print("Testing EngineeringBlogAggregator...")

    # Mock ChatOpenAI so we don't need an API key
    with patch('apps.api.agents.aggregator.ChatOpenAI') as MockLLM:
        agg = EngineeringBlogAggregator()

        # Mock crawl_blogs
        agg.crawl_blogs = MagicMock(return_value=async_return({
            "TestBlog": "Sample content from test blog."
        }))

        # Mock process_post to avoid LLM chain issues
        mock_result = BlogAnalysisResult(
            summary="Test Summary",
            decision_primitives=["Primitive 1"],
            concept_mappings={"Primitive 1": 1},
            cards=[
                {"front": "Q1", "back": "A1", "tags": ["tag1"]}
            ]
        )
        agg.process_post = MagicMock(return_value=async_return(mock_result))

        print("Running aggregator.run()...")
        results = await agg.run()

        print("Verifying results...")
        assert "TestBlog" in results
        data = results["TestBlog"]
        assert data["summary"] == "Test Summary"
        assert len(data["decision_primitives"]) == 1
        assert data["cards"][0]["front"] == "Q1"

        print("SUCCESS: Aggregator run logic verified.")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(test_aggregator())
