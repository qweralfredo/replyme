from sqlmodel import SQLModel, Session, text
from src.database import engine
from src.models import KanbanColumn, Email

def migrate():
    # Create the table
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        # Tenta adicionar a coluna recipient caso ainda não exista
        try:
            session.exec(text("ALTER TABLE emails ADD COLUMN recipient VARCHAR(255) DEFAULT 'suporte@replyme.local'"))
            session.commit()
            print("Coluna recipient adicionada com sucesso.")
        except Exception as e:
            session.rollback()
            print("Coluna recipient já existe ou erro ignorado:", e)

        try:
            session.exec(text("ALTER TABLE kanban_columns ADD COLUMN mcp_servers TEXT DEFAULT '[]'"))
            session.commit()
            print("Coluna mcp_servers adicionada com sucesso.")
        except Exception as e:
            session.rollback()
            print("Coluna mcp_servers já existe ou erro ignorado:", e)

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
