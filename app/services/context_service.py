from azure.storage.blob import BlobServiceClient
from azure.data.tables import TableServiceClient, UpdateMode
from fastapi import HTTPException
from models.context import Context
from config import Config
import json
import uuid
from typing import List

class ContextService:
    def __init__(self):
        connection_string = (
            f"DefaultEndpointsProtocol=https;"
            f"AccountName={Config.AZURE_STORAGE_ACCOUNT_NAME};"
            f"AccountKey={Config.AZURE_STORAGE_ACCOUNT_KEY};"
            f"EndpointSuffix={Config.AZURE_STORAGE_ENDPOINT_SUFFIX}"
        )
        self.table_service = TableServiceClient.from_connection_string(connection_string)
        self.contexts_table = self.table_service.get_table_client(Config.AZURE_STORAGE_CONTEXTS_TABLE_NAME)
        self.contexts_blob_service = BlobServiceClient.from_connection_string(connection_string)
        self.contexts_blob_container = self.contexts_blob_service.get_container_client(Config.AZURE_STORAGE_CONTEXTS_BLOB_CONTAINER)

    async def save_context(self, context: Context) -> str:
        context.context_id = str(uuid.uuid4())
        
        # Save to blob storage
        blob_name = f"{context.context_id}.json"
        context.blob_name = blob_name
        blob_client = self.contexts_blob_container.get_blob_client(blob_name)
        
        try:
            # Save content to blob
            blob_client.upload_blob(json.dumps({"content": context.content}))
            
            # Save metadata to table
            context_entity = {
                "PartitionKey": "contexts",
                "RowKey": context.context_id,
                "name": context.name,
                "type": context.type,
                "blob_name": blob_name,
                "message_id": context.message_id,
                "project_id": context.project_id
            }
            self.contexts_table.create_entity(entity=context_entity)
            
            return context
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error saving context: {str(e)}")

    async def get_context(self, context_id: str) -> Context:
        try:
            # Get metadata from table
            context_entity = self.contexts_table.get_entity(
                partition_key="contexts",
                row_key=context_id
            )
            
            # Get content from blob
            blob_client = self.contexts_blob_container.get_blob_client(context_entity['blob_name'])
            context_data = json.loads(blob_client.download_blob().readall())
            
            return Context(
                context_id=context_id,
                type=context_entity['type'],
                content=context_data['content'],
                message_id=context_entity.get('message_id'),
                project_id=context_entity.get('project_id'),
                blob_name=context_entity['blob_name']
            )
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Context not found: {str(e)}")

    async def get_contexts_by_project_id(self, project_id: str) -> List[Context]:
        try:
            filter_query = f"PartitionKey eq 'contexts' and project_id eq '{project_id}'"
            contexts = []
            
            for entity in self.contexts_table.query_entities(filter_query):
                blob_client = self.contexts_blob_container.get_blob_client(entity['blob_name'])
                context_data = json.loads(blob_client.download_blob().readall())
                
                contexts.append(Context(
                    context_id=entity['RowKey'],
                    type=entity['type'],
                    content=context_data['content'],
                    message_id=entity.get('message_id'),
                    project_id=entity['project_id'],
                    blob_name=entity['blob_name'],
                    name=entity.get('name')
                ))
                
            return contexts
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def get_contexts_by_message_id(self, message_id: str) -> List[Context]:
        try:
            filter_query = f"PartitionKey eq 'contexts' and message_id eq '{message_id}'"
            contexts = []
            
            for entity in self.contexts_table.query_entities(filter_query):
                blob_client = self.contexts_blob_container.get_blob_client(entity['blob_name'])
                context_data = json.loads(blob_client.download_blob().readall())
                
                contexts.append(Context(
                    context_id=entity['RowKey'],
                    type=entity['type'],
                    name=entity.get('name'),
                    content=context_data['content'],
                    message_id=entity['message_id'],
                    project_id=entity.get('project_id'),
                    blob_name=entity['blob_name']
                ))
                
            return contexts
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def delete_context(self, context_id: str):
        try:
            # get it first so we can delete the blob
            context = await self.get_context(context_id)
            self.contexts_table.delete_entity(partition_key="contexts", row_key=context_id)
            self.contexts_blob_container.delete_blob(context.blob_name)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def delete_contexts_by_message_id(self, message_id: str):
        try:
            filter_query = f"PartitionKey eq 'contexts' and message_id eq '{message_id}'"
            contexts = self.contexts_table.query_entities(filter_query)

            for context in contexts:
                context_id = context['RowKey']
                # Delete the context
                self.contexts_table.delete_entity(partition_key="contexts", row_key=context_id)

        except Exception as e:
            logger.error(f"Error deleting contexts for message {message_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
