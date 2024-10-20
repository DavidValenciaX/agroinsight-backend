import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from app.user.infrastructure.api import user_router
from app.user.domain.schemas import UserCreate
from app.infrastructure.common.response_models import SuccessResponse
from fastapi import BackgroundTasks
from app.main import app
from app.infrastructure.common.common_exceptions import DomainException

# Agregar el router de usuario a la app de FastAPI para pruebas
app.include_router(user_router)

client = TestClient(app)

@pytest.fixture
def mock_db_session():
    """Fixture para simular la sesión de base de datos."""
    db = MagicMock(spec=Session)
    return db

@pytest.fixture
def mock_background_tasks():
    """Fixture para simular tareas en segundo plano."""
    return MagicMock(spec=BackgroundTasks)

@pytest.fixture
def user_create_data():
    """Fixture para simular los datos de creación de un usuario."""
    return UserCreate(
        nombre="Juan",
        apellido="Perez",
        email="juan.perez@example.com",
        password="contrasenalarga123!"
    )

@patch("app.user.application.user_register_process.user_register_use_case.UserRegisterUseCase.register_user")
@patch("app.user.infrastructure.api.getDb", return_value=MagicMock(spec=Session))
def test_register_user_success(mock_get_db, mock_register_user, user_create_data, mock_background_tasks):
    """
    Prueba para verificar que el registro de usuario se realiza con éxito.
    """
    # Simular que el caso de uso devuelve una respuesta exitosa
    mock_register_user.return_value = SuccessResponse(message="Usuario creado. Por favor, revisa tu email para confirmar el registro.")

    # Hacer la petición al endpoint de registro
    response = client.post(
        "/user/register",
        json={
            "nombre": user_create_data.nombre,
            "apellido": user_create_data.apellido,
            "email": user_create_data.email,
            "password": user_create_data.password
        }
    )

    # Verificar que la respuesta sea exitosa
    assert response.status_code == 201
    assert response.json() == {"message": "Usuario creado. Por favor, revisa tu email para confirmar el registro."}

    # Verificar que se haya llamado al caso de uso con los parámetros correctos, pero sin verificar BackgroundTasks
    called_user_data, called_background_tasks = mock_register_user.call_args[0]
    assert called_user_data == user_create_data

@patch("app.user.application.user_register_process.user_register_use_case.UserRegisterUseCase.register_user")
@patch("app.user.infrastructure.api.getDb", return_value=MagicMock(spec=Session))
def test_register_user_existing_user(mock_get_db, mock_register_user, user_create_data, mock_background_tasks):
    """
    Prueba para verificar que el registro de usuario falle si el usuario ya existe.
    """
    # Simular una excepción lanzada por el caso de uso cuando el usuario ya existe
    mock_register_user.side_effect = DomainException(message="El usuario ya existe.", status_code=400)

    # Hacer la petición al endpoint de registro
    response = client.post(
        "/user/register",
        json={
            "nombre": user_create_data.nombre,
            "apellido": user_create_data.apellido,
            "email": user_create_data.email,
            "password": user_create_data.password
        }
    )

    # Verificar que la respuesta indique que el usuario ya existe
    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "message": "El usuario ya existe.",
            "route": "http://testserver/user/register",
            "status_code": 400
        }
    }


