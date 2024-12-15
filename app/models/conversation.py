from typing import Optional, List
from pydantic import BaseModel
from .message import Message

class Conversation(BaseModel):
    conversation_id: Optional[str] = None
    username: str
    messages: List[Message] = []
    description: Optional[str] = None
    project_id: Optional[str] = None  # Reference to the associated project