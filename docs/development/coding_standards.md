# Estándares de Codificación para AgroInsight

Este documento describe los estándares de codificación y las mejores prácticas para el proyecto AgroInsight.  Adherirse a estos estándares garantiza la consistencia, legibilidad y mantenibilidad en toda la base de código.

## 1. Convenciones de Nombres

### 1.1 Variables y Funciones

- Usar `snake_case` para nombres de variables y funciones.
- Los nombres deben ser descriptivos e indicar el propósito o contenido.

Ejemplos:

```python
user_name = "John Doe"
def calculate_total_cost(items):
    # Implementación de la función
```

### 1.2 Clases

- Usar `PascalCase` para nombres de clases.
- Los nombres de las clases deben ser sustantivos y representar el objeto o concepto.

Ejemplo:

```python
class UserProfile:
    # Implementación de la clase
```

### 1.3 Módulos y Paquetes

- Usar `snake_case` para nombres de módulos y paquetes.
- Mantener los nombres de los módulos cortos y descriptivos.

Ejemplo:

```python
import user_authentication
from data_processing import clean_data
```

### 1.4 Constantes

- Usar `MAYÚSCULAS` con guiones bajos para las constantes.

Ejemplo:

```python
MAX_LOGIN_ATTEMPTS = 3
DEFAULT_TIMEOUT = 30
```

## 2. Diseño del Código

### 2.1 Indentación

- Usar 4 espacios para la indentación.
- No usar tabulaciones.

### 2.2 Longitud Máxima de Línea

- Limitar todas las líneas a un máximo de 79 caracteres.
- Para bloques de texto largos (docstrings o comentarios), limitar la longitud a 72 caracteres.

### 2.3 Líneas en Blanco

- Rodear las funciones y clases de nivel superior con dos líneas en blanco.
- Usar una línea en blanco para separar los métodos dentro de una clase.
- Usar líneas en blanco con moderación dentro de las funciones para indicar secciones lógicas.

## 3. Importaciones

- Las importaciones deben estar en líneas separadas.
- Agrupar las importaciones en el siguiente orden:
  1. Importaciones de la biblioteca estándar
  2. Importaciones de terceros relacionadas
  3. Importaciones específicas de la aplicación/biblioteca local
- Usar importaciones absolutas cuando sea posible.

Ejemplo:

```python
import os
import sys

from fastapi import FastAPI
from sqlalchemy import Column, Integer

from app.models import User
from app.utils import generate_token
```

## 4. Formato de Cadenas

- Usar f-strings para el formato de cadenas cuando sea posible.
- Para versiones anteriores de Python, usar el método `.format()`.

Ejemplo:

```python
name = "Alice"
age = 30
print(f"Name: {name}, Age: {age}")
```

## 5. Comentarios y Documentación

### 5.1 Comentarios en Línea

- Usar comentarios en línea con moderación.
- Escribir comentarios que expliquen el porqué, no el qué.

### 5.2 Docstrings de Funciones y Métodos

- Usar docstrings de estilo Google para funciones y métodos.
- Incluir una breve descripción, parámetros, valores de retorno y excepciones generadas.

Ejemplo:

```python
def calculate_area(length: float, width: float) -> float:
    """
    Calcula el área de un rectángulo.

    Parameters:
        length (float): La longitud del rectángulo.
        width (float): El ancho del rectángulo.

    Returns:
        float: El área calculada.

    Raises:
        ValueError: Si la longitud o el ancho son negativos.
    """
    if length < 0 or width < 0:
        raise ValueError("La longitud y el ancho deben ser no negativos.")
    return length * width
```

### 5.3 Docstrings de Clases

- Incluir un docstring para cada clase que describa su propósito y comportamiento.

Ejemplo:

```python
class UserManager:
    """
    Gestiona las operaciones relacionadas con el usuario, como la creación, la autenticación y las actualizaciones de perfil.

    Esta clase interactúa con el modelo de Usuario y proporciona una interfaz para la gestión de usuarios
    en toda la aplicación.
    """

    def __init__(self, db_session):
        """
        Inicializa el UserManager.

        Parameters:
            db_session: La sesión de la base de datos a utilizar para las operaciones.
        """
        self.db_session = db_session
```

## 6.  Indicación de Tipos (Type Hinting)

- Usar indicaciones de tipos para los argumentos de las funciones y los valores de retorno.
- Importar tipos del módulo `typing` cuando sea necesario.

Ejemplo:

```python
from typing import List, Dict

def process_user_data(users: List[Dict[str, Any]]) -> List[User]:
    # Implementación de la función
```

## 7. Manejo de Errores

- Usar tipos de excepción específicos al generar o capturar excepciones.
- Proporcionar mensajes de error informativos.

Ejemplo:

```python
def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("No se puede dividir por cero.")
    return a / b
```

## 8. Pruebas

- Escribir pruebas unitarias para todas las funciones y métodos.
- Usar nombres descriptivos para las funciones de prueba, comenzando con `test_`.
- Apuntar a al menos un 80% de cobertura de código.

Ejemplo:

