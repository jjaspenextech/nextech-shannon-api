import jwt
from fastapi import HTTPException, Header, Depends
from services.user_service import UserService
from models.chat import User

user_service = UserService()

def verify_jwt_token(authorization: str = Header(...)):
    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, user_service.secret_key, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token") 

def get_current_user(token_data: dict = Depends(verify_jwt_token)):
    return user_service.get_user_info(token_data['username'])
