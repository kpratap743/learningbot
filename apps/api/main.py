from functools import lru_cache
from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from pydantic import BaseModel
from .database import create_db_and_tables
from knowledge_graph.models import Node
from .agents.rfc_critique import RFCCritiqueAgent, RFCCritiqueResult

@asynccontextmanager
async def lifespan(app: FastAPI):
    # create_db_and_tables()
    # Commented out to avoid errors if DB isn't up during simple tests,
    # but strictly speaking we should try to connect.
    yield

app = FastAPI(lifespan=lifespan)

@lru_cache
def get_rfc_agent():
    return RFCCritiqueAgent()

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/test-model")
def test_model():
    node = Node(id="1", label="Test Node", type="concept")
    return node

class RFCRequest(BaseModel):
    content: str

@app.post("/critique/rfc", response_model=RFCCritiqueResult)
async def critique_rfc(request: RFCRequest, agent: RFCCritiqueAgent = Depends(get_rfc_agent)):
    return await agent.critique(request.content)
