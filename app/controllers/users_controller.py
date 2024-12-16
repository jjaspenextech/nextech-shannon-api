from fastapi import APIRouter, HTTPException, Depends, Body
from services.user_service import UserService
from models.chat import ApiKeyUpdate
from services.auth_service import AuthService

router = APIRouter()
user_service = UserService()

@router.post("/login/")
async def login(credentials: dict = Body(...)):
    try:
        username = credentials.get("username")
        password = credentials.get("password")
        
        user_data = user_service.login_user(username, password)
        return user_data
    except HTTPException as e:
        raise e

@router.get("/user-info/")
async def get_user_info(token_data: dict = Depends(AuthService.verify_jwt_token)):
    try:
        username = token_data.get("username")
        user_info = user_service.get_user_info(username)
        return user_info
    except HTTPException as e:
        raise e

@router.post("/api-keys/update")
async def update_api_key(key_update: ApiKeyUpdate, token_data: dict = Depends(AuthService.verify_jwt_token)):
    try:
        username = token_data.get("username")
        return user_service.update_api_key(username, key_update.service, key_update.key)
    except HTTPException as e:
        raise e

@router.get("/api-keys")
async def get_api_keys(token_data: dict = Depends(AuthService.verify_jwt_token)):
    try:
        username = token_data.get("username")
        return user_service.get_api_keys(username)
    except HTTPException as e:
        raise e 