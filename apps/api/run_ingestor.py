import asyncio
import os
import sys

# Ensure path is set up to import from root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Handle imports
try:
    from apps.api.services.ingestor import IngestorService
    from models import KnowledgeNode
except ImportError:
    # Try adding packages/shared
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../packages/shared')))
    from apps.api.services.ingestor import IngestorService
    from models import KnowledgeNode

async def main():
    service = IngestorService()

    print("Fetching posts...")
    posts = await service.fetch_posts(limit=5)
    print(f"Fetched {len(posts)} posts.")

    drafts = []

    for post in posts:
        print(f"Processing: {post['title']}")

        # Extract
        extraction = await service.extract_data(post['content'])
        summary = extraction.get("summary", "")
        primitives = extraction.get("design_primitives", [])

        if not primitives:
            print("No primitives found, skipping.")
            continue

        print(f"  Found primitives: {primitives}")

        # Link
        related_ids = await service.find_related_concepts(summary)
        print(f"  Linked to concepts: {related_ids}")

        # Create Draft KnowledgeNode per Primitive
        for primitive in primitives:
            node = KnowledgeNode(
                label=primitive,
                summary=summary, # Context
                source_url=post['url'],
                extracted_primitives=[primitive],
                linked_concept_ids=related_ids,
                status="draft"
            )
            drafts.append(node)

    print(f"Saving {len(drafts)} drafts...")
    count = service.save_drafts(drafts)
    print(f"Saved {count} drafts.")

if __name__ == "__main__":
    asyncio.run(main())
