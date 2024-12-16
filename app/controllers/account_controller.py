from fastapi import APIRouter, HTTPException, Body, status
from services.user_service import UserService
from models.chat import SignupRequest

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
async def signup(user_data: SignupRequest):
    try:
        # Validate signup code first
        if not user_service.validate_signup_code(user_data.signup_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signup code"
            )
        
        # If code is valid, proceed with user creation
        user_service.signup_user(
            user_data.username,
            user_data.password,
            user_data.email,
            user_data.first_name,
            user_data.last_name
        )
        return {"message": "User created successfully"}
    except HTTPException as e:
        raise e 