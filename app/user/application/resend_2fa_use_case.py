# \app\user\application\resend_2fa_use_case.py

from datetime import timedelta, datetime, timezone
from sqlalchemy.orm import Session
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
        """
        Reenvía el PIN de verificación en dos pasos al correo electrónico del usuario.
        
        Args:
            email (str): Correo electrónico del usuario.
        
        Returns:
            bool: True si el PIN se envió exitosamente, False de lo contrario.
        
        Raises:
            DomainException: Si ocurre un error durante el proceso.
        """
        user = self.user_repository.get_user_by_email(email)
        if not user:
            raise DomainException(
                message="Usuario no encontrado.",
                status_code=404
            )
            
        # Verificar el estado del usuario
        active_state_id = self.user_repository.get_active_user_state_id()
        if user.state_id != active_state_id:
            raise DomainException(message="El usuario no ha confirmado su registro o está bloqueado.", status_code=400)
        
        # Verificar si hay una confirmación pendiente
        pending_verification = self.user_repository.get_user_pending_2fa_verification(user.id)
        if not pending_verification:
            raise DomainException(message="No hay una verificación de doble factor de autenticación pendiente para reenviar el PIN.", status_code=400)
        
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
                return "PIN de verificación en dos pasos reenviado con éxito"
            else:
                raise DomainException(message="No se pudo reenviar el PIN. Verifique el correo electrónico o intente más tarde.", status_code=500)
        except Exception as e:
            raise DomainException(
                message=f"Error al reenviar el PIN de doble verificación: {str(e)}",
                status_code=500
            )
        
    def send_two_factor_pin(self, email: str, pin: str) -> bool:
        """
        Envía el PIN de verificación en dos pasos al correo electrónico del usuario.
        
        Args:
            email (str): Correo electrónico del usuario.
            pin (str): PIN de verificación.
        
        Returns:
            bool: True si el correo se envió exitosamente, False de lo contrario.
        """
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