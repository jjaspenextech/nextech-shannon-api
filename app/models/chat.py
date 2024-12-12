from pydantic import BaseModel
from typing import List, Literal, Dict, Optional
import uuid

class Message(BaseModel):
    role: Literal['user', 'assistant', 'system']
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

class ChatResponse(BaseModel):
    response: str

class User(BaseModel):
    username: str
    password: str
    email: str
    first_name: str
    last_name: str
    api_keys: Dict[str, str] = {}

class Conversation(BaseModel):
    conversation_id: str = str(uuid.uuid4())
    username: str
    messages: List[Message]
    description: str = "" 

class ApiKeyUpdate(BaseModel):
    service: Literal['jira']  # We can add more services later
    key: str

class ApiKeys(BaseModel):
    jira: Optional[str] = None 