from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials 
from jose import jwt, JWTError
from fastapi import status
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.infrastructure.common.datetime_utils import get_datetime_utc_time
from app.infrastructure.config.settings import SECRET_KEY, ALGORITHM
from app.user.infrastructure.sql_repository import UserRepository
from app.infrastructure.db.connection import getDb
from typing import Optional

# Crear una instancia de HTTPBearer
security_scheme = HTTPBearer()

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
    db: Session = Depends(getDb)
):
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Se requiere un token de autenticación")
    
    token = credentials.credentials
    user_repository = UserRepository(db)

    # Verificar si el token está en la lista negra
    if user_repository.is_token_blacklisted(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o ya ha sido cerrada la sesión.")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Obtener el email del payload
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No se pudo validar el email")
        
        # Obtener el tiempo de expiración del payload
        exp = payload.get("exp")
        if exp is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="El token no tiene expiración.")
        
        # Convertir el tiempo de expiración a un objeto datetime
        expiration_time = datetime.fromtimestamp(exp, tz=timezone.utc)
        
        # Comparar el tiempo de expiración con el tiempo actual
        current_time = get_datetime_utc_time()
        
        if expiration_time < current_time:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="El token ha expirado.")
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"No se pudieron validar las credenciales. {e}")
    
    user = user_repository.get_user_by_email(email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="La cuenta con este email no está registrada")
    return user
