import asyncio
import os
import json
from typing import List, Optional, Dict, Any

from playwright.async_api import async_playwright
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from sqlmodel import Session, select

try:
    from models import Concept
except ImportError:
    # If imports fail (e.g. running as script without installed package), try relative or skip
    pass

# Handle imports depending on execution context
try:
    from apps.api.database import engine
except ImportError:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
    try:
        from apps.api.database import engine
        from models import Concept
    except ImportError:
        pass

class SpacedRepetitionCard(BaseModel):
    front: str = Field(description="The question or prompt for the card")
    back: str = Field(description="The answer or explanation for the card")
    tags: List[str] = Field(description="Tags associated with the card")

class BlogAnalysisResult(BaseModel):
    summary: str = Field(description="Summary of the blog post")
    decision_primitives: List[str] = Field(description="List of extracted decision primitives")
    concept_mappings: Dict[str, Optional[int]] = Field(description="Mapping of primitives to existing Concept IDs")
    cards: List[SpacedRepetitionCard] = Field(description="3 Spaced Repetition cards")

class EngineeringBlogAggregator:
    def __init__(self):
        self.blogs = {
            "Meta": "https://engineering.fb.com/",
            "Netflix": "https://netflixtechblog.com/",
            "Google": "https://developers.googleblog.com/"
        }
        # Assuming OPENAI_API_KEY is in environment
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)

    async def crawl_blogs(self) -> Dict[str, str]:
        """
        Crawls the blogs and returns a dictionary of {BlogName: PostContent}.
        """
        results = {}
        async with async_playwright() as p:
            browser = await p.chromium.launch()

            for name, url in self.blogs.items():
                try:
                    page = await browser.new_page()
                    print(f"Visiting {name} at {url}...")
                    # Go to blog
                    await page.goto(url, timeout=30000)

                    # Heuristic to find the first article
                    # We try a few common selectors for blog post links:
                    # h2/h3 inside articles, or specific classes.
                    article_selector = "h2 a, h3 a, article h2 a, article h3 a, .post-title a"

                    if "netflixtechblog" in url:
                        # Medium often uses different structures, but h3 usually contains title on feed
                        article_selector = "h3, a h3"

                    found_article = False
                    try:
                        # Wait for potential article links
                        await page.wait_for_selector(article_selector, timeout=5000)
                        links = await page.query_selector_all(article_selector)

                        if links:
                            target = links[0]
                            print(f"Clicking article link on {name}...")

                            # Handle navigation
                            # Sometimes clicking h3 on Medium works if it's inside an anchor, or we need to click parent.
                            # We'll try to click the element.
                            async with page.expect_navigation(timeout=15000):
                                await target.click()

                            await page.wait_for_load_state("domcontentloaded")
                            found_article = True
                    except Exception as nav_err:
                        print(f"Navigation to article failed for {name}: {nav_err}. Falling back to page content.")

                    # Extract content (either from article or landing page if nav failed)
                    # Ideally we'd extract from <article> tag if present
                    content = await page.evaluate("""() => {
                        const article = document.querySelector('article') || document.querySelector('main') || document.body;
                        return article.innerText;
                    }""")

                    # Truncate to avoid context limit issues in this demo
                    # If we successfully found an article, we might want more content.
                    limit = 10000 if found_article else 5000
                    results[name] = content[:limit] if content else ""

                    await page.close()
                except Exception as e:
                    print(f"Error crawling {name}: {e}")
                    results[name] = f"Error: {str(e)}"

            await browser.close()
        return results

    def _get_existing_concepts(self) -> Dict[int, str]:
        try:
            with Session(engine) as session:
                concepts = session.exec(select(Concept)).all()
                return {c.id: c.topic for c in concepts if c.id is not None}
        except Exception as e:
            # Fallback if DB is not accessible
            print(f"Warning: Could not fetch concepts from DB: {e}")
            return {}

    async def process_post(self, content: str) -> BlogAnalysisResult:
        existing_concepts = self._get_existing_concepts()

        parser = JsonOutputParser(pydantic_object=BlogAnalysisResult)

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert software engineering assistant."),
            ("user", """
            Analyze the following blog post content.

            Content: {content}

            Existing Knowledge Graph Concepts: {concepts}

            Tasks:
            1. Summarize the post.
            2. Extract 'Decision Primitives' (e.g., 'Choosing LSM trees over B-Trees').
            3. Map these primitives to the closest existing Concept IDs provided. If no close match exists, map to null.
            4. Generate 3 Spaced Repetition cards.

            {format_instructions}
            """)
        ])

        chain = prompt | self.llm | parser

        try:
            result = await chain.ainvoke({
                "content": content,
                "concepts": str(existing_concepts),
                "format_instructions": parser.get_format_instructions()
            })
            return BlogAnalysisResult(**result)
        except Exception as e:
            print(f"Error in LLM processing: {e}")
            return BlogAnalysisResult(
                summary="Error processing content",
                decision_primitives=[],
                concept_mappings={},
                cards=[]
            )

    async def run(self):
        print("Starting crawl...")
        crawled_data = await self.crawl_blogs()
        final_results = {}
        for blog, content in crawled_data.items():
            if content and not content.startswith("Error"):
                print(f"Processing content for {blog}...")
                analysis = await self.process_post(content)
                final_results[blog] = analysis.dict()
        return final_results

if __name__ == "__main__":
    agg = EngineeringBlogAggregator()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    results = loop.run_until_complete(agg.run())
    print(json.dumps(results, indent=2))
