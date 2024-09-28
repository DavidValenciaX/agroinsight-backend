from sqlalchemy.orm import Session
from fastapi import status
from datetime import datetime, timedelta, timezone
from app.infrastructure.services.pin_service import generate_pin
from app.user.domain.schemas import SuccessResponse
from app.user.domain.user_state_validator import UserState
from app.user.infrastructure.orm_models import RecuperacionContrasena
from app.infrastructure.services.email_service import send_email
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.common.common_exceptions import DomainException, UserNotRegisteredException
from app.user.domain.user_state_validator import UserState, UserStateValidator

class PasswordRecoveryUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        self.state_validator = UserStateValidator(self.user_repository)

    def execute(self, email: str) -> dict:
        user = self.user_repository.get_user_by_email(email)
        if not user:
            raise UserNotRegisteredException()
            
        # Validar el estado del usuario
        state_validation_result = self.state_validator.validate_user_state(
            user,
            allowed_states=[UserState.ACTIVE],
            disallowed_states=[UserState.INACTIVE, UserState.PENDING, UserState.LOCKED]
        )
        if state_validation_result:
            return state_validation_result

        self.user_repository.delete_password_recovery(user.id)

        pin, pin_hash = generate_pin()

        recovery = RecuperacionContrasena(
            usuario_id=user.id,
            pin=pin_hash,
            expiracion=datetime.now(timezone.utc) + timedelta(minutes=10)
        )
        
        if not self.send_password_recovery_email(email, pin):
            raise DomainException(
                message="No se pudo enviar el PIN de recuperación a tu correo electrónico.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        self.user_repository.add_password_recovery(recovery)
        return SuccessResponse(
            message="Se ha enviado un PIN de recuperación a tu correo electrónico."
        )

    
    def send_password_recovery_email(self, email: str, pin: str) -> bool:
        subject = "Recuperación de contraseña - AgroInSight"
        text_content = f"Tu PIN de recuperación de contraseña es: {pin}\nEste PIN expirará en 10 minutos."
        html_content = f"<html><body><p><strong>Tu PIN de recuperación de contraseña es: {pin}</strong></p><p>Este PIN expirará en 10 minutos.</p></body></html>"
        
        return send_email(email, subject, text_content, html_content)