from fastapi import APIRouter, HTTPException, Body, status
from services.user_service import UserService
from models.chat import SignupRequest
from utils.logger import logger

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
        signup_code = user_data.get("signupCode")

        # Validate signup code first
        if not user_service.validate_signup_code(signup_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signup code"
            )
        
        # If code is valid, proceed with user creation
        logger.info(f"Creating user: {user_data}")
        user = user_service.create_user(
            user_data.get("username"),
            user_data.get("password"),
            user_data.get("email"),
            user_data.get("firstName"),
            user_data.get("lastName")
        )
        token = await user_service.get_user_token(user)
        return token
    except HTTPException as e:
        raise e 