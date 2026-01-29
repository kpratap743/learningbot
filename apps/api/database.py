from sqlmodel import SQLModel, create_engine, Session

# Using localhost for running outside docker, but targeting the docker port.
# If running inside docker, this would be 'db'.
# For now, assuming local development against dockerized DB.
DATABASE_URL = "postgresql://user:password@localhost:5432/learning"

engine = create_engine(DATABASE_URL)

def get_session():
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
