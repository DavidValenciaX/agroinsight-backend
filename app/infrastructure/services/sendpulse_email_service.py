import os
from pysendpulse.pysendpulse import PySendPulse
from dotenv import load_dotenv

load_dotenv(override=True)

REST_API_ID = os.getenv('SENDPULSE_CLIENT_ID')
REST_API_SECRET = os.getenv('SENDPULSE_CLIENT_SECRET')
TOKEN_STORAGE = 'file'  # Puedes usar 'file' o 'memcached'
TOKEN_STORAGE_PATH = 'C:/Users/David/Downloads/Programacion/Python/agroinsight-backend/tmp' # Ruta donde se almacenará el token si usas 'file'

SPApiProxy = PySendPulse(REST_API_ID, REST_API_SECRET, TOKEN_STORAGE, token_file_path=TOKEN_STORAGE_PATH)


def send_email_sendpulse(to_email: str, subject: str, text_content: str, html_content: str):
    email = {
        'subject': subject,
        'html': html_content,
        'text': text_content,
        'from': {
            'name': 'AgroInsight',  # Reemplaza con tu nombre o el de tu empresa
            'email': 'oscarvalencia@agroinsight.cloud-ip.biz'  # Debe ser un correo electrónico verificado en SendPulse
        },
        'to': [
            {
                'name': '',  # Puedes agregar el nombre del destinatario si lo deseas
                'email': to_email
            }
        ]
    }

    response = SPApiProxy.smtp_send_mail(email)
    
    if response.get('result'):
        print(f"Correo enviado exitosamente a {to_email}")
        return True
    else:
        print(f"Error al enviar el correo electrónico: {response}")
        return False
