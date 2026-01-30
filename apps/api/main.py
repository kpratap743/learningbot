from functools import lru_cache
from typing import List
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from sqlmodel import Session, select
if __package__:
    from .database import create_db_and_tables, migrate_schema, get_session
    from .agents.rfc_critique import RFCCritiqueAgent, RFCCritiqueResult
else:
    from database import create_db_and_tables, migrate_schema, get_session
    from agents.rfc_critique import RFCCritiqueAgent, RFCCritiqueResult
from knowledge_graph.models import Node as GraphNode
from models import KnowledgeNode  # Importing from the shared models module

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        create_db_and_tables()
    except Exception as e:
        print(f"Startup warning: Could not create tables: {e}")

    try:
        # Attempt to migrate schema
        # We wrap in try/except so that if DB is not available (e.g. build time), app still starts
        migrate_schema()
    except Exception as e:
        print(f"Startup warning: Could not migrate DB: {e}")
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@lru_cache
def get_rfc_agent():
    return RFCCritiqueAgent()

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/test-model")
def test_model():
    node = GraphNode(id="1", label="Test Node", type="concept")
    return node

class RFCRequest(BaseModel):
    content: str

@app.post("/critique/rfc", response_model=RFCCritiqueResult)
async def critique_rfc(request: RFCRequest, agent: RFCCritiqueAgent = Depends(get_rfc_agent)):
    return await agent.critique(request.content)

# Knowledge Node Endpoints

@app.post("/nodes", response_model=KnowledgeNode)
def create_node(node: KnowledgeNode, session: Session = Depends(get_session)):
    session.add(node)
    session.commit()
    session.refresh(node)
    return node

@app.get("/nodes", response_model=List[KnowledgeNode])
def read_nodes(session: Session = Depends(get_session)):
    nodes = session.exec(select(KnowledgeNode)).all()
    return nodes

@app.post("/nodes/{node_id}/quiz")
def simulate_quiz(node_id: int, session: Session = Depends(get_session)):
    node = session.get(KnowledgeNode, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    # Simulate quiz: update mastery score to 100% (1.0) or increment
    # For the test, setting it to a specific value we can verify is best.
    node.mastery_score = 100.0
    session.add(node)
    session.commit()
    session.refresh(node)
    return {"message": "Quiz simulated", "mastery_score": node.mastery_score}
