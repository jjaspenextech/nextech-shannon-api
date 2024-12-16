from pydantic import BaseModel
from typing import Optional, List, Literal
from .context import Context
from datetime import datetime

class Message(BaseModel):
    message_id: Optional[str] = None
    conversation_id: Optional[str] = None
    content: str
    contexts: List[Context] = []
    sequence: int = 0
    role: Literal['user', 'assistant', 'system']
    timestamp: str = datetime.now().isoformat()