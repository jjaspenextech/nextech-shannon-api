import json
import httpx
from config import Config
from utils.logger import setup_logger
from models.chat import Message

logger = setup_logger(__name__)

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

async def query_llm_stream(messages: list[Message]):
    logger.info(f"Starting streaming response for chat with {len(messages)} messages")
    
    # Add system message if not present
    if not any(msg.role == 'system' for msg in messages):
        messages.insert(0, Message(
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
        "temperature": 0,
        "stream": True
    }
    
    url = f"{Config.AZURE_OPENAI_URL}openai/deployments/{Config.AZURE_OPENAI_MODEL}/chat/completions?api-version={Config.AZURE_OPENAI_API_VERSION}"
    
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