# app/infrastructure/security/custom_http_bearer.py
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Request, HTTPException, status
from typing import Optional

class CustomHTTPBearer(HTTPBearer):
    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        authorization: str = request.headers.get("Authorization")
        scheme, credentials = self.get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            # Personaliza el código de estado y el mensaje de error
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Se requiere un token de autenticación"
            )
        return HTTPAuthorizationCredentials(scheme=scheme, credentials=credentials)
    def get_authorization_scheme_param(self, authorization_header_value: str):
        if not authorization_header_value:
            return "", ""
        scheme, _, param = authorization_header_value.partition(" ")
        return scheme, param