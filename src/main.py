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
from src.models import Email, EmailHistory, KanbanColumn, MCPServer
import asyncio
from src.services.mcp_installer import run_installer_loop
from src.services.mcp_agent import run_mcp_agent

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
                
                # Fetch recipient (To) address
                to_addresses = detail_data.get("To", [])
                recipient = to_addresses[0].get("Address", "suporte@replyme.local") if to_addresses else "suporte@replyme.local"

                body = detail_data.get("Text", "No Body")
                body_html = detail_data.get("HTML", "")
                
                new_email = Email(sender=sender, recipient=recipient, subject=subject, body=body.strip(), body_html=body_html, status="inbox")
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
                            # Execute Agent if Column has MCPs
                            matched_col = next((c for c in rules if c.status_key == matched_status), None)
                            if matched_col and matched_col.mcp_servers:
                                try:
                                    mcp_configs = json.loads(matched_col.mcp_servers)
                                    for cfg in mcp_configs:
                                        mcp_id = cfg.get("mcp_id")
                                        prompt = cfg.get("prompt")
                                        
                                        # fetch MCP server
                                        from sqlmodel import select
                                        mcp_server = session.exec(select(MCPServer).where(MCPServer.id == mcp_id)).first()
                                        
                                        if mcp_server and mcp_server.status == "installed" and mcp_server.inferred_command:
                                            # execute agent
                                            logger.info("Executing MCP Agent", mcp_id=mcp_id, email_id=email.id)
                                            agent_result = asyncio.run(run_mcp_agent(
                                                email_json=email.model_dump(),
                                                prompt=prompt,
                                                command=mcp_server.inferred_command
                                            ))
                                            
                                            # Save to Tracker (EmailHistory)
                                            hist = EmailHistory(
                                                email_id=email.id,
                                                action=f"Agent Execution (MCP: {mcp_server.name}):\n{agent_result}",
                                                from_status=matched_status,
                                                to_status=matched_status
                                            )
                                            session.add(hist)
                                except Exception as e:
                                    logger.error("Error executing MCP agent", error=str(e))
                            
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
                                msg['From'] = email.recipient
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

from http.server import BaseHTTPRequestHandler, HTTPServer

class MCPTestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/test_mcp':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            mcp_id = data.get('mcp_id')
            prompt = data.get('prompt')
            
            try:
                with Session(engine) as session:
                    from sqlmodel import select
                    from src.models import MCPServer
                    mcp = session.exec(select(MCPServer).where(MCPServer.id == mcp_id)).first()
                    if not mcp or not mcp.inferred_command:
                        self.send_response(400)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(b'{"error": "MCP not found or not installed"}')
                        return
                    command = mcp.inferred_command
                
                result = asyncio.run(run_mcp_agent({}, prompt, command))
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"result": result}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def http_server_loop():
    server_address = ('0.0.0.0', 8000)
    httpd = HTTPServer(server_address, MCPTestHandler)
    logger.info("Starting internal HTTP server on port 8000")
    httpd.serve_forever()

if __name__ == "__main__":
    # Run dispatch loop in background
    dispatch_thread = Thread(target=dispatch_loop, daemon=True)
    dispatch_thread.start()
    
    # Run installer loop in background
    installer_thread = Thread(target=run_installer_loop, daemon=True)
    installer_thread.start()

    # Run internal HTTP API in background
    http_thread = Thread(target=http_server_loop, daemon=True)
    http_thread.start()
    
    # Run main worker loop
    worker_loop()
