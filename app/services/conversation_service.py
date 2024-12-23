import json
from azure.data.tables import TableServiceClient, UpdateMode
from azure.storage.blob import BlobServiceClient
from fastapi import HTTPException
from models import Conversation, Message, Context
from config import Config
from typing import List
from azure.core.exceptions import ResourceNotFoundError
import uuid
from services.llm_service import query_llm
from services.context_service import ContextService
from services.message_service import MessageService
from utils.logger import logger
from datetime import datetime

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
        self.contexts_blob_service = BlobServiceClient.from_connection_string(connection_string)
        self.contexts_blob_container = self.contexts_blob_service.get_container_client(Config.AZURE_STORAGE_CONTEXTS_BLOB_CONTAINER)
        self.context_service = ContextService()
        self.message_service = MessageService()

    async def save_conversation(self, conversation: Conversation):      
        logger.info(f"Saving conversation: {conversation}")
        if conversation.conversation_id is None and conversation.messages is not None and len(conversation.messages) > 0:            
            try:
                conversation_entity = await self.create_conversation(conversation)
                logger.info(f"Created conversation: {conversation_entity}")
            except Exception as e:
                logger.error(f"Error creating conversation: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        else:
            try:
                conversation.updated_at = datetime.now().isoformat()
                conversation_entity = await self.update_conversation(conversation)
                logger.info(f"Updated conversation: {conversation_entity}")
            except Exception as e:
                logger.error(f"Error updating conversation: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        messages_without_id = [message for message in conversation.messages if message.message_id is None]

        # Save each message separately using MessageService
        for message in messages_without_id:
            logger.info(f"Saving message: {message}")
            await self.message_service.save_message(message, conversation.conversation_id)
        
        return conversation
    
    async def create_conversation(self, conversation: Conversation):
        first_message = conversation.messages[0].content
        # prompt = f"Generate a short description for the following conversation. This description \
        # will be saved as the title of the conversation for future reference, so it needs to be concise and descriptive: {first_message}"
        # logger.info(f"Generating description for conversation: {prompt}")
        # conversation.description = await query_llm(prompt)
        # logger.info(f"Generated description: {conversation.description}")
        conversation.conversation_id = str(uuid.uuid4())
        conversation_entity = {
            "PartitionKey": "conversations",
            "RowKey": conversation.conversation_id,
            "username": conversation.username,
            "description": conversation.description,
            "conversation_id": conversation.conversation_id,
            "project_id": conversation.project_id,
            "updated_at": conversation.updated_at
        }
        logger.info(f"Creating conversation entity: {conversation_entity}")
        if conversation.description is None:
            conversation.description = "No description provided"
        convo_entity = self.conversations_table.create_entity(entity=conversation_entity)
        logger.info(f"Created conversation entity: {convo_entity}")
        return convo_entity

    async def update_conversation(self, conversation: Conversation):
        conversation_entity = {
            "PartitionKey": "conversations",
            "RowKey": conversation.conversation_id,
            "username": conversation.username,
            "description": conversation.description,
            "conversation_id": conversation.conversation_id,
            "project_id": conversation.project_id,
            "updated_at": conversation.updated_at
        }
        convo_entity = self.conversations_table.update_entity(entity=conversation_entity, mode=UpdateMode.MERGE)
        return convo_entity

    async def get_conversation(self, conversation_id: str) -> Conversation:
        try:
            conversation_entity = self.conversations_table.get_entity(partition_key="conversations", row_key=conversation_id)
            messages = await self.message_service.get_messages_by_conversation_id(conversation_id)
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
            messages = await self.message_service.get_messages_by_conversation_id(entity['RowKey'])
            conversation = Conversation(
                conversation_id=entity['RowKey'],
                username=entity['username'],
                description=entity.get('description', ''),
                messages=messages
            )
            result.append(conversation)
            
        return result

    async def get_conversations_by_project_id(self, project_id: str, include_messages: bool = True) -> List[Conversation]:
        try:
            # Query conversations table for all conversations with this project_id
            conversations = self.conversations_table.query_entities(
                f"PartitionKey eq 'conversations' and project_id eq '{project_id}'"
            )
            
            # Convert entities to Conversation objects and include messages if requested
            result = []
            for conv in conversations:
                conversation = self.create_conversation_from_entity(conv)
                if include_messages:
                    # Get messages for this conversation
                    messages = await self.message_service.get_messages_by_conversation_id(conversation.conversation_id)
                    conversation.messages = messages
                result.append(conversation)
                
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def create_conversation_from_entity(self, entity: dict) -> Conversation:
        return Conversation(
            conversation_id=entity['RowKey'],
            project_id=entity.get('project_id'),
            username=entity.get('username'),
            description=entity.get('description', ''),
            messages=[]  # Will be populated separately
        )
