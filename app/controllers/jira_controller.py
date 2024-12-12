from fastapi import APIRouter, HTTPException, Depends
from integrations.jira import JiraIntegration
from services.auth_service import verify_jwt_token, get_current_user
from models.chat import User

router = APIRouter()
jira_integration = JiraIntegration()

@router.get("/jira/story/{story_key}")
async def get_story_description(
    story_key: str, 
    current_user: User = Depends(get_current_user)
):
    try:
        description = jira_integration.get_story_description(story_key, current_user)
        return {"description": description}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))