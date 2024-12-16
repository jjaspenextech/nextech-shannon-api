from fastapi import APIRouter, HTTPException, Depends
from integrations.jira import JiraIntegration
from models.chat import User
from services.user_service import UserService

router = APIRouter()
jira_integration = JiraIntegration()
user_service = UserService()

@router.get("/jira/story/{story_key}")
async def get_story_description(
    story_key: str, 
    current_user: User = Depends(user_service.get_current_user)
):
    try:
        description = jira_integration.get_story_description(story_key, current_user)
        return {"description": description}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))