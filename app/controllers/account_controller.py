from fastapi import APIRouter, HTTPException, Body
from services.user_service import UserService

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

@router.post("/signup/")
async def signup(user_data: dict = Body(...)):
    try:
        username = user_data.get("username")
        password = user_data.get("password")
        email = user_data.get("email")
        first_name = user_data.get("firstName")
        last_name = user_data.get("lastName")
        
        user_service.signup_user(username, password, email, first_name, last_name)
        return {"message": "User created successfully"}
    except HTTPException as e:
        raise e 