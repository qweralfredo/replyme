import time
import structlog
from datetime import datetime
from threading import Thread

import urllib.request
import json
from sqlmodel import Session
from src.database import engine
from src.services.ingestion import EmailIngestionService
from src.services.ai_classifier import AIClassifierService
from src.models import Email

logger = structlog.get_logger(__name__)

processed_mailpit_ids = set()

def poll_mailpit():
    req = urllib.request.Request("http://mailpit:8025/api/v1/messages")
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        
    messages = data.get("messages", [])
    if not messages:
        return
        
    with Session(engine) as session:
        for msg in messages:
            msg_id = msg.get("ID")
            if msg_id and msg_id not in processed_mailpit_ids:
                # Fetch details
                detail_req = urllib.request.Request(f"http://mailpit:8025/api/v1/message/{msg_id}")
                with urllib.request.urlopen(detail_req) as detail_res:
                    detail_data = json.loads(detail_res.read().decode())
                    
                subject = detail_data.get("Subject", "No Subject")
                sender = detail_data.get("From", {}).get("Address", "Unknown")
                body = detail_data.get("Text", "No Body")
                
                new_email = Email(sender=sender, subject=subject, body=body.strip(), status="inbox")
                session.add(new_email)
                processed_mailpit_ids.add(msg_id)
                logger.info("Ingested email from Mailpit", mailpit_id=msg_id)
        session.commit()

def worker_loop():
    logger.info("Starting replyme worker loop...")
    ingestion_service = EmailIngestionService()
    classifier_service = AIClassifierService()

    while True:
        # Poll Mailpit for incoming emails
        poll_mailpit()

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
            logger.exception("Fatal error in worker loop, crashing container to allow restart", error=str(e))
            raise
        
        # Sleep before next poll
        time.sleep(5)

if __name__ == "__main__":
    # Run main worker loop
    worker_loop()
