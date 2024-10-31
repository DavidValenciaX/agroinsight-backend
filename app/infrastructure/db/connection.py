"""
Módulo de configuración y gestión de la conexión a la base de datos.

Este módulo proporciona la configuración necesaria para establecer la conexión
con la base de datos PostgreSQL utilizando SQLAlchemy, incluyendo la creación
del motor de base de datos y la gestión de sesiones.
"""

from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv(override=True)

DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql+psycopg2://', 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def getDb():
    """
    Genera un generador de sesiones de base de datos.

    Esta función crea una nueva sesión de base de datos y la gestiona dentro
    de un contexto, asegurando que la sesión se cierre correctamente después
    de su uso, incluso si ocurre una excepción.

    Yields:
        Session: Una sesión de SQLAlchemy para interactuar con la base de datos.

    Example:
        ```python
        db = next(getDb())
        try:
            # Usar la sesión de base de datos
            result = db.query(Model).all()
        finally:
            db.close()
        ```
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
