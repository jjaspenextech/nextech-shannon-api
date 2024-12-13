from pydantic import BaseModel
from typing import List, Literal, Dict, Optional
import uuid

class Context(BaseModel):
    type: str
    content: str
    error: Optional[str] = None

class Message(BaseModel):
    message_id: Optional[str] = None
    conversation_id: Optional[str] = None
    content: str
    contexts: List[Context] = []
    sequence: int = 0
    role: Literal['user', 'assistant', 'system']

class ChatRequest(BaseModel):
    messages: List[Message]

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

class Conversation(BaseModel):
    conversation_id: Optional[str] = None
    username: str
    messages: List[Message] = []
    description: Optional[str] = None

class ApiKeyUpdate(BaseModel):
    service: Literal['jira']  # We can add more services later
    key: str

class ApiKeys(BaseModel):
    jira: Optional[str] = None 