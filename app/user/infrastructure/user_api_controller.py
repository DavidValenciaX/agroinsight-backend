#app/user/infrastructure/user_api_controller.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.user.application.user_creation_use_case import UserCreationUseCase
from app.user.application.user_authentication_use_case import AuthUseCase
from app.user.infrastructure.sql_user_repository import UserRepository
from app.infrastructure.db.connection import getDb
from app.user.domain.user_entities import UserCreate, UserResponse, LoginRequest, TokenResponse

router = APIRouter()

router = APIRouter(prefix="/user", tags=["user"])

@router.post(
    "/create", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def create_user(user: UserCreate, db: Session = Depends(getDb)):
    user_repository = UserRepository(db)
    creation_use_case = UserCreationUseCase(user_repository)

    existing_user = user_repository.get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario con este correo electrónico ya existe.",
        )

    try:
        created_user = creation_use_case.create_user(
            nombre=user.nombre,
            apellido=user.apellido,
            email=user.email,
            password=user.password,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

    # Convertir el modelo SQLAlchemy a un modelo Pydantic
    return UserResponse.from_orm(created_user)

@router.post("/login", response_model=TokenResponse)
async def login_for_access_token(login_request: LoginRequest, db: Session = Depends(getDb)):
    user_repository = UserRepository(db)
    auth_use_case = AuthUseCase(user_repository)

    # Obtener el usuario
    user = user_repository.get_user_by_email(login_request.email)
    if user:
        # Intentar desbloquear si está bloqueado
        auth_use_case.unlock_user(user)

    # Intentar autenticar al usuario
    try:
        authenticated_user = auth_use_case.authenticate_user(login_request.email, login_request.password)
    except HTTPException as e:
        raise e  # Re-lanza la excepción para mantener el mensaje detallado

    if not authenticated_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo electrónico o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Crear el token de acceso si la autenticación es exitosa
    access_token = auth_use_case.create_access_token(data={"sub": authenticated_user.email})
    return {"access_token": access_token, "token_type": "bearer"}