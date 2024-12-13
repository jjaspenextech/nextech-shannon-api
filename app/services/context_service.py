from azure.storage.blob import BlobServiceClient
from fastapi import HTTPException
from models.context import Context
from config import Config
import json
import uuid

class ContextService:
    def __init__(self):
        connection_string = (
            f"DefaultEndpointsProtocol=https;"
            f"AccountName={Config.AZURE_STORAGE_ACCOUNT_NAME};"
            f"AccountKey={Config.AZURE_STORAGE_ACCOUNT_KEY};"
            f"EndpointSuffix={Config.AZURE_STORAGE_ENDPOINT_SUFFIX}"
        )
        self.contexts_blob_service = BlobServiceClient.from_connection_string(connection_string)
        self.contexts_blob_container = self.contexts_blob_service.get_container_client(Config.AZURE_STORAGE_CONTEXTS_BLOB_CONTAINER)

    async def save_context(self, context: Context, parent_id: str) -> str:
        file_name_guid = str(uuid.uuid4())
        blob_name = f"{parent_id}/{file_name_guid}.json"
        blob_client = self.contexts_blob_container.get_blob_client(blob_name)
        try:
            blob_client.upload_blob(json.dumps(context.dict()))
            return blob_name
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error saving context: {str(e)}")

    async def get_context(self, parent_id: str, context_name: str) -> Context:
        blob_client = self.contexts_blob_container.get_blob_client(context_name)
        try:
            context_data = blob_client.download_blob().readall()
            return Context(**json.loads(context_data))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving context: {str(e)}")
