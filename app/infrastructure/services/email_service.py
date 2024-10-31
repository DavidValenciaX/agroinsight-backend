import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Cargar las variables de entorno
load_dotenv(override=True)

# Configuración del servicio de PrivateEmail
PRIVATEEMAIL_USER = os.getenv('PRIVATEEMAIL_USER')  # tu email de privateemail, ej: 'agroinsight@agroinsight.site'
PRIVATEEMAIL_PASSWORD = os.getenv('PRIVATEEMAIL_PASSWORD')  # tu contraseña de privateemail
SMTP_SERVER = "mail.privateemail.com"
SMTP_PORT = 465  # Puerto SSL para el servidor de salida

def send_email(to_email: str, subject: str, text_content: str, html_content: str):
    """
    Envía un correo electrónico usando PrivateEmail SMTP.

    Args:
        to_email (str): Dirección de correo electrónico del destinatario.
        subject (str): Asunto del correo electrónico.
        text_content (str): Contenido del correo en formato texto plano.
        html_content (str): Contenido del correo en formato HTML.

    Returns:
        bool: True si el correo se envió exitosamente, False en caso contrario.
    """
    try:
        # Crear el mensaje MIME
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = PRIVATEEMAIL_USER
        message["To"] = to_email

        # Adjuntar las partes de texto plano y HTML
        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")

        message.attach(part1)
        message.attach(part2)

        # Configurar el contexto SSL
        context = ssl.create_default_context()

        # Conectarse al servidor SMTP y enviar el correo
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(PRIVATEEMAIL_USER, PRIVATEEMAIL_PASSWORD)
            # Enviar el correo y obtener la respuesta del servidor
            response = server.sendmail(PRIVATEEMAIL_USER, to_email, message.as_string())
            
            # Verificar la respuesta del servidor SMTP
            if response == {}:
                print("Correo enviado exitosamente.")
                return True
            else:
                print(f"Error en algunos destinatarios: {response}")
                return False

    except Exception as e:
        print(f"Error al enviar el correo electrónico: {e}")
        return False

