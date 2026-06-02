import structlog
from typing import List
from sqlmodel import Session, select
from src.models import Email
from src.database import engine

logger = structlog.get_logger(__name__)

class EmailRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_pending_emails(self, limit: int = 10) -> List[Email]:
        statement = select(Email).where(Email.status == "inbox").limit(limit).with_for_update(skip_locked=True)
        return list(self.session.exec(statement).all())

    def mark_as_processing(self, emails: List[Email]) -> None:
        for email in emails:
            email.status = "processing"
            self.session.add(email)
        self.session.commit()

class EmailIngestionService:
    def __init__(self):
        # By default we can create a new session if not injected, for simplicity
        # Real-world apps might inject the session per-request.
        pass

    def fetch_pending_emails(self, limit: int = 10) -> List[Email]:
        logger.info("Fetching pending emails", limit=limit)
        with Session(engine) as session:
            repo = EmailRepository(session)
            pending = repo.get_pending_emails(limit)
            if pending:
                repo.mark_as_processing(pending)
                logger.info("Emails marked as processing", count=len(pending))
            else:
                logger.info("No pending emails found")
            return pending
