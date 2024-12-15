import os
from dotenv import load_dotenv

load_dotenv('.local.env', override=True)

class Config:
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_EASTUS2_API_KEY")
    AZURE_OPENAI_URL = os.getenv("AZURE_OPENAI_EASTUS2_URL")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_EASTUS2_API_VERSION", "2024-02-15-preview")
    AZURE_OPENAI_MODEL = os.getenv("AZURE_OPENAI_EASTUS2_MODEL", "gpt-4o")
    AZURE_SUBSCRIPTION_ID = os.getenv("PERSONAL_AZURE_SUBSCRIPTION_ID")
    AZURE_RESOURCE_GROUP = "nextech-shannon-rg"
    AZURE_STORAGE_ACCOUNT_NAME = "shannonstorage"
    AZURE_STORAGE_ACCOUNT_KEY = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
    AZURE_STORAGE_ENDPOINT_SUFFIX = "core.windows.net"
    AZURE_STORAGE_USERS_TABLE_NAME = "users"
    AZURE_STORAGE_PROJECTS_TABLE_NAME = "projects"
    AZURE_STORAGE_MESSAGES_TABLE_NAME = "messages"
    AZURE_STORAGE_CONTEXTS_TABLE_NAME = "contexts"
    AZURE_STORAGE_CONTEXTS_BLOB_CONTAINER = "contexts"
    AZURE_STORAGE_CONVERSATIONS_TABLE_NAME = "conversations"
