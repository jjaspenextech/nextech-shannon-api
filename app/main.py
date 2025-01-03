from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controllers.jira_controller import router as jira_router
from controllers.users_controller import router as users_router
from controllers.conversations_controller import router as conversations_router
from controllers.account_controller import router as account_router
from controllers.llm_controller import router as llm_router
from controllers.web_controller import router as web_router
from controllers.project_controller import router as project_router
from utils.logger import logger
from config import Config
import json
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    # Angular allowed origins, controlled by azure deployment
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include the routers
app.include_router(jira_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(conversations_router, prefix="/api")
app.include_router(account_router, prefix="/api")
app.include_router(llm_router, prefix="/api")
app.include_router(web_router, prefix="/api")
app.include_router(project_router, prefix="/api")

@app.get("/")
async def root():
    logger.info("Health check endpoint called")
    # need to get print version of config
    return {"message": "Welcome to the Enterprise LLM Chat API. Config:" + Config.AZURE_STORAGE_ACCOUNT_NAME}