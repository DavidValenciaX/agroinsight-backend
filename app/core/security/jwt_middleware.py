from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
from datetime import datetime, timezone
from app.core.config.settings import SECRET_KEY, ALGORITHM
from app.user.infrastructure.repositories.sql_user_repository import UserRepository
from app.infrastructure.db.connection import getDb

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
        exp = payload.get("exp")
        if exp is None:
            raise HTTPException(status_code=401, detail="Token is missing expiration")
        if datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    
    db = next(getDb())
    user_repository = UserRepository(db)
    user = user_repository.get_user_by_email(email)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user