from azure.data.tables import TableServiceClient, UpdateMode
from fastapi import HTTPException
from models import Project, Context, Conversation
from config import Config
import uuid
from typing import List
from services.context_service import ContextService
from services.conversation_service import ConversationService

class ProjectService:
    def __init__(self):
        connection_string = (
            f"DefaultEndpointsProtocol=https;"
            f"AccountName={Config.AZURE_STORAGE_ACCOUNT_NAME};"
            f"AccountKey={Config.AZURE_STORAGE_ACCOUNT_KEY};"
            f"EndpointSuffix={Config.AZURE_STORAGE_ENDPOINT_SUFFIX}"
        )
        self.table_service = TableServiceClient.from_connection_string(connection_string)
        self.projects_table = self.table_service.get_table_client(Config.AZURE_STORAGE_PROJECTS_TABLE_NAME)
        self.context_service = ContextService()
        self.conversation_service = ConversationService()

    def create_project_from_entity(self, entity: dict) -> Project:
        return Project(
            project_id=entity['RowKey'],
            name=entity['name'],
            description=entity.get('description', ''),
            username=entity.get('username'),
            is_public=entity.get('is_public', False)
        )

    async def create_project(self, project: Project) -> Project:
        project.project_id = str(uuid.uuid4())
        project_entity = {
            "PartitionKey": "projects",
            "RowKey": project.project_id,
            "name": project.name,
            "description": project.description,
            "username": project.username,
            "is_public": project.is_public
        }
        try:
            self.projects_table.create_entity(entity=project_entity)
            return project
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def get_project(self, project_id: str) -> Project:
        try:
            project_entity = self.projects_table.get_entity(partition_key="projects", row_key=project_id)            
            project_conversations = await self.conversation_service.get_conversations_by_project_id(project_id)
            project_contexts = await self.context_service.get_contexts_by_project_id(project_id)
            
            project = self.create_project_from_entity(project_entity)
            project.contexts = project_contexts
            project.conversations = project_conversations
            return project
        except Exception as e:
            raise HTTPException(status_code=404, detail="Project not found")

    async def update_project(self, project: Project) -> Project:
        try:
            project_entity = {
                "PartitionKey": "projects",
                "RowKey": project.project_id,
                "name": project.name,
                "description": project.description,
                "username": project.username,
                "is_public": project.is_public
            }
            self.projects_table.update_entity(entity=project_entity, mode=UpdateMode.MERGE)
            await self.update_project_contexts(project.project_id, project.contexts)
            await self.update_project_conversations(project.project_id, project.conversations)
            return project
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # save any new contexts using the context service
    async def update_project_contexts(self, project_id: str, contexts: List[Context]) -> List[Context]:
        try:
            existing_contexts = await self.context_service.get_contexts_by_project_id(project_id)
            for context in contexts:
                if context.context_id not in [existing_context.context_id for existing_context in existing_contexts]:
                    await self.context_service.save_context(context)
            for existing_context in existing_contexts:
                if existing_context.context_id not in [context.context_id for context in contexts]:
                    await self.context_service.delete_context(existing_context.context_id)
            return contexts
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def update_project_conversations(self, project_id: str, conversations: List[Conversation]) -> List[Conversation]:
        try:
            existing_conversations = await self.conversation_service.get_conversations_by_project_id(project_id)
            for conversation in conversations:
                if conversation.conversation_id not in [existing_conversation.conversation_id for existing_conversation in existing_conversations]:
                    await self.conversation_service.save_conversation(conversation)
            return conversations
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def delete_project(self, project_id: str):
        try:
            self.projects_table.delete_entity(partition_key="projects", row_key=project_id)
            await self.context_service.delete_contexts_by_project_id(project_id)
            await self.conversation_service.delete_conversations_by_project_id(project_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def list_projects(self) -> List[Project]:
        try:
            projects = self.projects_table.query_entities("PartitionKey eq 'projects'")
            return [self.create_project_from_entity(entity) for entity in projects]
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def list_user_projects(self, username: str) -> List[Project]:
        try:
            projects = self.projects_table.query_entities(f"PartitionKey eq 'projects' and username eq '{username}'")
            return [self.create_project_from_entity(entity) for entity in projects]
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def list_public_projects(self) -> List[Project]:
        try:
            projects = self.projects_table.query_entities("PartitionKey eq 'projects' and is_public eq true")
            return [self.create_project_from_entity(entity) for entity in projects]
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) 