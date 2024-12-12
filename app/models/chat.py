from pydantic import BaseModel
from typing import List, Literal, Dict
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