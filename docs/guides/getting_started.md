# Guía de Inicio Rápido para Desarrolladores Backend de AgroInsight

## Introducción

Bienvenido al equipo de desarrollo backend de AgroInsight. Esta guía te proporcionará la información necesaria para comenzar a contribuir al proyecto. AgroInsight es una aplicación de gestión agrícola diseñada para optimizar el cultivo de maíz en la región del Huila, Colombia, utilizando tecnologías modernas y prácticas de desarrollo ágil.

## Estructura del Proyecto

El proyecto sigue una arquitectura limpia y está organizado en módulos, cada uno con sus propias capas. La estructura general es la siguiente:

```text
app/
├── [nombre_del_modulo]/
│   ├── application/
│   ├── domain/
│   └── infrastructure/
├── infrastructure/
│   ├── common/
│   ├── database/
│   ├── security/
│   └── services/
└── main.py
```

### Estructura de un Módulo

Cuando se desarrolla un nuevo módulo, se debe crear una carpeta con el nombre del módulo dentro de `app/` y dentro de ella las siguientes subcarpetas y archivos:

- `application/`: Contiene los casos de uso (archivos `*_use_case.py`).
- `domain/`: Define las entidades y reglas de negocio.
  - `schemas.py`: Define los esquemas Pydantic del módulo.
- `infrastructure/`:
  - `api.py`: Define los endpoints del módulo.
  - `sql_repository.py`: Contiene las transacciones de la base de datos.
  - `orm_models.py`: Define los modelos ORM del módulo.

### Infraestructura Común

La carpeta `app/infrastructure` contiene archivos comunes a todo el proyecto, incluyendo:

- Conexión a la base de datos
- Middleware JWT
- Servicios para envío de emails
- Servicios para generación de PINs de seguridad
- Servicios de encriptación de contraseñas
- Servicios de generación de tokens de acceso
- Validadores
- Response mappers
- Importaciones de variables de entorno
- Errores personalizados
- Manejadores de errores
- Código común utilizado en todos los módulos

## Principios de Desarrollo

### Clean Code y Arquitectura Limpia

El proyecto AgroInsight sigue los principios de Clean Code y Arquitectura Limpia. Esto implica:

1. Separación clara de responsabilidades entre capas.
2. Dependencias apuntando hacia el dominio.
3. Entidades de negocio independientes de frameworks y detalles de implementación.
4. Casos de uso que encapsulan la lógica de la aplicación.

### Convenciones de Código

- Seguimos la guía de estilo PEP 8 para Python.
- Utilizamos Type Hints para anotaciones de tipo.
- Documentamos las funciones y clases utilizando docstrings en formato Google.
- Utilizamos Black para el formateo automático del código.
- Empleamos Flake8 para el linting del código.

### Prácticas de Codificación

1. **Early Return**: Preferimos el estilo de "early return" para mejorar la legibilidad y reducir la anidación.

