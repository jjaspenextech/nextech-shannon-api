import json
from azure.data.tables import TableServiceClient, UpdateMode
from fastapi import HTTPException
from models.chat import Conversation, Message
from config import Config
from typing import List
from azure.core.exceptions import ResourceNotFoundError
import uuid

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

    async def save_conversation(self, conversation: Conversation):      
        if conversation.conversation_id is None:
            conversation.conversation_id = str(uuid.uuid4())
            try:
                conversation_entity = {
                    "PartitionKey": "conversations",
                    "RowKey": conversation.conversation_id,
                    "username": conversation.username,
                    "description": conversation.description,
                    "conversation_id": conversation.conversation_id
                }
                convo_entity = self.conversations_table.create_entity(entity=conversation_entity)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        messages_without_id = [message for message in conversation.messages if message.message_id is None]

        # Save each message separately
        for index, message_data in enumerate(messages_without_id):
            id = str(uuid.uuid4())
            message_entity = {
                "PartitionKey": "messages",
                "RowKey": id,
                "conversation_id": conversation.conversation_id,
                "content": message_data.content,
                "contexts": json.dumps(message_data.contexts),
                "sequence": index,
                "message_id": id
            }
            try:
                entity = self.messages_table.create_entity(entity=message_entity)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

    async def get_conversation(self, conversation_id: str) -> Conversation:
        try:
            conversation_entity = self.conversations_table.get_entity(partition_key="conversations", row_key=conversation_id)
            messages = self.messages_table.query_entities(f"PartitionKey eq 'messages' and conversation_id eq '{conversation_id}'")
            sorted_messages = sorted(messages, key=lambda msg: msg['sequence'])
            
            return Conversation(
                conversation_id=conversation_entity['conversation_id'],
                username=conversation_entity['username'],
                description=conversation_entity.get('description'),
                messages=[Message(**{**msg, 'contexts': json.loads(msg['contexts'])}) for msg in sorted_messages]
            )
        except Exception as e:
            raise HTTPException(status_code=404, detail="Conversation not found")

    def get_conversations_by_username(self, username: str) -> List[Conversation]:
        # Query all conversations for the user
        filter_query = f"PartitionKey eq 'conversations' and username eq '{username}'"
        conversations = self.conversations_table.query_entities(filter_query)

        # Convert the entities to Conversation objects
        result = []
        for entity in conversations:
            messages = self.get_messages_by_conversation_id(entity['RowKey'])
            conversation = Conversation(
                conversation_id=entity['RowKey'],
                username=entity['username'],
                description=entity.get('description', ''),
                messages=messages
            )
            result.append(conversation)
            
        return result

    def get_messages_by_conversation_id(self, conversation_id: str) -> List[Message]:
        filter_query = f"PartitionKey eq 'messages' and conversation_id eq '{conversation_id}'"
        messages = self.messages_table.query_entities(filter_query)
        return [Message(**msg) for msg in messages]
