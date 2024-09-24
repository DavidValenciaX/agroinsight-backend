from sqlalchemy.orm import Session
from fastapi import status
from app.user.infrastructure.orm_models import User, ConfirmacionUsuario
from app.user.infrastructure.sql_repository import UserRepository
from app.user.domain.schemas import UserCreate
from app.core.security.security_utils import hash_password
from app.user.domain.exceptions import DomainException
from app.core.services.pin_service import generate_pin
from app.core.services.email_service import send_email
from datetime import datetime, timezone, timedelta

class UserCreationUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)

    def execute(self, user_data: UserCreate) -> dict:
        # Verificar si el usuario ya existe
        existing_user = self.user_repository.get_user_by_email(user_data.email)
        
        if existing_user:
            # Verificar el estado del usuario
            active_state_id = self.user_repository.get_active_user_state_id()
            if existing_user.state_id == active_state_id:
                raise DomainException(
                    message="La cuenta ya está confirmada y activa.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                
            # Verificar si el usuario ha sido eliminado
            inactive_state_id = self.user_repository.get_inactive_user_state_id()
            if existing_user.state_id == inactive_state_id:
                raise DomainException(
                    message="El usuario fue eliminado del sistema.",
                    status_code=status.HTTP_410_GONE
                )

            # Verificar si la cuenta del usuario está bloqueada        
            if existing_user.locked_until:
                existing_user.locked_until = existing_user.locked_until.replace(tzinfo=timezone.utc)

            locked_state_id = self.user_repository.get_locked_user_state_id()
            if existing_user.state_id == locked_state_id and existing_user.locked_until > datetime.now(timezone.utc):
                time_left = existing_user.locked_until - datetime.now(timezone.utc)
                minutos_restantes = time_left.seconds // 60
                raise DomainException(
                    message=f"Tu cuenta está bloqueada. Intenta nuevamente en {minutos_restantes} minutos.",
                    status_code=status.HTTP_403_FORBIDDEN
                )
            
            # Verificar si el usuario tiene una confirmación pendiente
            pending_confirmation = self.user_repository.get_user_pending_confirmation(existing_user.id)
            if pending_confirmation:
                # Eliminar usuario y confirmación pendiente para crearlos de nuevo
                self.user_repository.delete_user_confirmations(existing_user.id)
                self.user_repository.delete_user(existing_user)

        # Hash del password
        hashed_password = hash_password(user_data.password)

        # Obtener estado "pendiente" del usuario
        pending_state_id = self.user_repository.get_pending_user_state_id()
        if not pending_state_id:
            raise DomainException(
                message="No se pudo encontrar el estado de usuario pendiente.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Crear nuevo usuario
        new_user = User(
            nombre=user_data.nombre,
            apellido=user_data.apellido,
            email=user_data.email,
            password=hashed_password,
            state_id=pending_state_id
        )
        created_user = self.user_repository.create_user(new_user)

        # Asignar rol de "Usuario No Confirmado"
        unconfirmed_role = self.user_repository.get_unconfirmed_user_role()
        if unconfirmed_role:
            if not self.user_repository.assign_role_to_user(created_user.id, unconfirmed_role.id):
                self.user_repository.delete_user(created_user)  # Eliminar el usuario si falla la asignación del rol
                raise DomainException(
                    message="No se pudo asignar el rol de Usuario No Confirmado.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
        else:
            self.user_repository.delete_user(created_user)  # Eliminar el usuario si no se encuentra el rol
            raise DomainException(
                message="No se pudo encontrar el rol de Usuario No Confirmado.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Intentar crear la confirmación y enviar el correo
        if not self.create_and_send_confirmation(created_user):
            # Si falla la confirmación, eliminar el usuario
            self.user_repository.delete_user(created_user)
            raise DomainException(
                message="Error al crear la confirmación de usuario.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return {"message":"Usuario creado. Por favor, revisa tu email para confirmar el registro."}

    def create_and_send_confirmation(self, user: User) -> bool:
        try:
            # Generar PIN y su hash
            expiration_time = 10  # minutos
            pin, pin_hash = generate_pin()
            confirmation = ConfirmacionUsuario(
                usuario_id=user.id,
                pin=pin_hash,
                expiracion=datetime.now(timezone.utc) + timedelta(minutes=expiration_time)
            )

            # Enviar correo de confirmación
            if self.send_confirmation_email(user.email, pin):
                return self.user_repository.add_user_confirmation(confirmation)
            else:
                return False
        except Exception as e:
            print(f"Error al crear la confirmación del usuario: {str(e)}")
            return False

    def send_confirmation_email(self, email: str, pin: str) -> bool:
        """Envía un correo electrónico con el PIN de confirmación."""
        subject = "Confirma tu registro en AgroInSight"
        text_content = f"Tu PIN de confirmación es: {pin}\nEste PIN expirará en 10 minutos."
        html_content = f"""
        <html>
            <body>
                <p><strong>Tu PIN de confirmación es: {pin}</strong></p>
                <p>Este PIN expirará en 10 minutos.</p>
            </body>
        </html>
        """
        return send_email(email, subject, text_content, html_content)