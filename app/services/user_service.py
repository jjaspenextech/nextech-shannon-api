import jwt
import datetime
from azure.data.tables import TableServiceClient, UpdateMode
from config import Config
from models import User, Message, Conversation
from fastapi import HTTPException
from typing import List
from services.llm_service import query_llm  # Import the LLM query function
import json
from services.auth_service import AuthService
from fastapi import Depends
from utils.logger import logger
from azure.core.exceptions import ResourceNotFoundError

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
        self.signup_codes_table = self.table_service.get_table_client(Config.AZURE_STORAGE_SIGNUP_CODES_TABLE_NAME)

    def get_current_user(self, token_data: dict = Depends(AuthService.verify_jwt_token)):
        return self.get_user_info(token_data['username'])

    def login_user(self, username: str, password: str) -> dict:
        try:
            user_entity = self.users_table.get_entity(partition_key="users", row_key=username)
            user = User(
                username=user_entity["RowKey"],
                password=user_entity["password"],
                email=user_entity.get("email", ""),
                first_name=user_entity.get("first_name", ""),
                last_name=user_entity.get("last_name", ""),
                is_admin=user_entity.get("is_admin", False),
                api_keys=json.loads(user_entity.get('api_keys', '{}'))
            )
            
            if user and AuthService.verify_password(password, user.password):
                token = AuthService.create_jwt_token(user.username, user.is_admin)
                return {
                    "token": token,
                    "username": user.username,
                    "email": user.email,
                    "firstName": user.first_name,
                    "lastName": user.last_name
                }
            else:
                raise HTTPException(status_code=401, detail="Invalid credentials")
        except ResourceNotFoundError as e:
            raise HTTPException(status_code=401, detail="Invalid username")
        except Exception as e:
            logger.error(f"Error logging in user: {str(e)}")
            # also log exception type
            logger.error(f"Exception type: {type(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    def get_user_info(self, username: str) -> User:
        try:
            user_entity = self.users_table.get_entity(partition_key="users", row_key=username)
            api_keys = json.loads(user_entity.get('api_keys', '{}'))
            return User(
                username=user_entity["RowKey"],
                email=user_entity.get("email", ""),
                first_name=user_entity.get("first_name", ""),
                last_name=user_entity.get("last_name", ""),
                is_admin=user_entity.get("is_admin", False),
                api_keys=api_keys
            )
        except Exception as e:
            raise HTTPException(status_code=404, detail="User not found")

    def create_user(self, username: str, password: str, email: str, first_name: str, last_name: str):
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
                "password": AuthService.hash_password(password),
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "api_keys": json.dumps({}),
                "is_admin": False
            }
            self.users_table.create_entity(entity=user_entity)
            user = User(
                username=user_entity.get("RowKey"),
                password=user_entity.get("password"),
                email=user_entity.get("email"),
                first_name=user_entity.get("first_name"),
                last_name=user_entity.get("last_name"),
                is_admin=user_entity.get("is_admin", False),
                api_keys=json.loads(user_entity.get('api_keys', '{}'))
            )
            return user

    async def get_user_token(self, user: User):
        # Fetch the user's admin status from the database or user object
        is_admin = user.is_admin or False

        token = AuthService.create_jwt_token(user.username, is_admin)
        return {
            "token": token,
            "username": user.username,
            "email": user.email,
            "firstName": user.first_name,
            "lastName": user.last_name
        }

    async def save_conversation(self, conversation: Conversation):
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

    def update_api_key(self, username: str, service: str, key: str) -> dict:
        try:
            user_entity = self.users_table.get_entity(partition_key="users", row_key=username)
            
            # Initialize or update api_keys
            api_keys = json.loads(user_entity.get('api_keys', '{}'))
            api_keys[service] = key
            
            # Update the entity
            user_entity['api_keys'] = json.dumps(api_keys)
            self.users_table.update_entity(entity=user_entity, mode=UpdateMode.MERGE)
            
            return {"message": f"{service} API key updated successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def get_api_keys(self, username: str) -> dict:
        try:
            user_entity = self.users_table.get_entity(partition_key="users", row_key=username)
            api_keys = json.loads(user_entity.get('api_keys', '{}'))
            return api_keys
        except Exception as e:
            raise HTTPException(status_code=404, detail="User not found") 

    def validate_signup_code(self, code: str) -> bool:
        try:
            connection_string = (
                f"DefaultEndpointsProtocol=https;"
                f"AccountName={Config.AZURE_STORAGE_ACCOUNT_NAME};"
                f"AccountKey={Config.AZURE_STORAGE_ACCOUNT_KEY};"
                f"EndpointSuffix={Config.AZURE_STORAGE_ENDPOINT_SUFFIX}"
            )
            logger.info(f"Connection string: {connection_string}")
            logger.info(f"Validating signup code: {code}")
            signup_code_entity = self.signup_codes_table.get_entity(partition_key="signupCodes", row_key=code)
            return True
        except Exception as e:
            logger.error(f"Error validating signup code: {str(e)}")
            return False

    def update_user_theme(self, username: str, theme: str) -> dict:
        try:
            user_entity = self.users_table.get_entity(partition_key="users", row_key=username)
            
            # Update the theme
            user_entity['theme'] = theme
            
            # Update the entity
            self.users_table.update_entity(entity=user_entity, mode=UpdateMode.MERGE)
            
            return {"message": "Theme updated successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
