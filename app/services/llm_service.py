import json
import httpx
from config import Config
from utils.logger import setup_logger
from models.chat import Message
from typing import Literal
logger = setup_logger(__name__)

class LLMMessage():
    role: Literal['user', 'assistant', 'system']
    content: str
    contexts: List[str] = []

    def __init__(self, role: Literal['user', 'assistant', 'system'], content: str):
        self.role = role
        self.content = content

    def dict(self):
        return {
            "role": self.role,
            "content": f"{self.content}\nContexts: {self.contexts}" if self.contexts else self.content
        }

MAX_TOKENS = 8000

def truncate_messages(messages: list[Message]) -> list[Message]:
    """Truncate messages to fit within context window"""
    total_chars = sum(len(msg.content) for msg in messages)
    
    if total_chars / 3 <= MAX_TOKENS:
        return messages
    
    # Keep system message if it exists
    result = [msg for msg in messages if msg.role == 'system']
    remaining_messages = [msg for msg in messages if msg.role != 'system']
    
    while remaining_messages and sum(len(msg.content) for msg in result + remaining_messages) / 3 > MAX_TOKENS:
        remaining_messages.pop(0)  # Remove oldest messages first
    
    return result + remaining_messages

async def get_query_params(messages: list[LLMMessage], stream: bool = False):    
    # Add system message if not present
    if not any(msg.role == 'system' for msg in messages):
        messages.insert(0, LLMMessage(
            role='system',
            content="You are a helpful AI assistant for a company's internal chat system. "
                   "Provide clear, professional responses while maintaining a friendly tone. "
                   "If you're unsure about something, acknowledge the uncertainty and suggest alternatives "
                   "or ask for clarification."
        ))
    
    # Truncate messages to fit context window
    messages = truncate_messages(messages)
    
    headers = {
        "api-key": Config.AZURE_OPENAI_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "messages": [msg.dict() for msg in messages], 
        "max_tokens": 8000,
        "temperature": 0
    }
    
    if stream:
        payload["stream"] = True
    
    url = f"{Config.AZURE_OPENAI_URL}openai/deployments/{Config.AZURE_OPENAI_MODEL}/chat/completions?api-version={Config.AZURE_OPENAI_API_VERSION}"
    
    return headers, payload, url

async def query_llm(content: str):
    messages = [LLMMessage(role="user", content=content)]
    return await chat_with_llm(messages)

async def chat_with_llm(messages: list[Message]):
    headers, payload, url = await get_query_params(messages)
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        contents = json.loads(response.text)
        return contents['choices'][0]['message']['content']

async def chat_with_llm_stream(messages: list[Message]):
    logger.info(f"Starting streaming response for chat with {len(messages)} messages")
    
    headers, payload, url = await get_query_params(messages, stream=True)
    
    async with httpx.AsyncClient() as client:
        async with client.stream('POST', url, headers=headers, json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.strip():
                    if line.startswith('data: '):
                        line = line[6:]
                    if line != '[DONE]':
                        try:
                            chunk = json.loads(line)
                            if chunk and 'choices' in chunk and chunk['choices']:
                                content = chunk['choices'][0].get('delta', {}).get('content', '')
                                if content:
                                    yield content
                        except json.JSONDecodeError as e:
                            logger.error(f"Error parsing chunk: {str(e)}")
                            continue