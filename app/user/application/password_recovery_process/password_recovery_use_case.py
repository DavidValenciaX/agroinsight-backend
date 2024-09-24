from sqlalchemy.orm import Session
from fastapi import status
from datetime import datetime, timedelta, timezone
from app.core.services.pin_service import generate_pin
from app.user.infrastructure.orm_models import RecuperacionContrasena
from app.core.services.email_service import send_email
from app.user.infrastructure.sql_repository import UserRepository
from app.user.domain.exceptions import DomainException

class PasswordRecoveryUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)

    def execute(self, email: str) -> dict:
        user = self.user_repository.get_user_by_email(email)
        if not user:
            raise DomainException(
                message="Este correo no está registrado, regístrese en la aplicación por favor.",
                status_code=status.HTTP_404_NOT_FOUND,
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

        self.user_repository.delete_password_recovery(user.id)

        pin, pin_hash = generate_pin()

        recovery = RecuperacionContrasena(
            usuario_id=user.id,
            pin=pin_hash,
            expiracion=datetime.now(timezone.utc) + timedelta(minutes=10)
        )
        
        if self.send_password_recovery_email(email, pin):
            self.user_repository.add_password_recovery(recovery)
            return {"message": "Se ha enviado un PIN de recuperación a tu correo electrónico."}
        else:
            raise DomainException(
                message="No se pudo reenviar el PIN de recuperación a tu correo electrónico.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def send_password_recovery_email(self, email: str, pin: str) -> bool:
        subject = "Recuperación de contraseña - AgroInSight"
        text_content = f"Tu PIN de recuperación de contraseña es: {pin}\nEste PIN expirará en 10 minutos."
        html_content = f"<html><body><p><strong>Tu PIN de recuperación de contraseña es: {pin}</strong></p><p>Este PIN expirará en 10 minutos.</p></body></html>"
        
        return send_email(email, subject, text_content, html_content)