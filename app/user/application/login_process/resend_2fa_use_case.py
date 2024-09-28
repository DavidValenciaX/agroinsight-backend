from datetime import timedelta, datetime, timezone
from sqlalchemy.orm import Session
from fastapi import status
from app.user.domain.schemas import SuccessResponse
from app.user.infrastructure.orm_models import VerificacionDospasos
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.services.pin_service import generate_pin
from app.infrastructure.services.email_service import send_email
from app.infrastructure.common.common_exceptions import DomainException, UserNotRegisteredException
from app.user.domain.user_state_validator import UserState, UserStateValidator

class Resend2faUseCase:
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
        
        # Verificar si hay una confirmación pendiente
        pending_verification = self.user_repository.get_user_pending_2fa_verification(user.id)
        if not pending_verification:
            raise DomainException(
                message="No hay una verificación de doble factor de autenticación pendiente para reenviar el PIN.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Eliminar cualquier verificación de dos factores existente
            self.user_repository.delete_two_factor_verification(user.id)
            
            # Generar un nuevo PIN y su hash
            pin, pin_hash = generate_pin()
            
            # Crear un nuevo registro de verificación de dos pasos
            verification = VerificacionDospasos(
                usuario_id=user.id,
                pin=pin_hash,
                expiracion=datetime.now(timezone.utc) + timedelta(minutes=10)
            )
            
            self.user_repository.add_two_factor_verification(verification)
            
            # Enviar el PIN al correo electrónico del usuario
            if not self.send_two_factor_pin(user.email, pin):
                raise DomainException(
                    message="No se pudo reenviar el PIN. Verifique el correo electrónico o intenta más tarde.",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            return SuccessResponse(
                message="PIN de verificación en dos pasos reenviado con éxito."
            )

        except Exception as e:
            raise DomainException(
                message=f"Error al reenviar el PIN de doble verificación: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    def send_two_factor_pin(self, email: str, pin: str) -> bool:
        subject = "Reenvío de PIN de verificación en dos pasos - AgroInSight"
        text_content = f"Reenvío: Tu PIN de verificación en dos pasos es: {pin}\nEste PIN expirará en 10 minutos."
        html_content = f"""
        <html>
            <body>
                <p><strong>Reenvío: Tu PIN de verificación en dos pasos es: {pin}</strong></p>
                <p>Este PIN expirará en 10 minutos.</p>
            </body>
        </html>
        """
        
        return send_email(email, subject, text_content, html_content)