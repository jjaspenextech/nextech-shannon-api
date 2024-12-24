import jwt
from fastapi import HTTPException, Header, Depends
from config import Config
import bcrypt
import datetime

class AuthService:
    secret_key = Config.SECRET_KEY
    token_duration = int(Config.TOKEN_DURATION) if Config.TOKEN_DURATION else 1

    @classmethod
    def verify_jwt_token(cls, authorization: str = Header(...)):
        try:
            token = authorization.split(" ")[1]
            payload = jwt.decode(token, cls.secret_key, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token") 

    @classmethod
    def create_jwt_token(cls, username: str, is_admin: bool) -> str:
        payload = {
            "username": username,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=cls.token_duration * 24),
            "is_admin": is_admin,
            # Add other claims as needed
        }
        return jwt.encode(payload, cls.secret_key, algorithm="HS256")
        return token

    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))