```python
def test_calculate_area_positive_values():
    assert calculate_area(5, 10) == 50

def test_calculate_area_raises_value_error():
    with pytest.raises(ValueError):
        calculate_area(-1, 5)
```

## 9. Control de Versiones

- Escribir mensajes de confirmación claros y concisos.
- Usar el tiempo presente en los mensajes de confirmación (por ejemplo, "Agregar función" no "Función agregada").
- Hacer referencia a los números de problema en los mensajes de confirmación cuando corresponda.
- Utilizar Semantic Versioning (SemVer) para el control de versiones del producto.

### 9.1 Semantic Versioning (SemVer)

El proyecto AgroInsight sigue las reglas de Semantic Versioning para el control de versiones. El formato de versión de SemVer consta de tres partes:

- **MAJOR:** Se incrementa cuando se realizan cambios incompatibles con versiones anteriores de la API.
- **MINOR:** Se incrementa cuando se añaden funcionalidades de manera compatible con versiones anteriores.
- **PATCH:** Se incrementa cuando se realizan correcciones de errores compatibles con versiones anteriores.

Ejemplo: 1.2.3 (MAJOR.MINOR.PATCH)

### 9.2 Relación entre Commits y Versiones

- Commits de tipo **feat** generalmente incrementan la versión MINOR.
- Commits de tipo **fix** generalmente incrementan la versión PATCH.
- Commits con "BREAKING CHANGE" en las notas al pie incrementan la versión MAJOR.

### 9.3 Convención de Commits

Se adopta la convención de formato de commits de Conventional Commits para estandarizar el registro de cambios y facilitar la comprensión del historial de desarrollo. Los mensajes de commit deben seguir esta estructura:

```text
<tipo>[ámbito opcional]: <descripción>

[cuerpo opcional]

[nota(s) al pie opcional(es)]
```

Donde `<tipo>` puede ser:

- **feat:** cuando se añade una nueva funcionalidad.
- **fix:** cuando se arregla un error.
- **docs:** cuando se realizan cambios en la documentación.
- **refactor:** cuando se realiza una refactorización del código sin cambiar su funcionalidad.
- **test:** cuando se añaden o modifican pruebas.
- **chore:** cuando se realizan cambios de mantenimiento o tareas no relacionadas con el código en sí.

Esta estructura de versionado y convención de commits ayuda a mantener un historial de cambios claro y a gestionar las actualizaciones del software de manera más efectiva.

## 10. Organización del Código

- Seguir la estructura modular del proyecto:
  - `app/`: Paquete principal de la aplicación
    - `[nombre_del_módulo]/`: Módulo específico (por ejemplo, `user`, `farm`, `plot`)
      - `application/`: Casos de uso y lógica de negocio
      - `domain/`: Modelos de dominio y reglas de negocio
      - `infrastructure/`: Modelos de base de datos, repositorios y rutas API

## 11. Directrices Específicas de FastAPI

- Usar modelos Pydantic para esquemas de solicitud y respuesta.
- Implementar la inyección de dependencias para sesiones de base de datos y otros recursos compartidos.
- Usar funciones asíncronas para operaciones de base de datos y llamadas a API externas.

Ejemplo:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.infrastructure.database import get_db
from app.user.domain.schemas import UserCreate, UserResponse

router = APIRouter()

@router.post("/users/", response_model=UserResponse)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Implementación
```

## 12. Operaciones de Base de Datos

- Usar SQLAlchemy ORM para las operaciones de base de datos.
- Definir los modelos de base de datos en `infrastructure/orm_models.py`.
- Implementar el patrón de repositorio para las interacciones con la base de datos.

Ejemplo:

```python
from sqlalchemy.orm import Session
from app.user.infrastructure.orm_models import User

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, user_data: dict) -> User:
        user = User(**user_data)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
```

## 13. Inyección de Dependencias

- Usar el sistema de inyección de dependencias de FastAPI para recursos compartidos.
- Crear dependencias reutilizables para operaciones comunes.

Ejemplo:

```python
from fastapi import Depends
from app.infrastructure.security import get_current_user
from app.user.domain.schemas import UserInDB

async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user)
) -> UserInDB:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    return current_user
```

## 14. Gestión de la Configuración

- Usar variables de entorno para la configuración.
- Cargar la configuración usando BaseSettings de Pydantic.

Ejemplo:

```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    api_prefix: str = "/api/v1"

    class Config:
        env_file = ".env"

settings = Settings()
```

## 15. Registro (Logging)

- Usar el módulo de registro integrado de Python.
- Configurar los niveles de registro adecuadamente para diferentes entornos.

Ejemplo:

```python
import logging

logger = logging.getLogger(__name__)

def some_function():
    logger.info("Procesamiento iniciado")
    try:
        # Alguna operación
        logger.debug("Detalles de la operación")
    except Exception as e:
        logger.error(f"Ocurrió un error: {str(e)}")
```

Siguiendo estos estándares de codificación, aseguramos una base de código consistente y mantenible para el proyecto AgroInsight.  Se deben utilizar revisiones de código regulares y herramientas de linting automatizadas para aplicar estos estándares en todo el equipo de desarrollo.
