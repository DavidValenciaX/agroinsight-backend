from datetime import timedelta, datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks, status
from app.user.infrastructure.orm_models import TwoStepVerification, User
from app.infrastructure.common.response_models import SuccessResponse
from app.user.domain.schemas import UserInDB
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.services.pin_service import generate_pin
from app.infrastructure.services.email_service import send_email
from app.infrastructure.security.security_utils import verify_password
from app.infrastructure.common.common_exceptions import DomainException, UserHasBeenBlockedException, UserNotRegisteredException
from app.user.domain.user_state_validator import UserState, UserStateValidator
from app.infrastructure.common.datetime_utils import ensure_utc, datetime_utc_time

class LoginUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        self.state_validator = UserStateValidator(db)
        
    def login_user(self, email: str, password: str, background_tasks: BackgroundTasks) -> SuccessResponse:
        user = self.user_repository.get_user_with_two_factor_verification(email)
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
        
        # Verificar si verification trajo una lista de varias verificaciones,
        verification = self.get_last_verification(user.verificacion_dos_pasos)
            
        # Verificar si ya se ha enviado un PIN en los ltimos 3 minutos
        warning_time = 3

        if verification:
            if self.was_recently_requested(verification, warning_time):
                raise DomainException(
                    message=f"Ya has solicitado un PIN de autenticación recientemente. Por favor, espera {warning_time} minutos antes de solicitar uno nuevo.",
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS
                )
            
            # Eliminar verificaciones de dos pasos expiradas
            self.user_repository.delete_two_factor_verification(verification)

        if not verify_password(password, user.password):
            self.handle_failed_login_attempt(user)
        
        # Autenticación exitosa
        user.failed_attempts = 0
        user.locked_until = None
        self.user_repository.update_user(user)
        
        # Generar el PIN y su hash
        pin, pin_hash = generate_pin()
        
        expiration_time = 10  # minutos
        expiration_datetime = datetime_utc_time() + timedelta(minutes=expiration_time)
        
        # Crear un nuevo registro de verificación
        verification = TwoStepVerification(
            usuario_id=user.id,
            pin=pin_hash,
            expiracion=expiration_datetime,
            resends=0,
            created_at=datetime_utc_time()
        )
        
        self.user_repository.add_two_factor_verification(verification)
        
        # Enviar el PIN al correo electrónico del usuario
        background_tasks.add_task(self.send_two_factor_verification_email, user.email, pin)

        return SuccessResponse(
            message="Verificación en dos pasos iniciada. Por favor, revisa tu correo electrónico para obtener el PIN."
        )

    def handle_failed_login_attempt(self, user: User) -> None:        
        max_failed_attempts = 3
        block_time = 10
        
        user.failed_attempts += 1
        self.user_repository.update_user(user)

        if user.failed_attempts >= max_failed_attempts:
            self.block_user(user, timedelta(minutes=block_time))
            raise UserHasBeenBlockedException(block_time)

        raise DomainException(
            message="Contraseña incorrecta.",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    def send_two_factor_verification_email(self, email: str, pin: str) -> bool:
        subject = "PIN de verificación en dos pasos - AgroInSight"
        text_content = f"Tu PIN de verificación en dos pasos es: {pin}\nEste PIN expirará en 10 minutos."
        html_content = f"<html><body><p><strong>Tu PIN de verificación en dos pasos es: {pin}</strong></p><p>Este PIN expirará en 10 minutos.</p></body></html>"
        
        return send_email(email, subject, text_content, html_content)
    
    def was_recently_requested(self, verification: TwoStepVerification, minutes: int = 3) -> bool:
        """Verifica si la verificación de dos pasos se solicitó hace menos de x minutos."""
        return (datetime_utc_time() - ensure_utc(verification.created_at)).total_seconds() < minutes * 60
    
    def get_last_verification(self, verification: TwoStepVerification) -> Optional[TwoStepVerification]:
        """Obtiene la última verificación de dos pasos si existe."""
        if isinstance(verification, list) and verification:
            # Ordenar las verificaciones por fecha de creación de forma ascendente
            verification.sort(key=lambda v: v.created_at)
            # Tomar el último registro
            latest_verification = verification[-1]
            # Eliminar todas las verificaciones anteriores a la última
            for old_verification in verification[:-1]:
                self.user_repository.delete_two_factor_verification(old_verification)
            # Actualizar la variable verification para solo trabajar con la última
            return latest_verification
        # Si no hay verificaciones, retornar None
        return None

    def block_user(self, user: User, lock_duration: timedelta) -> bool:
        user.locked_until = datetime_utc_time() + lock_duration
        user.state_id = self.user_repository.get_locked_user_state().id
        return self.user_repository.update_user(user)
