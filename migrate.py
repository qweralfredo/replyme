from sqlmodel import SQLModel, Session
from src.database import engine
from src.models import KanbanColumn, Email

def migrate():
    # Create the table
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        default_columns = [
            KanbanColumn(status_key="inbox", name="Inbox", position=1, is_system=True),
            KanbanColumn(status_key="processing", name="Processing", position=2, is_system=True),
            KanbanColumn(status_key="review", name="Review Required", position=3, is_system=True),
            KanbanColumn(status_key="to_send", name="To Send (Queue)", position=4, is_system=True),
            KanbanColumn(status_key="done", name="Done / Sent", position=5, is_system=True)
        ]
        
        for col in default_columns:
            existing = session.get(KanbanColumn, col.status_key)
            if not existing:
                session.add(col)
        session.commit()
        print("Migration complete!")

if __name__ == "__main__":
    migrate()
