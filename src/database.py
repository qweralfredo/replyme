import os
from sqlmodel import create_engine, Session, SQLModel
import src.models  # Ensure models are loaded

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:password@localhost:5433/replayme_db")

engine = create_engine(DATABASE_URL, echo=False)
SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
