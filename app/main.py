from fastapi import FastAPI, HTTPException, Depends, Header, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from services.llm_service import chat_with_llm_stream
from services.user_service import UserService
from services.conversation_service import ConversationService
from models.chat import ChatRequest, ChatResponse, Conversation
from utils.logger import setup_logger
import jwt

logger = setup_logger(__name__)
user_service = UserService()
conversation_service = ConversationService()

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
            async for token in chat_with_llm_stream(request.messages):
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
        
        user_data = user_service.login_user(username, password)
        return user_data
    except HTTPException as e:
        raise e

@app.get("/user-info/")
async def get_user_info(token_data: dict = Depends(verify_jwt_token)):
    try:
        username = token_data.get("username")
        user_info = user_service.get_user_info(username)
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

@app.post("/save-conversation/")
async def save_conversation(conversation: Conversation, token_data: dict = Depends(verify_jwt_token)):
    try:
        await conversation_service.save_conversation(conversation)
        return {"message": "Conversation saved successfully"}
    except HTTPException as e:
        raise e

@app.get("/get-conversation/{conversation_id}")
async def get_conversation(conversation_id: str, token_data: dict = Depends(verify_jwt_token)):
    try:
        messages = conversation_service.get_conversation(conversation_id)
        return {"messages": messages}
    except HTTPException as e:
        raise e

@app.get("/conversations/{username}")
async def get_conversations(username: str, token_data: dict = Depends(verify_jwt_token)):
    try:
        # Optional: Verify that the requesting user matches the username
        if token_data.get("username") != username:
            raise HTTPException(status_code=403, detail="Not authorized to access these conversations")
            
        conversations = conversation_service.get_conversations_by_username(username)
        return conversations
    except HTTPException as e:
        raise e