from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from models.chat import ChatRequest, ChatResponse, DescriptionRequest
from services.llm_service import chat_with_llm_stream, query_llm, generate_description
from services import AuthService, ProjectService, ContextService
from utils.logger import logger

router = APIRouter()
context_service = ContextService()
project_service = ProjectService()

async def get_project_contexts(project_id: str):
    project_contexts = await context_service.get_contexts_by_project_id(project_id)
    project = await project_service.get_project(project_id)
    project_contexts.append({
        "type": "project_description",
        "content": project.description,
        "name": project.name,
        "project_id": project.project_id
    })

@router.post("/llm-query/", response_model=ChatResponse)
async def llm_query(request: ChatRequest, token_data: dict = Depends(AuthService.verify_jwt_token)):
    logger.info(f"Received chat request")
    try:
        response = await query_llm(request.prompt)
        logger.info("Successfully processed chat request")
        return ChatResponse(response=response)
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/llm-query/stream/")
async def llm_query_stream(request: ChatRequest, token_data: dict = Depends(AuthService.verify_jwt_token)):
    logger.info(f"Received streaming chat request")
    try:
        project_contexts = await get_project_contexts(request.project_id) if request.project_id else []

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
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/llm-query/description")
async def llm_generate_description(request: DescriptionRequest, token_data: dict = Depends(AuthService.verify_jwt_token)):
    logger.info(f"Received request to generate description")
    try:
        description = await generate_description(request.prompt)
        logger.info("Successfully generated description")
        return {"description": description}
    except Exception as e:
        logger.error(f"Error generating description: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error") 