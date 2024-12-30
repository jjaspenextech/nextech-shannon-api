from pydantic import BaseModel
from typing import List, Literal, Dict, Optional
from .message import Message
from datetime import datetime

class ChatRequest(BaseModel):
    messages: List[Message]
    project_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str

class DescriptionRequest(BaseModel):
    prompt: str
    project_id: Optional[str] = None

class User(BaseModel):
    username: str
    password: Optional[str] = None
    email: str
    first_name: str
    last_name: str
    api_keys: Dict[str, str] = {}
    is_admin: bool = False
    theme: Optional[str] = None  # New field for theme preference

    def get_api_key(self, service: str) -> str:
        if not (key := self.api_keys.get(service)):
            raise ValueError(f"No API key found for service: {service}")
        return key

class ApiKeyUpdate(BaseModel):
    service: Literal['JIRA', 'GITHUB', 'SLACK', 'CONFLUENCE']  # We can add more services later
    key: str

class ApiKeys(BaseModel):
    jira: Optional[str] = None 

class SignupRequest(BaseModel):
    username: str
    password: str
    email: str
    first_name: str
    last_name: str
    signup_code: str  # New field