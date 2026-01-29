from pydantic import BaseModel
from typing import List, Dict, Any

class Node(BaseModel):
    id: str
    label: str
    type: str
    properties: Dict[str, Any] = {}

class Edge(BaseModel):
    source: str
    target: str
    relation: str
    properties: Dict[str, Any] = {}

class Graph(BaseModel):
    nodes: List[Node]
    edges: List[Edge]
