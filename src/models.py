from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime

class Email(SQLModel, table=True):
    __tablename__ = "emails"  # Optional, but explicit is better
    
    id: Optional[int] = Field(default=None, primary_key=True)
    sender: str
    subject: str
    body: str
    status: str = Field(default="inbox")  # inbox, processing, done, error
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
