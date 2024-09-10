import pymysql
pymysql.install_as_MySQLdb()

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from databases import Database
import os
from dotenv import load_dotenv

load_dotenv()

# Asegúrate de que DATABASE_URL esté en el formato correcto para PyMySQL
DATABASE_URL = os.getenv('MYSQL_PUBLIC_URL')
if DATABASE_URL and DATABASE_URL.startswith('mysql://'):
    DATABASE_URL = DATABASE_URL.replace('mysql://', 'mysql+pymysql://', 1)

# Configuración de SQLAlchemy
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Conexión asincrónica para el manejo con FastAPI
database = Database(DATABASE_URL)

# Función para obtener la sesión de la base de datos
def getDb():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Funciones para manejar la conexión asíncrona
async def conectar():
    await database.connect()

async def desconectar():
    await database.disconnect()