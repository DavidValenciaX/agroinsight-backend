from dotenv import load_dotenv
import os

load_dotenv(override=True)

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM', 'HS256')
WARNING_TIME = os.getenv('WARNING_TIME', 1)
DEFAULT_EXPIRATION_TIME = int(os.getenv('DEFAULT_EXPIRATION_TIME', 10))