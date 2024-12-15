from pydantic import BaseModel
from typing import Optional

class Context(BaseModel):
    context_id: Optional[str] = None
    type: str
    content: str
    error: Optional[str] = None
    message_id: Optional[str] = None
    project_id: Optional[str] = None
    blob_name: Optional[str] = None