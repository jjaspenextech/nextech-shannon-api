from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controllers.jira_controller import router as jira_router
from controllers.users_controller import router as users_router
from controllers.conversations_controller import router as conversations_router
from controllers.account_controller import router as account_router
from controllers.llm_controller import router as llm_router
from utils.logger import setup_logger

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Angular dev server
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

@app.get("/")
async def root():
    logger.info("Health check endpoint called")
    return {"message": "Welcome to the Enterprise LLM Chat API"}