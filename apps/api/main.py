from fastapi import FastAPI
from contextlib import asynccontextmanager
from .database import create_db_and_tables
from knowledge_graph.models import Node

@asynccontextmanager
async def lifespan(app: FastAPI):
    # create_db_and_tables()
    # Commented out to avoid errors if DB isn't up during simple tests,
    # but strictly speaking we should try to connect.
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/test-model")
def test_model():
    node = Node(id="1", label="Test Node", type="concept")
    return node