2. **DRY (Don't Repeat Yourself)**: Si notas que estás repitiendo el mismo código en múltiples lugares, refactoriza ese código en una función o método reutilizable.

3. **Estructura del Proyecto**: Al desarrollar o refactorizar una funcionalidad de un módulo existente, sigue la estructura ya definida para mantener la consistencia.

4. **Nombres Descriptivos**: Usa nombres claros y significativos para variables, funciones y clases.

5. **Funciones Pequeñas**: Las funciones deben ser cortas y hacer una sola cosa.

6. **Comentarios Útiles**: Los comentarios deben explicar el "por qué", no el "qué". El código debe ser autoexplicativo.

7. **Manejo de Errores**: Implementa un manejo de errores personalizado para la lógica de negocio, la validación de datos de entrada y los errores inesperados. Los mensajes deben ser claros y consistente.

## Flujo de Trabajo de Desarrollo

1. Crea una nueva rama para tu feature o bugfix:

   ```bash
   git checkout -b feature/nombre-de-la-caracteristica
   ```

2. Desarrolla tu código siguiendo las convenciones y principios establecidos.

3. Ejecuta las pruebas unitarias y asegúrate de que pasen:

   ```bash
   pytest
   ```

4. Formatea tu código:

   ```bash
   black .
   ```

5. Ejecuta el linter:

   ```bash
   flake8
   ```

6. Realiza un commit de tus cambios:

   ```bash
   git add .
   git commit -m "Descripción concisa de los cambios"
   ```

7. Sube tus cambios a GitHub:

   ```bash
   git push origin feature/nombre-de-la-caracteristica
   ```

8. Crea un Pull Request en GitHub para revisión.

## Trabajando con la Base de Datos

AgroInsight utiliza Postgresql 16.2 como sistema de gestión de base de datos. La estructura de la base de datos se administra a través de PgAdmin utilizando lenguaje SQL. La estructura está documentada en [https://dbdocs.io/davidvalencia0526/AgroInsight](https://dbdocs.io/davidvalencia0526/AgroInsight).

## Integración con Servicios Externos

AgroInsight integra varios servicios externos. Asegúrate de tener las credenciales necesarias en tu archivo `.env`:

- API de OpenWeatherMap para datos meteorológicos
- Servicio de correo electrónico (SMTP) para notificaciones
- Servicios de almacenamiento en la nube para imágenes y archivos

## Pruebas

Ejecutamos pruebas unitarias, de integración y end-to-end. Para ejecutar todas las pruebas:

```bash
pytest
```

Para ejecutar pruebas específicas:

```bash
pytest tests/unit
pytest tests/integration
pytest tests/e2e
```

## Documentación

La documentación del API se genera automáticamente y está disponible en:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

Para generar la documentación del proyecto:

```bash
mkdocs serve
```

Esto iniciará un servidor local con la documentación en `http://localhost:8000`.

## Despliegue

El despliegue se realiza automáticamente a través de Railway cuando se fusiona código en la rama `main`. Asegúrate de que todas las pruebas pasen antes de fusionar tus cambios.

## Ejemplo de Creación de un Nuevo Módulo

Para ilustrar cómo crear un nuevo módulo en AgroInsight, vamos a desarrollar un módulo de "Análisis de Suelo". Este módulo permitirá a los usuarios registrar y consultar análisis de suelo para sus lotes.

### 1. Estructura del Módulo

Primero, creamos la estructura de carpetas para el nuevo módulo:

```text
app/
└── soil_analysis/
    ├── application/
    │   └── __init__.py
    ├── domain/
    │   ├── __init__.py
    │   └── schemas.py
    └── infrastructure/
        ├── __init__.py
        ├── api.py
        ├── orm_models.py
        └── sql_repository.py
```

### 2. Definición de Esquemas (domain/schemas.py)

```python
from pydantic import BaseModel, Field
from datetime import date
from typing import Optional

class SoilAnalysisBase(BaseModel):
    lote_id: int
    fecha_analisis: date
    ph: float = Field(..., ge=0, le=14)
    materia_organica: float = Field(..., ge=0, le=100)
    nitrogeno: float = Field(..., ge=0)
    fosforo: float = Field(..., ge=0)
    potasio: float = Field(..., ge=0)
    observaciones: Optional[str] = None

class SoilAnalysisCreate(SoilAnalysisBase):
    pass

class SoilAnalysisResponse(SoilAnalysisBase):
    id: int

    class Config:
        from_attributes = True
```

### 3. Definición de Modelos ORM (infrastructure/orm_models.py)

```python
from sqlalchemy import Column, Integer, Float, Date, ForeignKey, Text
from app.infrastructure.database.database import Base

class SoilAnalysis(Base):
    __tablename__ = "analisis_suelo"

    id = Column(Integer, primary_key=True, index=True)
    lote_id = Column(Integer, ForeignKey("lote.id"), nullable=False)
    fecha_analisis = Column(Date, nullable=False)
    ph = Column(Float, nullable=False)
    materia_organica = Column(Float, nullable=False)
    nitrogeno = Column(Float, nullable=False)
    fosforo = Column(Float, nullable=False)
    potasio = Column(Float, nullable=False)
    observaciones = Column(Text)
```

### 4. Implementación del Repositorio (infrastructure/sql_repository.py)

```python
from sqlalchemy.orm import Session
from app.soil_analysis.infrastructure.orm_models import SoilAnalysis
from app.soil_analysis.domain.schemas import SoilAnalysisCreate

class SoilAnalysisRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_soil_analysis(self, soil_analysis: SoilAnalysisCreate) -> SoilAnalysis:
        db_soil_analysis = SoilAnalysis(**soil_analysis.model_dump())
        self.db.add(db_soil_analysis)
        self.db.commit()
        self.db.refresh(db_soil_analysis)
        return db_soil_analysis

    def get_soil_analysis(self, soil_analysis_id: int) -> SoilAnalysis:
        return self.db.query(SoilAnalysis).filter(SoilAnalysis.id == soil_analysis_id).first()

    def get_soil_analyses_by_lote(self, lote_id: int):
        return self.db.query(SoilAnalysis).filter(SoilAnalysis.lote_id == lote_id).all()
```

### 5. Implementación del Caso de Uso (application/create_soil_analysis_use_case.py)

```python
from sqlalchemy.orm import Session
from app.soil_analysis.infrastructure.sql_repository import SoilAnalysisRepository
from app.soil_analysis.domain.schemas import SoilAnalysisCreate, SoilAnalysisResponse
from app.infrastructure.common.common_exceptions import DomainException
from app.user.domain.schemas import UserInDB
from fastapi import status

class CreateSoilAnalysisUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.soil_analysis_repository = SoilAnalysisRepository(db)

    def execute(self, soil_analysis_data: SoilAnalysisCreate, current_user: UserInDB) -> SoilAnalysisResponse:
        if not self.user_can_create_soil_analysis(current_user):
            raise DomainException(
                message="No tienes permisos para crear un análisis de suelo.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        # Aquí podrías agregar más validaciones, como verificar si el lote existe y pertenece al usuario

        soil_analysis = self.soil_analysis_repository.create_soil_analysis(soil_analysis_data)
        return SoilAnalysisResponse.model_validate(soil_analysis)

    def user_can_create_soil_analysis(self, user: UserInDB) -> bool:
        allowed_roles = ["Administrador de Finca", "Agrónomo"]
        return any(role.nombre in allowed_roles for role in user.roles)
```

### 6. Definición de la API (infrastructure/api.py)

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.infrastructure.database.database import getDb
from app.soil_analysis.domain.schemas import SoilAnalysisCreate, SoilAnalysisResponse
from app.soil_analysis.application.create_soil_analysis_use_case import CreateSoilAnalysisUseCase
from app.infrastructure.security.security_utils import get_current_user
from app.user.domain.schemas import UserInDB

router = APIRouter(prefix="/soil-analysis", tags=["Soil Analysis"])

@router.post("/", response_model=SoilAnalysisResponse)
def create_soil_analysis(
    soil_analysis: SoilAnalysisCreate,
    db: Session = Depends(getDb),
    current_user: UserInDB = Depends(get_current_user)
):
    use_case = CreateSoilAnalysisUseCase(db)
    try:
        return use_case.execute(soil_analysis, current_user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error interneo al crear el análisis de suelo: {str(e)}"
            )
```

### 7. Integración con el Sistema Principal (main.py)

Finalmente, incluimos el router del nuevo módulo en el archivo principal de la aplicación:

```python
from fastapi import FastAPI
from app.soil_analysis.infrastructure.api import router as soil_analysis_router

app = FastAPI()

# ... otros imports y configuraciones ...

app.include_router(soil_analysis_router)
```

### Uso de Servicios Comunes

En este ejemplo, hemos utilizado varios servicios y componentes comunes del proyecto:

1. **Base de datos**: Utilizamos la sesión de base de datos proporcionada por `getDb()`.
2. **Autenticación**: Usamos `get_current_user()` para obtener el usuario autenticado.
3. **Manejo de excepciones**: Empleamos `DomainException` para errores de dominio personalizados.
4. **Modelos ORM**: Extendemos `Base` de SQLAlchemy para nuestro modelo ORM.
5. **Validación de datos**: Utilizamos Pydantic para la validación de datos de entrada y salida.

## Recursos Adicionales

- [Documentación oficial de FastAPI](https://fastapi.tiangolo.com/)
- [Documentación de SQLAlchemy](https://docs.sqlalchemy.org/)
- [Guía de Railway para despliegue](https://docs.railway.app/)
- [Documentación de TensorFlow](https://www.tensorflow.org/api_docs)

## Soporte

Si encuentras algún problema o tienes preguntas, no dudes en contactar al equipo de desarrollo a través del canal #backend-support en Slack.

¡Bienvenido al equipo y feliz codificación!
