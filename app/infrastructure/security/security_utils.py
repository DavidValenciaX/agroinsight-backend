from passlib.context import CryptContext
from jose import jwt
from app.infrastructure.common.datetime_utils import datetime_timezone_utc_now
from app.infrastructure.config.settings import SECRET_KEY, ALGORITHM
from datetime import timedelta, datetime, timezone

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    access_token_expire_minutes = 120
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime_timezone_utc_now() + expires_delta
    else:
        expire = datetime_timezone_utc_now() + timedelta(minutes=access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

