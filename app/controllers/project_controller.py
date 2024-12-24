from fastapi import APIRouter, HTTPException, Depends
from models import Project
from services import ProjectService, ConversationService, AuthService
from datetime import datetime
from utils.logger import logger

router = APIRouter()
project_service = ProjectService()
conversation_service = ConversationService()

@router.post("/project/")
async def create_project(project: Project, token_data: dict = Depends(AuthService.verify_jwt_token)):
    try:
        project.username = project.username if project.username else token_data.get("username")
        return await project_service.create_project(project)
    except HTTPException as e:
        raise e

@router.get("/project/{project_id}")
async def get_project(project_id: str, token_data: dict = Depends(AuthService.verify_jwt_token)):
    try:
        return await project_service.get_project(project_id)
    except HTTPException as e:
        raise e

@router.put("/project/")
async def update_project(project: Project, token_data: dict = Depends(AuthService.verify_jwt_token)):
    try:
        return await project_service.update_project(project)
    except HTTPException as e:
        raise e

@router.delete("/project/{project_id}")
async def delete_project(project_id: str, token_data: dict = Depends(AuthService.verify_jwt_token)):
    try:
        await project_service.delete_project(project_id)
        return {"message": "Project deleted successfully"}
    except HTTPException as e:
        raise e

@router.get("/projects/")
async def list_projects(token_data: dict = Depends(AuthService.verify_jwt_token)):
    try:
        return await project_service.list_projects()
    except HTTPException as e:
        raise e

@router.get("/projects/user/")
async def list_user_projects(token_data: dict = Depends(AuthService.verify_jwt_token)):
    try:
        username = token_data.get("username")
        return await project_service.list_user_projects(username)
    except HTTPException as e:
        raise e

@router.get("/projects/public/")
async def list_public_projects(token_data: dict = Depends(AuthService.verify_jwt_token)):
    try:
        return await project_service.list_public_projects()
    except HTTPException as e:
        raise e

@router.get("/projects/{project_id}/conversations")
async def get_project_conversations(
    project_id: str,
    token_data: dict = Depends(AuthService.verify_jwt_token)
):
    try:
        return await conversation_service.get_conversations_by_project_id(project_id, include_messages=True)
    except Exception as e:
        logger.error(f"Error getting conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 


@router.get("/projects/{project_id}/conversation-summaries")
async def get_project_conversations(
    project_id: str,
    token_data: dict = Depends(AuthService.verify_jwt_token)
):
    try:
        return await conversation_service.get_conversations_by_project_id(project_id, include_messages=False)
    except Exception as e:
        logger.error(f"Error getting conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 

@router.delete("/projects/")
async def delete_projects(
    username: str = None,  # Query parameter
    token_data: dict = Depends(AuthService.verify_jwt_token)
):
    try:
        # Check if the user is an admin
        if not token_data.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Not authorized to delete projects")

        # Use the provided username or fallback to the token's username
        target_username = username or token_data.get("username")
        
        await project_service.delete_user_projects(target_username)
        return {"message": f"Projects for {target_username} deleted successfully"}
    except HTTPException as e:
        logger.error(f"Error deleting projects: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error deleting projects: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error") 