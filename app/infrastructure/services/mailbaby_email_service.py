import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Carga las variables de entorno
load_dotenv(override=True)

# Datos de acceso a Mail Baby desde las variables de entorno
MAILBABY_USER = os.getenv('MAILBABY_USER')  # mb71670, no es un email completo
MAILBABY_PASSWORD = os.getenv('MAILBABY_PASSWORD')  # Contraseña proporcionada

# Información del servidor SMTP de Mail Baby
SMTP_SERVER = "relay.mailbaby.net"
SMTP_PORT = 587  # Puedes usar 25, 587 o 2525

def send_email_mailbaby(to_email: str, subject: str, text_content: str, html_content: str):
    try:
        # Crear el mensaje
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = "cdns1.interserver.net"  # Usa una dirección de correo válida aquí
        message["To"] = to_email

        # Partes de texto y HTML
        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")

        # Adjuntar las partes al mensaje
        message.attach(part1)
        message.attach(part2)

        # Crear contexto SSL y conectar con el servidor usando STARTTLS
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)  # Asegura la conexión
            server.login(MAILBABY_USER, MAILBABY_PASSWORD)  # Iniciar sesión en el servidor SMTP usando solo el usuario (mb71670)
            server.sendmail("cdns1.interserver.net", to_email, message.as_string())  # Enviar el correo

        return True
    except Exception as e:
        print(f"Error al enviar el correo electrónico: {e}")
        return False
