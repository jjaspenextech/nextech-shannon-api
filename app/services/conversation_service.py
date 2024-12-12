import json
from azure.data.tables import TableServiceClient, UpdateMode
from fastapi import HTTPException
from models.chat import Conversation, Message
from services.llm_service import query_llm
from config import Config
from typing import List
from azure.core.exceptions import ResourceNotFoundError

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

    async def save_conversation(self, conversation: Conversation):
        if len(conversation.messages) == 1:
            first_message = conversation.messages[0].content
            prompt = f"Generate a short description for the following conversation. This description \
            will be saved as the title of the conversation for future reference, so it needs to be concise and descriptive: {first_message}"
            conversation.description = await query_llm(prompt)

        conversation_entity = {
            "PartitionKey": "conversations",
            "RowKey": conversation.conversation_id,
            "username": conversation.username,
            "description": conversation.description,
            "messages": json.dumps([msg.dict() for msg in conversation.messages])
        }

        try:
            existing_entity = self.conversations_table.get_entity(partition_key="conversations", row_key=conversation.conversation_id)
            existing_entity["messages"] = json.dumps([msg.dict() for msg in conversation.messages])
            self.conversations_table.update_entity(entity=existing_entity, mode=UpdateMode.MERGE)
        except ResourceNotFoundError:
            self.conversations_table.create_entity(entity=conversation_entity)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def get_conversation(self, conversation_id: str) -> List[Message]:
        try:
            conversation_entity = self.conversations_table.get_entity(partition_key="conversations", row_key=conversation_id)
            messages_json = conversation_entity["messages"]
            messages = json.loads(messages_json)
            return [Message(**msg) for msg in messages]
        except Exception as e:
            raise HTTPException(status_code=404, detail="Conversation not found") 