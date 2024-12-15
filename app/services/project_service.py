from azure.data.tables import TableServiceClient
from fastapi import HTTPException
from models.project import Project
from config import Config
import uuid
from typing import List
from services.context_service import ContextService

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
            
            return Project(
                project_id=project_entity['RowKey'],
                name=project_entity['name'],
                description=project_entity.get('description', ''),
                username=project_entity.get('username'),
                is_public=project_entity.get('is_public', False),
                contexts=project_contexts,
                conversations=project_conversations
            )
        except Exception as e:
            raise HTTPException(status_code=404, detail="Project not found")

    async def update_project(self, project: Project) -> Project:
        try:
            project_entity = {
                "PartitionKey": "projects",
                "RowKey": project.project_id,
                "name": project.name,
                "description": project.description,
                "contexts": [context.dict() for context in project.contexts],
                "conversations": project.conversations,
                "username": project.username,
                "is_public": project.is_public
            }
            self.projects_table.update_entity(entity=project_entity, mode='Merge')
            return project
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def delete_project(self, project_id: str):
        try:
            self.projects_table.delete_entity(partition_key="projects", row_key=project_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def list_projects(self) -> List[Project]:
        try:
            projects = self.projects_table.query_entities("PartitionKey eq 'projects'")
            return [Project(
                project_id=entity['RowKey'],
                name=entity['name'],
                description=entity.get('description', ''),
                username=entity.get('username'),
                is_public=entity.get('is_public', False)
            ) for entity in projects]
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def list_user_projects(self, username: str) -> List[Project]:
        try:
            projects = self.projects_table.query_entities(f"PartitionKey eq 'projects' and username eq '{username}'")
            return [Project(
                project_id=entity['RowKey'],
                name=entity['name'],
                description=entity.get('description', ''),
                contexts=entity.get('contexts', []),
                conversations=entity.get('conversations', []),
                username=entity.get('username'),
                is_public=entity.get('is_public', False)
            ) for entity in projects]
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def list_public_projects(self) -> List[Project]:
        try:
            projects = self.projects_table.query_entities("PartitionKey eq 'projects' and is_public eq true")
            return [Project(
                project_id=entity['RowKey'],
                name=entity['name'],
                description=entity.get('description', ''),
                contexts=entity.get('contexts', []),
                conversations=entity.get('conversations', []),
                username=entity.get('username'),
                is_public=entity.get('is_public', False)
            ) for entity in projects]
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) 