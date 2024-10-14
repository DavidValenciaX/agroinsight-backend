from datetime import timedelta, datetime, timezone
from sqlalchemy.orm import Session
from fastapi import status
from app.user.infrastructure.orm_models import TwoStepVerification
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
        
    def login_user(self, email: str, password: str) -> SuccessResponse:
        user = self.user_repository.get_user_by_email(email)
        if not user:
            raise UserNotRegisteredException()
            
        # Eliminar verificaciones de dos pasos expiradas
        self.user_repository.delete_expired_two_factor_verifications(user.id)
        
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
        
        # Verificar si ya se ha enviado un PIN en los últimos 3 minutos
        
        # Definimos el tiempo de espera en minutos
        warning_time = 3

        # Obtenemos la última verificación de dos factores
        last_verification = self.user_repository.get_last_two_factor_verification(user.id)

        # Comprobamos si ha pasado el tiempo definido desde la última verificación
        if last_verification and (datetime_utc_time() - ensure_utc(last_verification.created_at)).total_seconds() < warning_time * 60:
            raise DomainException(
                message=f"Ya has solicitado un PIN de autenticación recientemente. Por favor, espera {warning_time} minutos antes de solicitar uno nuevo.",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        # Eliminar cualquier verificación anterior
        self.user_repository.delete_two_factor_verification(user.id)
        
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
        
        # Enviar el PIN al correo electrónico del usuario
        if not self.send_two_factor_pin(user.email, pin):
            return DomainException(
                message="Error al enviar el PIN de autenticación.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        self.user_repository.add_two_factor_verification(verification)
        return SuccessResponse(
                message="Verificación en dos pasos iniciada. Por favor, revisa tu correo electrónico para obtener el PIN."
        )


    def handle_failed_login_attempt(self, user: UserInDB) -> None:        
        max_failed_attempts = 3
        block_time = 10
        
        user.failed_attempts += 1
        
        if user.failed_attempts >= max_failed_attempts:
            user.locked_until = datetime_utc_time() + timedelta(minutes=block_time)
            user.state_id = self.user_repository.get_locked_user_state_id()
            self.user_repository.update_user(user)
            raise UserHasBeenBlockedException(block_time)
        
        self.user_repository.update_user(user)
        raise DomainException(
            message="Contraseña incorrecta.",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    def send_two_factor_pin(self, email: str, pin: str) -> bool:
        subject = "PIN de verificación en dos pasos - AgroInSight"
        text_content = f"Tu PIN de verificación en dos pasos es: {pin}\nEste PIN expirará en 10 minutos."
        html_content = f"<html><body><p><strong>Tu PIN de verificación en dos pasos es: {pin}</strong></p><p>Este PIN expirará en 10 minutos.</p></body></html>"
        
        return send_email(email, subject, text_content, html_content)
