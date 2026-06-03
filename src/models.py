from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime

class Email(SQLModel, table=True):
    __tablename__ = "emails"  # Optional, but explicit is better
    
    id: Optional[int] = Field(default=None, primary_key=True)
    sender: str
    subject: str
    body: str
    body_html: Optional[str] = None
    status: str = Field(default="inbox")  # inbox, processing, done, error
    ai_category: Optional[str] = None
    ai_sentiment: Optional[str] = None
    ai_urgency: Optional[str] = None
    ai_summary: Optional[str] = None
    ai_response: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None

class KanbanColumn(SQLModel, table=True):
    __tablename__ = "kanban_columns"
    
    status_key: str = Field(primary_key=True)
    name: str
    position: int
    rule_category: Optional[str] = None
    rule_urgency: Optional[str] = None
    is_system: bool = Field(default=False)

class EmailHistory(SQLModel, table=True):
    __tablename__ = "email_history"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    email_id: int = Field(index=True)
    action: str
    from_status: Optional[str] = None
    to_status: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

