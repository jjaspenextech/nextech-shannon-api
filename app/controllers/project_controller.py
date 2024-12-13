from fastapi import APIRouter, HTTPException, Depends
from models.project import Project
from services.project_service import ProjectService
from services.auth_service import verify_jwt_token

router = APIRouter()
project_service = ProjectService()

@router.post("/project/")
async def create_project(project: Project, token_data: dict = Depends(verify_jwt_token)):
    try:
        return await project_service.create_project(project)
    except HTTPException as e:
        raise e

@router.get("/project/{project_id}")
async def get_project(project_id: str, token_data: dict = Depends(verify_jwt_token)):
    try:
        return await project_service.get_project(project_id)
    except HTTPException as e:
        raise e

@router.put("/project/")
async def update_project(project: Project, token_data: dict = Depends(verify_jwt_token)):
    try:
        return await project_service.update_project(project)
    except HTTPException as e:
        raise e

@router.delete("/project/{project_id}")
async def delete_project(project_id: str, token_data: dict = Depends(verify_jwt_token)):
    try:
        await project_service.delete_project(project_id)
        return {"message": "Project deleted successfully"}
    except HTTPException as e:
        raise e

@router.get("/projects/")
async def list_projects(token_data: dict = Depends(verify_jwt_token)):
    try:
        return await project_service.list_projects()
    except HTTPException as e:
        raise e

@router.get("/projects/user/")
async def list_user_projects(token_data: dict = Depends(verify_jwt_token)):
    try:
        username = token_data.get("username")
        return await project_service.list_user_projects(username)
    except HTTPException as e:
        raise e

@router.get("/projects/public/")
async def list_public_projects(token_data: dict = Depends(verify_jwt_token)):
    try:
        return await project_service.list_public_projects()
    except HTTPException as e:
        raise e 