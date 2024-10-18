import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Cargar las variables de entorno
load_dotenv(override=True)

GMAIL_USER = os.getenv('GMAIL_USER')
GMAIL_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

def send_email(to_email: str, subject: str, text_content: str, html_content: str):
    try:
        # Crear el mensaje MIME
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = GMAIL_USER
        message["To"] = to_email

        # Adjuntar las partes de texto plano y HTML
        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")
        message.attach(part1)
        message.attach(part2)

        # Agregar cabeceras para solicitar confirmación de entrega o lectura
        message["Disposition-Notification-To"] = GMAIL_USER
        message["Return-Receipt-To"] = GMAIL_USER

        # Configurar el contexto SSL
        context = ssl.create_default_context()

        # Conectarse al servidor SMTP y enviar el correo
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            # Enviar el correo y obtener la respuesta del servidor
            response = server.sendmail(GMAIL_USER, to_email, message.as_string())
            
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
