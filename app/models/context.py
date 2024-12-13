from pydantic import BaseModel
from typing import Optional

class Context(BaseModel):
    type: str
    content: str
    error: Optional[str] = None