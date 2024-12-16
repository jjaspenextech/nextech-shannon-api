from typing import Optional, List
from pydantic import BaseModel
from .message import Message
from datetime import datetime

class Conversation(BaseModel):
    conversation_id: Optional[str] = None
    username: str
    messages: List[Message] = []
    description: Optional[str] = None
    project_id: Optional[str] = None  # Reference to the associated project
    updated_at: datetime = datetime.now().isoformat()
