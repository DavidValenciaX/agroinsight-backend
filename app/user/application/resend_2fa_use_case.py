from datetime import timedelta, datetime, timezone
from sqlalchemy.orm import Session
from fastapi import status
from app.user.infrastructure.orm_models import VerificacionDospasos
from app.user.infrastructure.sql_repository import UserRepository
from app.core.services.pin_service import generate_pin
from app.core.services.email_service import send_email
from app.user.domain.exceptions import DomainException

class Resend2faUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        
    def execute(self, email: str) -> str:
        user = self.user_repository.get_user_by_email(email)
        if not user:
            raise DomainException(
                message="Usuario no encontrado.",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        # Verificar si la cuenta del usuario está pendiente de confirmación
        pending_state_id = self.user_repository.get_pending_user_state_id()
        if user.state_id == pending_state_id:
            raise DomainException(
                message="La cuenta del usuario está pendiente de confirmación.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar si el usuario ha sido eliminado
        inactive_state_id = self.user_repository.get_inactive_user_state_id()
        if user.state_id == inactive_state_id:
            raise DomainException(
                message="El usuario fue eliminado del sistema.",
                status_code=status.HTTP_410_GONE
            )
        
        # Verificar si la cuenta del usuario está bloqueada
        if user.locked_until:
            user.locked_until = user.locked_until.replace(tzinfo=timezone.utc)

        locked_state_id = self.user_repository.get_locked_user_state_id()
        if user.state_id == locked_state_id and user.locked_until > datetime.now(timezone.utc):
            time_left = user.locked_until - datetime.now(timezone.utc)
            minutos_restantes = time_left.seconds // 60
            raise DomainException(
                message=f"Su cuenta está bloqueada. Intente nuevamente en {minutos_restantes} minutos.",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
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
            if self.send_two_factor_pin(user.email, pin):
                return "PIN de verificación en dos pasos reenviado con éxito."
            else:
                raise DomainException(
                    message="No se pudo reenviar el PIN. Verifique el correo electrónico o intente más tarde.",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            raise DomainException(
                message=f"Error al reenviar el PIN de doble verificación: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    def send_two_factor_pin(self, email: str, pin: str) -> bool:
        subject = "Reenvío de código de verificación en dos pasos - AgroInSight"
        text_content = f"Reenvío: Tu código de verificación en dos pasos es: {pin}\nEste código expirará en 10 minutos."
        html_content = f"""
        <html>
            <body>
                <p><strong>Reenvío: Tu código de verificación en dos pasos es: {pin}</strong></p>
                <p>Este código expirará en 10 minutos.</p>
            </body>
        </html>
        """
        
        return send_email(email, subject, text_content, html_content)