import os
from sqlmodel import SQLModel, create_engine, Session

# Using localhost for running outside docker, but targeting the docker port.
# If running inside docker, this would be 'db'.
# For now, assuming local development against dockerized DB.
# Fallback to sqlite if postgres is not available or for simpler testing
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///learning.db")

engine = create_engine(DATABASE_URL)

def get_session():
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def migrate_schema():
    from sqlalchemy import text, inspect
    try:
        inspector = inspect(engine)
        # Check for knowledgenode (default lowercase) or knowledge_node (if snake case strategy used)
        table_name = "knowledgenode"
        if not inspector.has_table(table_name):
            return

        columns = [col['name'] for col in inspector.get_columns(table_name)]

        with engine.connect() as conn:
            if 'recall_half_life' not in columns:
                print(f"Adding recall_half_life column to {table_name} table")
                conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN recall_half_life FLOAT DEFAULT 7.0"))

            if 'last_recalled' not in columns:
                print(f"Adding last_recalled column to {table_name} table")
                conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN last_recalled TIMESTAMP"))

            if 'mastery_score' not in columns:
                print(f"Adding mastery_score column to {table_name} table")
                conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN mastery_score FLOAT DEFAULT 0.0"))

            conn.commit()
    except Exception as e:
        print(f"Migration failed: {e}")
