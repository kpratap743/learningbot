from typing import List, Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON

class Concept(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    topic: str
    prerequisites_ids: List[int] = Field(default_factory=list, sa_column=Column(JSON))
    mastery_score: float = Field(default=0.0)
    recall_half_life: float = Field(default=0.0)

class Resource(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    source_url: str
    summary: str
    linked_concept_ids: List[int] = Field(default_factory=list, sa_column=Column(JSON))

class PrincipalSkill(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    category: str
    simulation_prompt: str
    last_practiced: Optional[datetime] = Field(default=None)

class KnowledgeNode(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    label: str
    summary: str
    source_url: str
    extracted_primitives: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    linked_concept_ids: List[int] = Field(default_factory=list, sa_column=Column(JSON))
    status: str = Field(default="draft")
    recall_half_life: float = Field(default=7.0)
    last_recalled: Optional[datetime] = Field(default_factory=datetime.utcnow)
