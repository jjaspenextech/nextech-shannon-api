import os
from dotenv import load_dotenv

load_dotenv('.local.env', override=True)

class Config:
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_URL = os.getenv("AZURE_OPENAI_URL")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_EASTUS2_API_VERSION", "2024-02-15-preview")
    AZURE_OPENAI_MODEL = os.getenv("AZURE_OPENAI_MODEL", "gpt-4o")
    AZURE_STORAGE_ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    AZURE_STORAGE_ACCOUNT_KEY = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
    AZURE_STORAGE_ENDPOINT_SUFFIX = "core.windows.net"
    AZURE_STORAGE_USERS_TABLE_NAME = "users"
    AZURE_STORAGE_PROJECTS_TABLE_NAME = "projects"
    AZURE_STORAGE_MESSAGES_TABLE_NAME = "messages"
    AZURE_STORAGE_CONTEXTS_TABLE_NAME = "contexts"
    AZURE_STORAGE_CONTEXTS_BLOB_CONTAINER = "contexts"
    AZURE_STORAGE_CONVERSATIONS_TABLE_NAME = "conversations"
    AZURE_STORAGE_SIGNUP_CODES_TABLE_NAME = "signupCodes"
    SECRET_KEY = os.getenv("SECRET_KEY")
    TOKEN_DURATION = os.getenv("TOKEN_DURATION")

    @classmethod
    def serialize(cls):
        return {key: value for key, value in cls.__dict__.items() if not key.startswith('__') and not callable(value)}

