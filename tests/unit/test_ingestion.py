import pytest
from src.services.ingestion import EmailIngestionService

def test_fetch_pending_emails_empty_db():
    service = EmailIngestionService()
    # In a real scenario we might pass a mock DB session, but for now we test the signature
    pending = service.fetch_pending_emails()
    assert pending == []
