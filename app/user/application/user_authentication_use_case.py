from datetime import timedelta, datetime, timezone
from app.user.domain.user_entities import UserInDB
from app.user.domain.user_repository_interface import UserRepositoryInterface
from jose import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_TIME = timedelta(minutes=5)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthUseCase:
    def __init__(self, user_repository: UserRepositoryInterface):
        self.user_repository = user_repository

    def verify_password(self, plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)

    def authenticate_user(self, email: str, password: str) -> UserInDB:
        user = self.user_repository.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado.",
            )
        
        # Verificar si el usuario está activo
        if user.state_id != 1:  # 1 corresponde a 'active'
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="La cuenta no está activa o está bloqueada.",
            )
        
        # Verificar si la cuenta está bloqueada temporalmente
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            time_left = user.locked_until - datetime.now(timezone.utc)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"La cuenta está bloqueada temporalmente. Intenta nuevamente en {time_left.seconds // 60} minutos.",
            )

        if not self.verify_password(password, user.password):
            self._handle_failed_login_attempt(user)
            return None
        
        # Resetear intentos fallidos en caso de éxito
        user.failed_attempts = 0
        user.locked_until = None
        self.user_repository.update_user(user)
        return user

    def create_access_token(self, data: dict, expires_delta: timedelta = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def _handle_failed_login_attempt(self, user: UserInDB):
        user.failed_attempts += 1
        if user.failed_attempts >= MAX_FAILED_ATTEMPTS:
            user.locked_until = datetime.now(timezone.utc) + LOCKOUT_TIME
            user.state_id = 3  # 3 corresponde a 'locked'
            self.user_repository.update_user(user)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"La cuenta ha sido bloqueada debido a múltiples intentos fallidos. Intenta nuevamente después de {LOCKOUT_TIME.seconds // 60} minutos.",
            )
        self.user_repository.update_user(user)

    def unlock_user(self, user: UserInDB):
        current_time = datetime.now(timezone.utc)
        
        # Convertir user.locked_until a un datetime consciente de zona horaria
        if user.locked_until:
            user.locked_until = user.locked_until.replace(tzinfo=timezone.utc)
        
        if user.state_id == 3 and user.locked_until and current_time > user.locked_until:
            user.failed_attempts = 0
            user.locked_until = None
            user.state_id = 1  # Volver a estado "active"
            self.user_repository.update_user(user)