from typing import Optional, List
from pydantic import BaseModel
from .context import Context
from .conversation import Conversation
from datetime import datetime

class Project(BaseModel):
    project_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    contexts: List[Context] = []
    conversations: List[Conversation] = []  # List of conversations
    username: Optional[str] = None  # Optional user association
    is_public: bool = False  # Indicates if the project is public
    updated_at: str = datetime.now().isoformat()  # Updated timestamp
