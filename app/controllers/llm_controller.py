from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from models.chat import ChatRequest, ChatResponse
from services.llm_service import chat_with_llm_stream, query_llm
from services import AuthService, ProjectService, ContextService
from utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)

@router.post("/llm-query/", response_model=ChatResponse)
async def llm_query(request: ChatRequest, token_data: dict = Depends(AuthService.verify_jwt_token)):
    logger.info(f"Received chat request")
    try:
        response = await query_llm(request.prompt)
        logger.info("Successfully processed chat request")
        return ChatResponse(response=response)
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/llm-query/stream/")
async def llm_query_stream(request: ChatRequest, token_data: dict = Depends(AuthService.verify_jwt_token)):
    logger.info(f"Received streaming chat request")
    context_service = ContextService()
    try:
        # Get project contexts if project_id is provided
        project_contexts = []
        if request.project_id:
            project_contexts = await context_service.get_contexts_by_project_id(request.project_id)

        async def event_generator():
            async for token in chat_with_llm_stream(request.messages, project_contexts):
                yield f"{token}"
            yield "[DONE]"
            
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream"
        )
    except Exception as e:
        logger.error(f"Error processing streaming chat request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 