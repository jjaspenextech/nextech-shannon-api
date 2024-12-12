from fastapi import APIRouter, HTTPException, Depends
from integrations.jira import JiraIntegration
from services.auth_service import verify_jwt_token

router = APIRouter()
jira_integration = JiraIntegration()

@router.get("/jira/story/{story_key}")
async def get_story_description(story_key: str, token_data: dict = Depends(verify_jwt_token)):
    try:
        description = jira_integration.get_story_description(story_key)
        return {"description": description}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))