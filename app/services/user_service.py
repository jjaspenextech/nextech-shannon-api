import jwt
import datetime
from azure.data.tables import TableServiceClient
from config import Config
from models.chat import User, Message, Conversation
from fastapi import HTTPException
import bcrypt
from typing import List
from services.llm_service import query_llm  # Import the LLM query function
import json

class UserService:
    def __init__(self):
        connection_string = (
            f"DefaultEndpointsProtocol=https;"
            f"AccountName={Config.AZURE_STORAGE_ACCOUNT_NAME};"
            f"AccountKey={Config.AZURE_STORAGE_ACCOUNT_KEY};"
            f"EndpointSuffix={Config.AZURE_STORAGE_ENDPOINT_SUFFIX}"
        )
        self.table_service = TableServiceClient.from_connection_string(connection_string)
        self.users_table = self.table_service.get_table_client(Config.AZURE_STORAGE_USERS_TABLE_NAME)
        self.secret_key = "your_secret_key"  # Replace with a secure key

    def create_jwt_token(self, username: str) -> str:
        payload = {
            "username": username,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

    def login_user(self, username: str, password: str) -> dict:
        try:
            user_entity = self.users_table.get_entity(partition_key="users", row_key=username)
            user = User(
                username=user_entity["RowKey"],
                password=user_entity["password"],
                email=user_entity.get("email", ""),
                first_name=user_entity.get("first_name", ""),
                last_name=user_entity.get("last_name", ""),
                api_keys={}
            )
            
            if user and self.verify_password(password, user.password):
                token = self.create_jwt_token(user.username)
                return {
                    "token": token,
                    "username": user.username,
                    "email": user.email,
                    "firstName": user.first_name,
                    "lastName": user.last_name
                }
            else:
                raise HTTPException(status_code=401, detail="Invalid credentials")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def get_user_info(self, username: str) -> dict:
        try:
            user_entity = self.users_table.get_entity(partition_key="users", row_key=username)
            return {
                "username": user_entity["RowKey"],
                "email": user_entity.get("email", ""),
                "firstName": user_entity.get("first_name", ""),
                "lastName": user_entity.get("last_name", "")
            }
        except Exception as e:
            raise HTTPException(status_code=404, detail="User not found")

    def create_user(self, username: str, password: str):
        hashed_password = self.hash_password(password)
        user = User(username=username, password=hashed_password, api_keys={})
        self.users_table.create_entity(entity=user.dict()) 

    def signup_user(self, username: str, password: str, email: str, first_name: str, last_name: str):
        try:
            # Check if the user already exists
            existing_user = self.users_table.get_entity(partition_key="users", row_key=username)
            if existing_user:
                raise HTTPException(status_code=400, detail="User already exists")
        except Exception:
            # Create a new user entity
            user_entity = {
                "PartitionKey": "users",
                "RowKey": username,
                "password": self.hash_password(password),
                "email": email,
                "first_name": first_name,
                "last_name": last_name
            }
            # Insert the user into Azure Table Storage
            self.users_table.create_entity(entity=user_entity) 

    async def save_conversation(self, conversation: Conversation):
        # Check if the conversation is new
        if len(conversation.messages) == 1:
            # Generate a description using the LLM
            first_message = conversation.messages[0].content
            conversation.description = await query_llm(first_message)

        conversation_entity = {
            "PartitionKey": "conversations",
            "RowKey": conversation.conversation_id,
            "username": conversation.username,
            "description": conversation.description,
            "messages": json.dumps([msg.dict() for msg in conversation.messages])
        }

        try:
            # Try to get the existing conversation
            existing_entity = self.users_table.get_entity(partition_key="conversations", row_key=conversation.conversation_id)
            # If it exists, update it
            self.users_table.update_entity(entity=conversation_entity, mode='Merge')
        except Exception as e:
            # If it doesn't exist, create a new one
            if "EntityNotFound" in str(e):
                self.users_table.create_entity(entity=conversation_entity)
            else:
                raise HTTPException(status_code=500, detail=str(e))

    def get_conversation(self, conversation_id: str) -> List[Message]:
        try:
            conversation_entity = self.users_table.get_entity(partition_key="conversations", row_key=conversation_id)
            messages_json = conversation_entity["messages"]
            messages = json.loads(messages_json)
            return [Message(**msg) for msg in messages]
        except Exception as e:
            raise HTTPException(status_code=404, detail="Conversation not found") 