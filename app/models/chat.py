from pydantic import BaseModel
from typing import List, Literal, Dict

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
    api_keys: Dict[str, str] = {} 