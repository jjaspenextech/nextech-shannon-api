from typing import Optional, List
from pydantic import BaseModel
from .context import Context

class Project(BaseModel):
    project_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    contexts: List[Context] = []
    conversations: List[str] = []  # List of conversation IDs associated with this project
    username: Optional[str] = None  # Optional user association
    is_public: bool = False  # Indicates if the project is public