from fastapi import APIRouter, HTTPException, Depends
from models.chat import Conversation
from services.conversation_service import ConversationService
from services.auth_service import verify_jwt_token

router = APIRouter()

@router.post("/save-conversation/")
async def save_conversation(conversation: Conversation, token_data: dict = Depends(verify_jwt_token)):
    try:
        conversation_service = ConversationService()
        await conversation_service.save_conversation(conversation)
        return {"message": "Conversation and messages saved successfully"}
    except HTTPException as e:
        raise e

@router.get("/get-conversation/{conversation_id}")
async def get_conversation(conversation_id: str, token_data: dict = Depends(verify_jwt_token)):
    try:
        conversation_service = ConversationService()
        messages = await conversation_service.get_conversation(conversation_id)
        return {"messages": messages}
    except HTTPException as e:
        raise e 