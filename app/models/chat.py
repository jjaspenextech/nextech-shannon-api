from pydantic import BaseModel
from typing import List, Literal, Dict, Optional
from .message import Message

class ChatRequest(BaseModel):
    messages: List[Message]
    project_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str

class User(BaseModel):
    username: str
    password: Optional[str] = None
    email: str
    first_name: str
    last_name: str
    api_keys: Dict[str, str] = {}

    def get_api_key(self, service: str) -> str:
        if not (key := self.api_keys.get(service)):
            raise ValueError(f"No API key found for service: {service}")
        return key

class ApiKeyUpdate(BaseModel):
    service: Literal['jira']  # We can add more services later
    key: str

class ApiKeys(BaseModel):
    jira: Optional[str] = None 