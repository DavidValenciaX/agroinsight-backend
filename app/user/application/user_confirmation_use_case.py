from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.user.infrastructure.orm_models.user_orm_model import User
from app.user.infrastructure.orm_models.user_confirmation_orm_model import ConfirmacionUsuario
from app.core.services.email_service import send_email
from app.core.services.pin_service import generate_pin
from app.user.infrastructure.repositories.sql_user_repository import UserRepository
from app.user.infrastructure.orm_models.user_state_orm_model import EstadoUsuario

class UserConfirmationUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        
    def create_user_with_confirmation(self, user: User) -> bool:
        try:
            # Eliminar confirmaciones anteriores si existen
            self.db.query(ConfirmacionUsuario).filter(ConfirmacionUsuario.usuario_id == user.id).delete()
            
            pin, pin_hash = generate_pin()
            confirmation = ConfirmacionUsuario(
                usuario_id=user.id,
                pin=pin_hash,
                expiracion=datetime.utcnow() + timedelta(minutes=10)
            )
            self.db.add(confirmation)
            
            if self.send_confirmation_email(user.email, pin):
                self.db.commit()
                return True
            else:
                self.db.rollback()
                return False
        except Exception as e:
            self.db.rollback()
            print(f"Error al crear la confirmación del usuario: {str(e)}")
            return False
        
    def send_confirmation_email(self, email: str, pin: str):
        subject = "Confirma tu registro en AgroInSight"
        text_content = f"Tu PIN de confirmación es: {pin}\nEste PIN expirará en 10 minutos."
        html_content = f"<html><body><p><strong>Tu PIN de confirmación es: {pin}</strong></p><p>Este PIN expirará en 10 minutos.</p></body></html>"
        
        return send_email(email, subject, text_content, html_content)
        
    def confirm_user(self, user_id: int, pin_hash: str):
        confirmation = self.db.query(ConfirmacionUsuario).filter(
            ConfirmacionUsuario.usuario_id == user_id,
            ConfirmacionUsuario.pin == pin_hash,
            ConfirmacionUsuario.expiracion > datetime.utcnow()
        ).first()
        
        if not confirmation:
            return False
        
        user_repository = UserRepository(self.db)
        user = self.db.query(User).filter(User.id == user_id).first()
        active_state = self.db.query(EstadoUsuario).filter(EstadoUsuario.nombre == 'active').first()
        user.state_id = active_state.id
        
        # Cambiar el rol del usuario
        user_repository.change_user_role(user.id, "Usuario No Confirmado", "Usuario")
        
        self.db.delete(confirmation)
        self.db.commit()
        
        return True
    
    def resend_confirmation_pin(self, email: str) -> bool:
        user = self.user_repository.get_user_by_email(email)
        if not user:
            return False
        
        try:
            # Iniciar una transacción
            self.db.begin_nested()
            
            # Eliminar la confirmación existente si la hay
            self.db.query(ConfirmacionUsuario).filter(ConfirmacionUsuario.usuario_id == user.id).delete()
            
            # Crear una nueva confirmación
            pin, pin_hash = generate_pin()
            confirmation = ConfirmacionUsuario(
                usuario_id=user.id,
                pin=pin_hash,
                expiracion=datetime.utcnow() + timedelta(minutes=10)
            )
            self.db.add(confirmation)
            
            # Intentar enviar el correo electrónico
            if self.send_confirmation_email(email, pin):
                # Si el envío del correo es exitoso, confirmar la transacción
                self.db.commit()
                return True
            else:
                # Si el envío del correo falla, revertir la transacción
                self.db.rollback()
                return False
        except Exception as e:
            # En caso de cualquier error, revertir la transacción
            self.db.rollback()
            print(f"Error al reenviar el PIN de confirmación: {str(e)}")
            return False
    
    def handle_failed_confirmation(self, user_id: int):
        confirmation = self.db.query(ConfirmacionUsuario).filter(ConfirmacionUsuario.usuario_id == user_id).first()
        if confirmation:
            confirmation.intentos += 1
            if confirmation.intentos >= 3:
                user = self.db.query(User).filter(User.id == user_id).first()
                self.db.delete(user)
            else:
                self.db.commit()