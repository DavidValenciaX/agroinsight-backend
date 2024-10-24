from sqlalchemy.orm import Session
from app.cultural_practices.domain.schemas import TaskTypeListResponse
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository 
from app.infrastructure.mappers.response_mappers import map_task_type_to_response
from app.user.domain.schemas import UserInDB

class ListTaskTypesUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.cultural_practice_repository = CulturalPracticesRepository(db)

    def list_task_types(self, current_user: UserInDB) -> TaskTypeListResponse:
        task_types = self.cultural_practice_repository.get_task_types()
        task_type_responses = [map_task_type_to_response(type) for type in task_types]
        return TaskTypeListResponse(task_types=task_type_responses)

