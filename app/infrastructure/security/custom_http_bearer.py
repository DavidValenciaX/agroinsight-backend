# app/infrastructure/security/custom_http_bearer.py
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Request, HTTPException, status
from typing import Optional

class CustomHTTPBearer(HTTPBearer):
    """
    Clase personalizada para la autenticación HTTP Bearer.

    Esta clase extiende la funcionalidad de HTTPBearer para personalizar
    el manejo de tokens de autenticación Bearer en las solicitudes HTTP.
    """
    
    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        """
        Procesa la solicitud para extraer las credenciales de autorización.

        Args:
            request (Request): La solicitud HTTP que contiene el encabezado de autorización.

        Returns:
            Optional[HTTPAuthorizationCredentials]: Las credenciales de autorización si están presentes.

        Raises:
            HTTPException: Si el encabezado de autorización no está presente o no es un esquema Bearer.
        """
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
        """
        Extrae el esquema y el parámetro de un valor de encabezado de autorización.

        Args:
            authorization_header_value (str): El valor del encabezado de autorización.

        Returns:
            tuple: Un tuple que contiene el esquema y el parámetro de autorización.
        """
        if not authorization_header_value:
            return "", ""
        scheme, _, param = authorization_header_value.partition(" ")
        return scheme, param