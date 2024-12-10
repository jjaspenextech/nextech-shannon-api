from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from app.services.llm_service import query_llm_stream
from app.models.chat import ChatRequest, ChatResponse
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Angular dev server
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/")
async def root():
    logger.info("Health check endpoint called")
    return {"message": "Welcome to the Enterprise LLM Chat API"}

@app.post("/llm-query/", response_model=ChatResponse)
async def llm_query(request: ChatRequest):
    logger.info(f"Received chat request")
    try:
        response = await query_llm(request.prompt)
        logger.info("Successfully processed chat request")
        return ChatResponse(response=response)
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/llm-query/stream/")
async def llm_query_stream(request: ChatRequest):
    logger.info(f"Received streaming chat request")
    try:
        async def event_generator():
            async for token in query_llm_stream(request.messages):
                yield f"data: {token}\n\n"
            yield "data: [DONE]\n\n"
            
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