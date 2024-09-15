from datetime import timedelta, datetime, timezone
from sqlalchemy.orm import Session
from jose import jwt
from fastapi import HTTPException, status
from app.user.domain.user_entities import UserInDB
from app.user.infrastructure.repositories.sql_user_repository import UserRepository
from app.user.infrastructure.orm_models.two_factor_verify_orm_model import VerificacionDospasos
from app.user.infrastructure.orm_models.user_orm_model import User
from app.core.services.pin_service import generate_pin
from app.core.services.email_service import send_email
from app.core.config.settings import SECRET_KEY, ALGORITHM
from app.core.security.security_utils import verify_password
import hashlib

class AuthenticationUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)

    def authenticate_user(self, email: str, password: str) -> UserInDB:
        user = self.user_repository.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado.",
            )
        
        # Intentar desbloquear si está bloqueado y el tiempo de bloqueo ha pasado
        if user.state_id == 3:  # 3 corresponde a 'locked'
            self.unlock_user(user)
            # Recargar el usuario después del desbloqueo
            user = self.user_repository.get_user_by_email(email)
        
        if user.state_id != 1:  # 1 corresponde a 'active'
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="La cuenta no está activa o está bloqueada.",
            )
        
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            time_left = user.locked_until - datetime.now(timezone.utc)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"La cuenta está bloqueada temporalmente. Intenta nuevamente en {time_left.seconds // 60} minutos.",
            )

        if not verify_password(password, user.password):
            return self.handle_failed_login_attempt(user)
        
        # Autenticación exitosa
        user.failed_attempts = 0
        user.locked_until = None
        return self.user_repository.update_user(user)

    def create_access_token(self, data: dict, expires_delta: timedelta = None):
        accessTokenExpireMinutes = 30
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=accessTokenExpireMinutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def handle_failed_login_attempt(self, user: UserInDB) -> None:        
        maxFailedAttempts = 5
        lockOutTime = timedelta(minutes=5)
        
        user.failed_attempts += 1
        
        if user.failed_attempts >= maxFailedAttempts:
            user.locked_until = datetime.now(timezone.utc) + lockOutTime
            user.state_id = 3  # Estado bloqueado
            self.user_repository.update_user(user)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"La cuenta ha sido bloqueada debido a múltiples intentos fallidos. Intenta nuevamente después de {lockOutTime.seconds // 60} minutos.",
            )
        
        self.user_repository.update_user(user)
        return None

    def unlock_user(self, user: UserInDB):
        current_time = datetime.now(timezone.utc)
        
        if user.locked_until:
            user.locked_until = user.locked_until.replace(tzinfo=timezone.utc)
        
        if user.state_id == 3 and user.locked_until and current_time > user.locked_until:
            user.failed_attempts = 0
            user.locked_until = None
            user.state_id = 1  # Estado activo
            self.user_repository.update_user(user)

    # Métodos de autenticación de dos factores
    def initiate_two_factor_auth(self, user: User) -> bool:
        return self.create_two_factor_verification(self.db, user)
    
    def create_two_factor_verification(self, db: Session, user: User) -> bool:
        try:
            db.query(VerificacionDospasos).filter(VerificacionDospasos.usuario_id == user.id).delete()
            
            pin, pin_hash = generate_pin()
            
            verification = VerificacionDospasos(
                usuario_id=user.id,
                pin=pin_hash,
                expiracion=datetime.utcnow() + timedelta(minutes=5)
            )
            db.add(verification)
            
            if self.send_two_factor_pin(user.email, pin):
                db.commit()
                return True
            else:
                db.rollback()
                return False
        except Exception as e:
            db.rollback()
            print(f"Error al crear la verificación en dos pasos: {str(e)}")
            return False
        
    def send_two_factor_pin(self, email: str, pin: str):
        subject = "Código de verificación en dos pasos - AgroInSight"
        text_content = f"Tu código de verificación en dos pasos es: {pin}\nEste código expirará en 5 minutos."
        html_content = f"<html><body><p><strong>Tu código de verificación en dos pasos es: {pin}</strong></p><p>Este código expirará en 5 minutos.</p></body></html>"
        
        return send_email(email, subject, text_content, html_content)

    def verify_two_factor_pin(self, user_id: int, pin: str) -> bool:
        pin_hash = hashlib.sha256(pin.encode()).hexdigest()
        verification = self.db.query(VerificacionDospasos).filter(
            VerificacionDospasos.usuario_id == user_id,
            VerificacionDospasos.pin == pin_hash,
            VerificacionDospasos.expiracion > datetime.utcnow()
        ).first()

        if not verification:
            return False

        self.db.delete(verification)
        self.db.commit()
        return True
    
    def resend_2fa_pin(self, email: str) -> bool:
        user = self.user_repository.get_user_by_email(email)
        if not user:
            return False
        
        try:
            self.db.begin_nested()
            self.db.query(VerificacionDospasos).filter(VerificacionDospasos.usuario_id == user.id).delete()
            
            pin, pin_hash = generate_pin()
            
            verification = VerificacionDospasos(
                usuario_id=user.id,
                pin=pin_hash,
                expiracion=datetime.utcnow() + timedelta(minutes=5)
            )
            self.db.add(verification)
            
            if self.send_two_factor_pin(user.email, pin):
                self.db.commit()
                return True
            else:
                self.db.rollback()
                return False
        except Exception as e:
            self.db.rollback()
            print(f"Error al reenviar el PIN de doble verificación: {str(e)}")
            return False

    def handle_failed_verification(self, user_id: int):
        verification = self.db.query(VerificacionDospasos).filter(VerificacionDospasos.usuario_id == user_id).first()
        if verification:
            verification.intentos += 1
            if verification.intentos >= 3:
                user = self.db.query(User).filter(User.id == user_id).first()
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
                user.state_id = 3  # Estado bloqueado
                self.db.delete(verification)
            self.db.commit()