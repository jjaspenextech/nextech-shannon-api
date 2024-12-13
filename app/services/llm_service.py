import json
import httpx
from config import Config
from utils.logger import setup_logger
from models.chat import Message
from typing import Literal, Optional, List, Dict
import math
logger = setup_logger(__name__)
MAX_TOKENS = 8000

def build_message_context(message: Message, ignore_contexts: bool = False):
    context_str = "\nContexts: " + ", ".join(
        [f"{context.type}: {context.content}" for context in message.contexts]
    ) if message.contexts else ""
    return {
        "role": message.role,
        "content": f"{message.content}{context_str}" if not ignore_contexts else message.content
    }

def build_contexts(messages: list[Message], max_tokens: int) -> list[str]:
    contexts = []
    max_input_tokens = math.floor(max_tokens*0.9)
    messages_sorted_by_sequence_desc = sorted(messages, key=lambda x: x.sequence, reverse=True)
    for message in messages_sorted_by_sequence_desc:
        msg_str = build_message_context(message)
        if (len(contexts) + len(msg_str)) / 3 > max_input_tokens:
            msg_str = build_message_context(message, ignore_contexts=True)
            if (len(contexts) + len(msg_str)) / 3 > max_input_tokens:
                break
        # add to the front of the list
        contexts.insert(0, msg_str)
    
    return contexts

async def get_query_params(messages: list[Message], stream: bool = False):    
    chat_messages = build_contexts(messages, MAX_TOKENS)
    # Add system message if not present
    if not any(msg['role'] == 'system' for msg in chat_messages):
        chat_messages.insert(0, {
            "role": 'system',
            "content": "You are a helpful AI assistant for a company's internal chat system. "
                   "Provide clear, professional responses while maintaining a friendly tone. "
                   "If you're unsure about something, acknowledge the uncertainty and suggest alternatives "
                   "or ask for clarification."
        })
    
    headers = {
        "api-key": Config.AZURE_OPENAI_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "messages": chat_messages, 
        "max_tokens": MAX_TOKENS,
        "temperature": 0
    }
    
    if stream:
        payload["stream"] = True
    
    url = f"{Config.AZURE_OPENAI_URL}openai/deployments/{Config.AZURE_OPENAI_MODEL}/chat/completions?api-version={Config.AZURE_OPENAI_API_VERSION}"
    
    return headers, payload, url

async def query_llm(content: str):
    messages = [Message(role="user", content=content)]
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