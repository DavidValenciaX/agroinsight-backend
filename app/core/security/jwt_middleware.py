from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials 
from jose import jwt, JWTError
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.core.config.settings import SECRET_KEY, ALGORITHM
from app.user.infrastructure.repository import UserRepository
from app.infrastructure.db.connection import getDb

# Crear una instancia de HTTPBearer
security_scheme = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security_scheme),
    db: Session = Depends(getDb)
):
    token = credentials.credentials
    user_repository = UserRepository(db)

    # Verificar si el token está en la lista negra
    if user_repository.is_token_blacklisted(token):
        raise HTTPException(status_code=401, detail="Token inválido o ya ha sido cerrado la sesión")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="No se pudieron validar las credenciales")
        exp = payload.get("exp")
        if exp is None:
            raise HTTPException(status_code=401, detail="El token no tiene expiración")
        if datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="El token ha expirado")
    except JWTError:
        raise HTTPException(status_code=401, detail="No se pudieron validar las credenciales")
    
    user = user_repository.get_user_by_email(email)
    if user is None:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return user