from fastapi import FastAPI, HTTPException, Depends, Header, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from services.llm_service import query_llm_stream
from services.user_service import UserService
from models.chat import ChatRequest, ChatResponse
from utils.logger import setup_logger
import jwt

logger = setup_logger(__name__)
user_service = UserService()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Angular dev server
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

def verify_jwt_token(authorization: str = Header(...)):
    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, user_service.secret_key, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/")
async def root():
    logger.info("Health check endpoint called")
    return {"message": "Welcome to the Enterprise LLM Chat API"}

@app.post("/llm-query/", response_model=ChatResponse)
async def llm_query(request: ChatRequest, token_data: dict = Depends(verify_jwt_token)):
    logger.info(f"Received chat request")
    try:
        response = await query_llm(request.prompt)
        logger.info("Successfully processed chat request")
        return ChatResponse(response=response)
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/llm-query/stream/")
async def llm_query_stream(request: ChatRequest, token_data: dict = Depends(verify_jwt_token)):
    logger.info(f"Received streaming chat request")
    try:
        async def event_generator():
            async for token in query_llm_stream(request.messages):
                yield f"{token}"
            yield "[DONE]"
            
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream"
        )
    except Exception as e:
        logger.error(f"Error processing streaming chat request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    logger.info("API Server starting up")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("API Server shutting down")

@app.post("/login/")
async def login(credentials: dict = Body(...)):
    try:
        username = credentials.get("username")
        password = credentials.get("password")
        
        token = user_service.login_user(username, password)
        return {"token": token}
    except HTTPException as e:
        raise e

@app.get("/user-info/")
async def get_user_info(user_id: str):
    try:
        user_info = user_service.get_user_info(user_id)
        return user_info
    except HTTPException as e:
        raise e

@app.post("/signup/")
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