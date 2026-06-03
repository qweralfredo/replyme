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
from src.models import Email, EmailHistory, KanbanColumn

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
                body_html = detail_data.get("HTML", "")
                
                new_email = Email(sender=sender, subject=subject, body=body.strip(), body_html=body_html, status="inbox")
                session.add(new_email)
                session.flush() # Get email.id
                
                from src.models import EmailHistory
                history = EmailHistory(email_id=new_email.id, action="Email ingested from Mailpit", to_status="inbox")
                session.add(history)
                
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
                            email.ai_response = classification.response
                            
                            # Fetch columns rules to determine status
                            from src.models import KanbanColumn
                            rules = session.exec(select(KanbanColumn)).all()
                            
                            matched_status = "review" # Default fallback
                            for col in rules:
                                # Simple matching logic (ignore case)
                                cat_match = True
                                urg_match = True
                                
                                if col.rule_category:
                                    cat_match = col.rule_category.lower() == classification.category.lower()
                                if col.rule_urgency:
                                    urg_match = col.rule_urgency.lower() == str(classification.urgency).lower()
                                    
                                if col.rule_category or col.rule_urgency:
                                    if cat_match and urg_match:
                                        matched_status = col.status_key
                                        break
                                        
                            email.status = matched_status
                            email.processed_at = datetime.utcnow()
                            session.add(email)
                            
                            history = EmailHistory(
                                email_id=email.id, 
                                action=f"AI Classification (Cat: {email.ai_category}, Urg: {email.ai_urgency})", 
                                from_status="processing", 
                                to_status=matched_status
                            )
                            session.add(history)
                            
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

def dispatch_loop():
    import smtplib
    from email.message import EmailMessage
    
    logger.info("Starting replyme dispatch queue loop...")
    while True:
        try:
            with Session(engine) as session:
                from sqlmodel import select
                from src.models import Email
                
                # Fetch pending emails to send
                statement = select(Email).where(Email.status == "to_send").limit(5).with_for_update(skip_locked=True)
                pending_dispatch = list(session.exec(statement).all())
                
                if pending_dispatch:
                    try:
                        with smtplib.SMTP('mailpit', 1025) as s:
                            for email in pending_dispatch:
                                msg = EmailMessage()
                                msg.set_content(email.ai_response or "No response provided.")
                                msg['Subject'] = f"Re: {email.subject}"
                                msg['From'] = 'suporte@replyme.local'
                                msg['To'] = email.sender
                                
                                s.send_message(msg)
                                logger.info("Dispatched automated reply", id=email.id, to=email.sender)
                                
                                email.status = "sent"
                                session.add(email)
                                
                                from src.models import EmailHistory
                                history = EmailHistory(
                                    email_id=email.id,
                                    action="Automated reply sent via SMTP",
                                    from_status="to_send",
                                    to_status="sent"
                                )
                                session.add(history)
                    except Exception as smtp_err:
                        logger.error("Failed to connect to SMTP server", error=str(smtp_err))
                    
                    session.commit()
        except Exception as e:
            logger.exception("Fatal error in dispatch loop", error=str(e))
        
        time.sleep(3)


if __name__ == "__main__":
    # Run dispatch loop in background
    dispatch_thread = Thread(target=dispatch_loop, daemon=True)
    dispatch_thread.start()
    
    # Run main worker loop
    worker_loop()
