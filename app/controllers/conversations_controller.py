from fastapi import APIRouter, HTTPException, Depends
from models import Conversation
from services import ConversationService, AuthService, ProjectService
from utils.logger import logger
from datetime import datetime

router = APIRouter()

@router.post("/conversation/")
async def save_conversation(conversation: Conversation, token_data: dict = Depends(AuthService.verify_jwt_token)):
    try:
        logger.info(f"Saving conversation: {conversation}")
        conversation_service = ConversationService()
        project_service = ProjectService()
        saved_conversation = await conversation_service.save_conversation(conversation)
        logger.info(f"Saved conversation: {saved_conversation}")

        # update the project's updated_at field with the current timestamp
        if conversation.project_id is not None and conversation.project_id != "":
            project = await project_service.get_project(conversation.project_id)
            project.updated_at = datetime.now().isoformat()
            await project_service.update_project(project)
            logger.info(f"Updated project: {project}")

        return {"message": "Conversation and messages saved successfully", "conversation": saved_conversation}
    except HTTPException as e:
        logger.error(f"Error saving conversation: {e}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error saving conversation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str, token_data: dict = Depends(AuthService.verify_jwt_token)):
    try:
        conversation_service = ConversationService()
        conversation = await conversation_service.get_conversation(conversation_id)
        # logger.info(f"Retrieved conversation: {conversation}")
        return conversation
    except HTTPException as e:
        raise e 
    except Exception as e:
        logger.error(f"Unexpected error retrieving conversation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/conversations/{username}")
async def get_conversations(username: str, token_data: dict = Depends(AuthService.verify_jwt_token)):
    try:
        conversation_service = ConversationService()
        # Optional: Verify that the requesting user matches the username
        if token_data.get("username") != username:
            raise HTTPException(status_code=403, detail="Not authorized to access these conversations")
            
        conversations = await conversation_service.get_conversations_by_username(username)
        # logger.info(f"Retrieved conversations: {conversations}")
        return conversations
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error retrieving conversations: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/conversations/")
async def delete_conversations(
    username: str = None,  # Query parameter
    token_data: dict = Depends(AuthService.verify_jwt_token)
):
    try:
        # Check if the user is an admin
        if not token_data.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Not authorized to delete conversations")

        # Use the provided username or fallback to the token's username
        target_username = username or token_data.get("username")
        
        await conversation_service.delete_user_conversations(target_username)
        return {"message": f"Conversations for {target_username} deleted successfully"}
    except HTTPException as e:
        logger.error(f"Error deleting conversations: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error deleting conversations: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
