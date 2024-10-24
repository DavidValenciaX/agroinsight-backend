from passlib.context import CryptContext
from jose import jwt
from app.infrastructure.common.datetime_utils import datetime_utc_time
from app.infrastructure.config.settings import SECRET_KEY, ALGORITHM
from datetime import timedelta

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    access_token_expire_minutes = 120
    to_encode = data.copy()
    
    current_time = datetime_utc_time()
    
    if expires_delta:
        expire = current_time + expires_delta
    else:
        expire = current_time + timedelta(minutes=access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
