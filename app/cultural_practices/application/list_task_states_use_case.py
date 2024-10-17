from sqlalchemy.orm import Session
from app.cultural_practices.domain.schemas import TaskStateResponse, TaskStateListResponse
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository 
from app.infrastructure.common.common_exceptions import DomainException
from app.user.domain.schemas import UserInDB

class ListTaskStatesUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.cultural_practice_repository = CulturalPracticesRepository(db)

    def list_task_states(self, current_user: UserInDB) -> TaskStateListResponse:
        try:
            # Assuming the repository method returns a list of task state objects
            task_states = self.cultural_practice_repository.get_states()
            
            # Debugging: print the task states to check their structure
            for state in task_states:
                print(state)
            
            # Convert each task state to a dictionary if necessary
            task_state_dicts = [state.__dict__ for state in task_states]  # or use a method if available
            
            # Create TaskStateResponse objects
            task_state_responses = [TaskStateResponse.model_validate(state_dict) for state_dict in task_state_dicts]
            
            # Return a TaskStateListResponse object
            return TaskStateListResponse(states=task_state_responses)
        except Exception as e:
            raise DomainException(f"Error obteniendo los estados de las tareas: {str(e)}")
