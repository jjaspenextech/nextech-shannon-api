from fastapi import APIRouter, HTTPException, Depends
from services.conversation_service import ConversationService
from models.chat import Conversation
from services.auth_service import verify_jwt_token

router = APIRouter()
conversation_service = ConversationService()

@router.post("/save-conversation/")
async def save_conversation(conversation: Conversation, token_data: dict = Depends(verify_jwt_token)):
    try:
        await conversation_service.save_conversation(conversation)
        return {"message": "Conversation saved successfully"}
    except HTTPException as e:
        raise e

@router.get("/get-conversation/{conversation_id}")
async def get_conversation(conversation_id: str, token_data: dict = Depends(verify_jwt_token)):
    try:
        messages = conversation_service.get_conversation(conversation_id)
        return {"messages": messages}
    except HTTPException as e:
        raise e

@router.get("/conversations/{username}")
async def get_conversations(username: str, token_data: dict = Depends(verify_jwt_token)):
    try:
        # Optional: Verify that the requesting user matches the username
        if token_data.get("username") != username:
            raise HTTPException(status_code=403, detail="Not authorized to access these conversations")
            
        conversations = conversation_service.get_conversations_by_username(username)
        return conversations
    except HTTPException as e:
        raise e 