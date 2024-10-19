import logging
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Cargar variables de entorno desde .env
load_dotenv(override=True)

# Definir las credenciales y configuración del servidor SMTP de Zoho
ZOHO_USER = os.getenv('ZOHO_USER')
ZOHO_PASSWORD = os.getenv('ZOHO_APP_PASSWORD')
SMTP_SERVER = "smtp.zoho.com"
SMTP_PORT = 465

def send_email(to_email: str, subject: str, text_content: str, html_content: str):
    try:
        logger.info("Iniciando proceso de envío de correo...")

        # Verificar que las variables de entorno están cargadas correctamente
        if not ZOHO_USER or not ZOHO_PASSWORD:
            logger.error("Credenciales no encontradas en las variables de entorno.")
            return False
        else:
            logger.info(f"Usuario Zoho: {ZOHO_USER}")

        # Crear el mensaje con múltiples partes (plain text y HTML)
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = ZOHO_USER
        message["To"] = to_email

        # Crear las partes de texto y HTML del mensaje
        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")

        # Adjuntar las partes al mensaje
        message.attach(part1)
        message.attach(part2)

        logger.info("Mensaje construido correctamente.")

        # Crear un contexto SSL para la conexión segura
        context = ssl.create_default_context()

        # Conectar al servidor SMTP de Zoho y enviar el correo
        logger.info(f"Conectando al servidor SMTP: {SMTP_SERVER}:{SMTP_PORT}...")

        # Habilitar el modo de depuración en el servidor SMTP
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.set_debuglevel(0)  # Desactivar depuración detallada en el servidor SMTP (la salida sería demasiado extensa)

            logger.info("Iniciando sesión en Zoho SMTP...")
            server.login(ZOHO_USER, ZOHO_PASSWORD)
            logger.info("Sesión iniciada correctamente.")

            logger.info(f"Enviando correo a {to_email}...")
            server.sendmail(ZOHO_USER, to_email, message.as_string())
            logger.info(f"Correo enviado correctamente a {to_email}.")

        return True

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"Error de autenticación SMTP: {e}")
        return {"status": "failed", "error": "SMTPAuthenticationError", "details": str(e)}
    except smtplib.SMTPRecipientsRefused as e:
        logger.error(f"Error: Destinatarios rechazados: {e.recipients}")
        return {"status": "failed", "error": "SMTPRecipientsRefused", "details": str(e)}
    except smtplib.SMTPSenderRefused as e:
        logger.error(f"Error: Remitente rechazado: {e.sender}")
        return {"status": "failed", "error": "SMTPSenderRefused", "details": str(e)}
    except smtplib.SMTPException as e:
        logger.error(f"Error general de SMTP: {e}")
        return {"status": "failed", "error": "SMTPException", "details": str(e)}
    except Exception as e:
        # Capturar cualquier otra excepción y mostrar el error
        logger.error(f"Error al enviar el correo electrónico: {e}")
        return {"status": "failed", "error": "GeneralException", "details": str(e)}
