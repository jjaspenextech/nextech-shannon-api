import json
from azure.data.tables import TableServiceClient, UpdateMode
from azure.storage.blob import BlobServiceClient
from fastapi import HTTPException
from models.chat import Conversation, Message, Context
from config import Config
from typing import List
from azure.core.exceptions import ResourceNotFoundError
import uuid
from services.llm_service import query_llm
from services.context_service import ContextService

class ConversationService:
    def __init__(self):
        connection_string = (
            f"DefaultEndpointsProtocol=https;"
            f"AccountName={Config.AZURE_STORAGE_ACCOUNT_NAME};"
            f"AccountKey={Config.AZURE_STORAGE_ACCOUNT_KEY};"
            f"EndpointSuffix={Config.AZURE_STORAGE_ENDPOINT_SUFFIX}"
        )
        self.table_service = TableServiceClient.from_connection_string(connection_string)
        self.conversations_table = self.table_service.get_table_client(Config.AZURE_STORAGE_CONVERSATIONS_TABLE_NAME)
        self.messages_table = self.table_service.get_table_client(Config.AZURE_STORAGE_MESSAGES_TABLE_NAME)
        self.contexts_blob_service = BlobServiceClient.from_connection_string(connection_string)
        self.contexts_blob_container = self.contexts_blob_service.get_container_client(Config.AZURE_STORAGE_CONTEXTS_BLOB_CONTAINER)
        self.context_service = ContextService()
        

    async def save_conversation(self, conversation: Conversation):      
        if conversation.conversation_id is None and conversation.messages is not None and len(conversation.messages) > 0:            
            try:
                first_message = conversation.messages[0].content
                prompt = f"Generate a short description for the following conversation. This description \
                will be saved as the title of the conversation for future reference, so it needs to be concise and descriptive: {first_message}"
                conversation.description = await query_llm(prompt)
                conversation.conversation_id = str(uuid.uuid4())
                conversation_entity = {
                    "PartitionKey": "conversations",
                    "RowKey": conversation.conversation_id,
                    "username": conversation.username,
                    "description": conversation.description,
                    "conversation_id": conversation.conversation_id
                }
                if conversation.description is None:
                    conversation.description = "No description provided"
                convo_entity = self.conversations_table.create_entity(entity=conversation_entity)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        messages_without_id = [message for message in conversation.messages if message.message_id is None]

        # Save each message separately
        for message in messages_without_id:
            await self.save_message(message, conversation.conversation_id)
        
        return conversation

    async def save_message(self, message: Message, conversation_id: str):
        message.message_id = str(uuid.uuid4())
        message.conversation_id = conversation_id
        message_entity = {
            "PartitionKey": "messages",
            "RowKey": message.message_id,
            "conversation_id": conversation_id,
            "content": message.content,
            "sequence": message.sequence,
            "role": message.role,
            "message_id": message.message_id
        }
        try:
            context_names = [await self.context_service.save_context(context, message.message_id) for context in message.contexts]
            message_entity['contexts'] = json.dumps(context_names)
            entity = self.messages_table.create_entity(entity=message_entity)
            return entity
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def get_conversation(self, conversation_id: str) -> Conversation:
        try:
            conversation_entity = self.conversations_table.get_entity(partition_key="conversations", row_key=conversation_id)
            messages = await self.get_messages_by_conversation_id(conversation_id)
            sorted_messages = sorted(messages, key=lambda msg: msg.sequence)
            
            return Conversation(
                conversation_id=conversation_entity['conversation_id'],
                username=conversation_entity['username'],
                description=conversation_entity.get('description'),
                messages=sorted_messages
            )
        except Exception as e:
            raise HTTPException(status_code=404, detail="Conversation not found")

    async def get_conversations_by_username(self, username: str) -> List[Conversation]:
        # Query all conversations for the user
        filter_query = f"PartitionKey eq 'conversations' and username eq '{username}'"
        conversations = self.conversations_table.query_entities(filter_query)

        # Convert the entities to Conversation objects
        result = []
        for entity in conversations:
            messages = await self.get_messages_by_conversation_id(entity['RowKey'])
            conversation = Conversation(
                conversation_id=entity['RowKey'],
                username=entity['username'],
                description=entity.get('description', ''),
                messages=messages
            )
            result.append(conversation)
            
        return result

    async def get_messages_by_conversation_id(self, conversation_id: str) -> List[Message]:
        filter_query = f"PartitionKey eq 'messages' and conversation_id eq '{conversation_id}'"
        messages = self.messages_table.query_entities(filter_query)
        result = []
        for message in messages:
            blob_names = json.loads(message['contexts'])
            contexts = []
            for blob_name in blob_names:
                context = await self.context_service.get_context(message['message_id'], blob_name)
                contexts.append(context)
            message['contexts'] = contexts
            result.append(Message(**message))
        return result
