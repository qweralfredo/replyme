from sqlmodel import SQLModel, Session
from src.database import engine
from src.models import KanbanColumn, Email

def migrate():
    # Create the table
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        default_columns = [
            KanbanColumn(status_key="inbox", name="Caixa de Entrada", position=1, is_system=True),
            KanbanColumn(status_key="processing", name="Processando", position=2, is_system=True),
            KanbanColumn(status_key="review", name="Revisão (IA)", position=3, is_system=True),
            KanbanColumn(status_key="to_send", name="Fila de Envio", position=4, is_system=True),
            KanbanColumn(status_key="done", name="Concluído / Enviado", position=5, is_system=True),
            KanbanColumn(status_key="archive", name="Arquivo Morto", position=99, is_system=True)
        ]
        
        for col in default_columns:
            existing = session.get(KanbanColumn, col.status_key)
            if existing:
                existing.name = col.name
                session.add(existing)
            else:
                session.add(col)
        session.commit()
        print("Migration complete!")

if __name__ == "__main__":
    migrate()
