from azure.data.tables import TableServiceClient, UpdateMode
from fastapi import HTTPException
from models import Message
from config import Config
from typing import List
import json
import uuid
from services.context_service import ContextService

class MessageService:
    def __init__(self):
        connection_string = (
            f"DefaultEndpointsProtocol=https;"
            f"AccountName={Config.AZURE_STORAGE_ACCOUNT_NAME};"
            f"AccountKey={Config.AZURE_STORAGE_ACCOUNT_KEY};"
            f"EndpointSuffix={Config.AZURE_STORAGE_ENDPOINT_SUFFIX}"
        )
        self.table_service = TableServiceClient.from_connection_string(connection_string)
        self.messages_table = self.table_service.get_table_client(Config.AZURE_STORAGE_MESSAGES_TABLE_NAME)
        self.context_service = ContextService()

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
            # Save contexts and get their IDs
            entity = self.messages_table.create_entity(entity=message_entity)
            existing_contexts = await self.context_service.get_contexts_by_message_id(message.message_id)
            # add new contexts to the message
            for context in message.contexts:
                if context.context_id not in [existing_context.context_id for existing_context in existing_contexts]:
                    await self.context_service.save_context(context)
            return entity
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def get_messages_by_conversation_id(self, conversation_id: str) -> List[Message]:
        filter_query = f"PartitionKey eq 'messages' and conversation_id eq '{conversation_id}'"
        messages = self.messages_table.query_entities(filter_query)
        result = []
        for message in messages:
            contexts = await self.context_service.get_contexts_by_message_id(message['message_id'])
            message['contexts'] = contexts
            result.append(Message(**message))
        return result 

    async def get_first_message_by_conversation_id(self, conversation_id: str) -> Message:
        filter_query = f"PartitionKey eq 'messages' and conversation_id eq '{conversation_id}'"
        messages = self.messages_table.query_entities(filter_query)
        
        # Convert the paged results to a list and sort by sequence
        messages_list = list(messages)
        if not messages_list:
            return None
        
        # Sort messages by the 'sequence' property
        messages_list.sort(key=lambda msg: msg['sequence'])
        
        # Get the first message after sorting
        first_message_entity = messages_list[0]
        contexts = await self.context_service.get_contexts_by_message_id(first_message_entity['message_id'])
        first_message_entity['contexts'] = contexts
        return Message(**first_message_entity)
