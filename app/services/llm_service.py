import json
import httpx
from config import Config
from utils.logger import logger
from models.chat import Message
from typing import Literal, Optional, List, Dict
import math
MAX_TOKENS = Config.MAX_TOKENS

def build_chat_message_with_contexts(message: Message, contexts: list = None):
    text_contexts = [ctx for ctx in contexts if ctx.type != 'image'] if contexts != None else None
    image_contexts = [ctx for ctx in contexts if ctx.type == 'image']
    context_parts = [f"{ctx.type}: {ctx.content}" for ctx in text_contexts]
    
    context_str = "\nContexts: " + ", ".join(context_parts) if context_parts else ""
    text_content = f"{message.content}{context_str}" if text_contexts != None else message.content
    chat_message = {
        "role": message.role,
        "content": text_content
    }

    if image_contexts:
        # build image content for each image context
        chat_message['content'] = [{"type": "text", "text": text_content}]
        for ctx in image_contexts:
            if ctx.type == 'image':
                chat_message['content'].append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{ctx.content}"}})

    return chat_message

# Find the earliest user message and update it to include project contexts
def add_project_contexts(chat_messages: list, messages: list[Message], project_contexts: list = None):
    for i in range(len(chat_messages)-1, -1, -1):
        if chat_messages[i]['role'] == 'user':
            all_contexts = messages[i].contexts
            all_contexts.extend(project_contexts)
            chat_messages[i]['content'] = build_chat_message_with_contexts(messages[i], all_contexts)['content']
            break

def build_chat_messages_for_api(messages: list[Message], project_contexts: list = None, max_tokens: int = MAX_TOKENS) -> list[str]:
    chat_messages = []
    max_input_tokens = math.floor(max_tokens * 0.9)
    
    # Calculate the length of the project contexts
    project_context_str = "\nContexts: " + ", ".join([f"{ctx.type}: {ctx.content}" for ctx in project_contexts]) if project_contexts else ""
    project_context_length = len(project_context_str)
    
    # Adjust max tokens to account for project contexts
    adjusted_max_tokens = max_input_tokens - project_context_length
    
    messages_sorted_by_sequence_desc = sorted(messages, key=lambda x: x.sequence, reverse=True)
    
    for message in messages_sorted_by_sequence_desc:
        msg_str = build_chat_message_with_contexts(message, message.contexts)
        if (len(chat_messages) + len(msg_str)) / 3 > adjusted_max_tokens:
            msg_str = build_chat_message_with_contexts(message, [])
            if (len(chat_messages) + len(msg_str)) / 3 > adjusted_max_tokens:
                break
        chat_messages.insert(0, msg_str)
    
    add_project_contexts(chat_messages, messages, project_contexts)

    return chat_messages

def add_conversation_system_message(chat_messages: list):
    if not any(msg['role'] == 'system' for msg in chat_messages):
        chat_messages.insert(0, {
            "role": 'system',
            "content": "You are a helpful AI assistant for a company's internal chat system. "
                   "Provide clear, professional responses while maintaining a friendly tone. "
                   "If you're unsure about something, acknowledge the uncertainty and suggest alternatives "
                   "or ask for clarification."
        })

async def get_api_call_params(chat_messages: list[dict], contexts: list = None):
    headers = {
        "api-key": Config.AZURE_OPENAI_API_KEY,
        "Content-Type": "application/json"
    }
    logger.info(f"Headers: {headers}")
    
    payload = {
        "messages": chat_messages, 
        "max_tokens": MAX_TOKENS,
        "temperature": 0
    }
    
    url = f"{Config.AZURE_OPENAI_URL}openai/deployments/{Config.AZURE_OPENAI_MODEL}/chat/completions?api-version={Config.AZURE_OPENAI_API_VERSION}"
    logger.info(f"URL: {url}")
    logger.info(f"Payload: {payload}")
    return headers, payload, url

async def query_llm(content: str):
    logger.info(f"Querying LLM with content: {content}")
    messages = [Message(role="user", content=content)]
    return await chat_with_llm(messages)

async def chat_with_llm(messages: list[Message]):
    logger.info(f"Chatting with LLM with {len(messages)} messages")
    chat_messages = build_chat_messages_for_api(messages)
    add_conversation_system_message(chat_messages)
    headers, payload, url = await get_api_call_params(chat_messages)
    return await call_llm_api(headers, payload, url)

async def call_llm_api(headers, payload, url):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            contents = json.loads(response.text)
            return contents['choices'][0]['message']['content']
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            raise

async def chat_with_llm_stream(messages: list[Message], contexts: list = None):
    logger.info(f"Starting streaming response for chat with {len(messages)} messages")
    chat_messages = build_chat_messages_for_api(messages, contexts)
    add_conversation_system_message(chat_messages)
    headers, payload, url = await get_api_call_params(chat_messages)
    payload["stream"] = True
    
    async with httpx.AsyncClient() as client:
        try:
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
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred during streaming: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"An error occurred during streaming: {str(e)}")
            raise

async def generate_conversation_description_with_llm(first_message: str, contexts: list = []) -> str:
    prompt = f"You are an assistant that generates short descriptions for conversations. "
    "This description will be saved as the title of the conversation for future reference, "
    "so it needs to be concise and descriptive."
    logger.info(f"Generating description with prompt: {prompt}")
    system_message = {
        "role": "system",
        "content": prompt.format(first_message)
    }
    first_message = f"The first message in the conversation is: {first_message}"
    user_message = build_chat_message_with_contexts(Message(role="user", content=first_message), contexts)
    messages = [system_message, user_message]    
    try:
        headers, payload, url = await get_api_call_params(messages)
        return await call_llm_api(headers, payload, url)
    except Exception as e:
        logger.error(f"Error generating description: {str(e)}")
        return "Error generating description"