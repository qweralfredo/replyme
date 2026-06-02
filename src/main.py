import time
import structlog
from datetime import datetime
from threading import Thread

from sqlmodel import Session
from src.database import engine
from src.services.ingestion import EmailIngestionService
from src.services.ai_classifier import AIClassifierService

logger = structlog.get_logger(__name__)

def worker_loop():
    logger.info("Starting replyme worker loop...")
    ingestion_service = EmailIngestionService()
    classifier_service = AIClassifierService()

    while True:
        try:
            with Session(engine) as session:
                # 1. Fetch pending emails directly in this session
                from sqlmodel import select
                from src.models import Email
                
                statement = select(Email).where(Email.status == "inbox").limit(5).with_for_update(skip_locked=True)
                pending_emails = list(session.exec(statement).all())
                
                if pending_emails:
                    for email in pending_emails:
                        email.status = "processing"
                        session.add(email)
                    session.commit()
                    logger.info("Emails marked as processing", count=len(pending_emails))
                    
                    for email in pending_emails:
                        # 2. Classify via LLM
                        logger.info("Classifying email", id=email.id)
                        try:
                            classification = classifier_service.classify_email(email.body)
                            
                            # 3. Update DB record
                            email.ai_category = classification.category
                            email.ai_sentiment = classification.sentiment
                            email.ai_urgency = str(classification.urgency)
                            email.ai_summary = classification.summary
                            
                            # Use LLM-generated response draft
                            email.ai_response = classification.response
                            
                            email.status = "review"
                            email.processed_at = datetime.utcnow()
                            session.add(email)
                        except Exception as e:
                            logger.error("Error classifying email", id=email.id, error=str(e))
                            email.status = "error"
                            session.add(email)
                    
                    session.commit()
                    logger.info("Batch processed successfully", count=len(pending_emails))
        except Exception as e:
            logger.error("Error in worker loop", error=str(e))
        
        # Sleep before next poll
        time.sleep(5)

if __name__ == "__main__":
    # Run main worker loop
    worker_loop()
