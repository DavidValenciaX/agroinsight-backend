from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.cultural_practices.domain.schemas import AssignmentCreate, AssignmentResponse
from app.cultural_practices.application.create_assignment_use_case import CreateAssignmentUseCase
from app.infrastructure.db.connection import getDb
from app.infrastructure.security.jwt_middleware import get_current_user
from app.user.domain.schemas import UserInDB

router = APIRouter(prefix="/cultural_practices", tags=["cultural_practices"])

@router.post("/assignments", response_model=AssignmentResponse)
def create_assignment(
    assignment: AssignmentCreate,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
):
    use_case = CreateAssignmentUseCase(db)
    try:
        return use_case.execute(assignment, current_user)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))