from sqlalchemy.orm import Session
from app.user.infrastructure.sql_repository import UserRepository
from app.user.domain.schemas import UserResponse
from app.user.domain.exceptions import DomainException
from fastapi import status

class GetCurrentUserUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        
    def execute(self, current_user):
        if not current_user:
            raise DomainException(
                message="No estás autenticado. Por favor, proporciona un token válido.",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
            
        # Obtener el estado del usuario
        estado = self.user_repository.get_state_by_id(current_user.state_id)
        if not estado:
            raise DomainException(
                message="Estado del usuario no encontrado.",
                status_code=500
            )
            
        estado_nombre = estado.nombre
        
        # Obtener el rol del usuario
        user_role = ", ".join([role.nombre for role in current_user.roles]) if current_user.roles else "Rol no asignado"

        return UserResponse(
            id=current_user.id,
            nombre=current_user.nombre,
            apellido=current_user.apellido,
            email=current_user.email,
            estado=estado_nombre,
            rol=user_role
        )