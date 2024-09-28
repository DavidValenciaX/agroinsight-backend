from datetime import timedelta, datetime, timezone
from sqlalchemy.orm import Session
from fastapi import status
from app.user.infrastructure.orm_models import VerificacionDospasos
from app.user.domain.schemas import SuccessResponse, UserInDB
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.services.pin_service import generate_pin
from app.infrastructure.services.email_service import send_email
from app.infrastructure.security.security_utils import verify_password
from app.infrastructure.common.common_exceptions import DomainException, UserNotRegisteredException
from app.user.domain.user_state_validator import UserState, UserStateValidator

class LoginUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        self.state_validator = UserStateValidator(self.user_repository)
        
    def execute(self, email: str, password: str) -> dict:
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

        if not verify_password(password, user.password):
            self.handle_failed_login_attempt(user)
        
        # Autenticación exitosa
        user.failed_attempts = 0
        user.locked_until = None
        self.user_repository.update_user(user)
        
        if not self.initiate_two_factor_auth(user):
            raise DomainException(
                message="Error al iniciar la verificación en dos pasos.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        return SuccessResponse(
                message="Verificación en dos pasos iniciada. Por favor, revisa tu correo electrónico para obtener el PIN."
        )


    def handle_failed_login_attempt(self, user: UserInDB) -> None:        
        maxFailedAttempts = 3
        block_time = 10  # minutos
        
        user.failed_attempts += 1
        
        if user.failed_attempts >= maxFailedAttempts:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=block_time)
            user.state_id = self.user_repository.get_locked_user_state_id()
            self.user_repository.update_user(user)
            raise DomainException(
                message=f"La cuenta ha sido bloqueada debido a múltiples intentos fallidos. Intente nuevamente en {block_time} minutos.",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        self.user_repository.update_user(user)
        raise DomainException(
            message="Contraseña incorrecta.",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    def initiate_two_factor_auth(self, user: UserInDB) -> bool:
        try:
            # Eliminar cualquier verificación anterior
            self.user_repository.delete_two_factor_verification(user.id)
            
            # Generar el PIN y su hash
            pin, pin_hash = generate_pin()
            
            # Crear un nuevo registro de verificación
            verification = VerificacionDospasos(
                usuario_id=user.id,
                pin=pin_hash,
                expiracion=datetime.now(timezone.utc) + timedelta(minutes=5)
            )
            
            # Enviar el PIN al correo electrónico del usuario
            if not self.send_two_factor_pin(user.email, pin):
                return False

            self.user_repository.add_two_factor_verification(verification)
            return True

            
        except Exception as e:
            print(f"Error al iniciar la verificación en dos pasos: {str(e)}")
            return False

    def send_two_factor_pin(self, email: str, pin: str) -> bool:
        subject = "PIN de verificación en dos pasos - AgroInSight"
        text_content = f"Tu PIN de verificación en dos pasos es: {pin}\nEste PIN expirará en 10 minutos."
        html_content = f"<html><body><p><strong>Tu PIN de verificación en dos pasos es: {pin}</strong></p><p>Este PIN expirará en 10 minutos.</p></body></html>"
        
        return send_email(email, subject, text_content, html_content)