import jwt
import datetime
from azure.data.tables import TableServiceClient
from app.config import Config
from app.models.chat import User
from fastapi import HTTPException

class UserService:
    def __init__(self):
        self.table_service = TableServiceClient.from_connection_string(Config.AZURE_STORAGE_CONNECTION_STRING)
        self.users_table = self.table_service.get_table_client(Config.AZURE_STORAGE_USERS_TABLE_NAME)
        self.secret_key = "your_secret_key"  # Replace with a secure key

    def create_jwt_token(self, user_id: str) -> str:
        payload = {
            "user_id": user_id,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def login_user(self, username: str, password: str) -> str:
        try:
            user_entity = self.users_table.get_entity(partition_key="user", row_key=username)
            user = User(username=user_entity["username"], password=user_entity["password"], api_keys={})
            if user and user.password == password:  # Ensure password is hashed in production
                return self.create_jwt_token(user.username)
            else:
                raise HTTPException(status_code=401, detail="Invalid credentials")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def get_user_info(self, user_id: str):
        try:
            user_entity = self.users_table.get_entity(partition_key="user", row_key=user_id)
            user = User(username=user_entity["username"], password=user_entity["password"], api_keys={})
            return {"user_id": user.username, "username": user.username}
        except Exception as e:
            raise HTTPException(status_code=404, detail="User not found") 