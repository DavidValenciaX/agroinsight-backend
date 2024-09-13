from dotenv import load_dotenv
import os

load_dotenv(override=True)

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = "HS256"