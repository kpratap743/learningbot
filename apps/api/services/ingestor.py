import os
import sys
import asyncio
from typing import List, Dict, Any, Optional
from sqlmodel import Session, select
from pydantic import BaseModel, Field
from playwright.async_api import async_playwright
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pinecone import Pinecone

# Imports assumed to be available from execution environment
try:
    from models import KnowledgeNode, Concept
    from apps.api.database import engine
except ImportError as e:
    # If we are running strictly as a script without proper setup, we might fail here.
    # But strictly speaking, the caller should set up sys.path.
    # However, to be helpful during dev/test if paths aren't perfect:
    try:
         sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
         sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../packages/shared')))
         from models import KnowledgeNode, Concept
         from apps.api.database import engine
    except ImportError:
         raise ImportError(f"Could not import required modules (models, apps.api.database). Ensure PYTHONPATH is set. Error: {e}")

class ExtractionResult(BaseModel):
    summary: str = Field(description="A concise summary of the blog post")
    design_primitives: List[str] = Field(description="List of extracted Design Primitives (e.g., 'Load Shedding', 'Idempotency Keys')")


class IngestorService:
    def __init__(self):
        pass

    async def fetch_posts(self, limit: int = 5) -> List[Dict[str, str]]:
        posts = []
        sources = {
            "Meta": "https://engineering.fb.com/",
            "Netflix": "https://netflixtechblog.com/",
            "Google Research": "https://research.google/blog/"
        }

        async with async_playwright() as p:
            # Launch without headless=False unless debugging. Docker needs headless=True usually.
            browser = await p.chromium.launch(headless=True)

            for source_name, url in sources.items():
                page = await browser.new_page()
                try:
                    print(f"Visiting {source_name} at {url}...")
                    await page.goto(url, timeout=30000)
                    await page.wait_for_load_state("domcontentloaded")

                    links = []

                    if "netflix" in url:
                        # Medium structure: often h3 is inside the link
                        links = await page.evaluate("""() => {
                            const nodes = Array.from(document.querySelectorAll('a h3'));
                            if (nodes.length > 0) return nodes.slice(0, 10).map(h3 => h3.closest('a').href);
                            # Fallback for some medium themes
                            return Array.from(document.querySelectorAll('.postArticle-content a')).slice(0, 10).map(a => a.href);
                        }""")
                    elif "engineering.fb.com" in url:
                        links = await page.evaluate("""() => {
                            return Array.from(document.querySelectorAll('.entry-title a')).slice(0, 10).map(a => a.href);
                        }""")
                    elif "research.google" in url:
                        links = await page.evaluate("""() => {
                            # Try to find blog post cards
                            let nodes = Array.from(document.querySelectorAll('a.blog-post-card'));
                            if (nodes.length > 0) return nodes.map(a => a.href);
                            # Fallback generic
                            return Array.from(document.querySelectorAll('h3 a')).slice(0, 10).map(a => a.href);
                        }""")

                    # Deduplicate, filter, and limit
                    unique_links = []
                    seen = set()
                    for link in links:
                        if link and link.startswith('http') and link not in seen:
                            seen.add(link)
                            unique_links.append(link)

                    target_links = unique_links[:limit]
                    print(f"Found {len(target_links)} links for {source_name}")

                    for link in target_links:
                        try:
                            print(f"Fetching {link}...")
                            await page.goto(link, timeout=30000)
                            await page.wait_for_load_state("domcontentloaded")

                            # Extract Title
                            title = await page.title()

                            # Extract Content
                            content = await page.evaluate("""() => {
                                const article = document.querySelector('article') || document.querySelector('main') || document.body;
                                return article.innerText;
                            }""")

                            if content:
                                posts.append({
                                    "source": source_name,
                                    "url": link,
                                    "title": title,
                                    "content": content[:15000] # reasonable limit
                                })
                        except Exception as e:
                            print(f"Error fetching post {link}: {e}")

                except Exception as e:
                    print(f"Error crawling {source_name}: {e}")
                finally:
                    await page.close()

            await browser.close()

        return posts

    async def extract_data(self, content: str) -> Dict[str, Any]:
        """
        Extracts design primitives and summary from content using LLM.
        """
        # Ensure API key is set in environment or handled by LangChain
        llm = ChatOpenAI(model="gpt-4o", temperature=0)

        parser = JsonOutputParser(pydantic_object=ExtractionResult)

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert software architect."),
            ("user", """
            Analyze the following engineering blog post.

            Content: {content}

            Tasks:
            1. Create a concise summary.
            2. Extract key 'Design Primitives' or 'Architectural Patterns' discussed.

            {format_instructions}
            """)
        ])

        chain = prompt | llm | parser

        try:
            result = await chain.ainvoke({
                "content": content,
                "format_instructions": parser.get_format_instructions()
            })
            return result
        except Exception as e:
            print(f"Error in LLM extraction: {e}")
            return {"summary": "", "design_primitives": []}

    async def find_related_concepts(self, summary: str) -> List[int]:
        try:
            # Requires OPENAI_API_KEY
            embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
            vector = await embeddings.aembed_query(summary)

            api_key = os.environ.get("PINECONE_API_KEY")
            if not api_key:
                print("PINECONE_API_KEY not set, skipping vector search.")
                return []

            pc = Pinecone(api_key=api_key)
            index_name = os.environ.get("PINECONE_INDEX_NAME", "concepts")

            # Check if index exists (optional, or just assume)
            # For this task, we assume the index exists.
            index = pc.Index(index_name)

            results = index.query(
                vector=vector,
                top_k=3,
                include_metadata=False
            )

            related_ids = []
            for match in results.matches:
                try:
                    # IDs might be "concept_123" or just "123"
                    clean_id = str(match.id).replace("concept_", "")
                    related_ids.append(int(clean_id))
                except ValueError:
                    pass

            return related_ids
        except Exception as e:
            print(f"Error in vector search: {e}")
            return []

    def save_drafts(self, drafts: List[KnowledgeNode]) -> int:
        """
        Saves a list of KnowledgeNode drafts to the database.
        Returns the count of saved items.
        """
        try:
            count = 0
            with Session(engine) as session:
                for draft in drafts:
                    # Check if already exists by source_url?
                    # For now, just add.
                    session.add(draft)
                    count += 1
                session.commit()
            return count
        except Exception as e:
            print(f"Error saving drafts: {e}")
            return 0
