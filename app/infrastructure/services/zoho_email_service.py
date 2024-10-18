import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv(override=True)

# Definir las credenciales y configuración del servidor SMTP de Zoho
ZOHO_USER = os.getenv('ZOHO_USER')
ZOHO_PASSWORD = os.getenv('ZOHO_APP_PASSWORD')
SMTP_SERVER = "smtp.zoho.com"
SMTP_PORT = 465

def send_email_zoho(to_email: str, subject: str, text_content: str, html_content: str):
    try:
        print("Iniciando proceso de envío de correo...")  # Depuración

        # Verificar que las variables de entorno están cargadas correctamente
        if not ZOHO_USER or not ZOHO_PASSWORD:
            print("Error: Credenciales no encontradas en las variables de entorno.")
            return False
        else:
            print(f"Usuario Zoho: {ZOHO_USER}")  # Depuración

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

        print("Mensaje construido correctamente.")  # Depuración

        # Crear un contexto SSL para la conexión segura
        context = ssl.create_default_context()

        # Conectar al servidor SMTP de Zoho y enviar el correo
        print(f"Conectando al servidor SMTP: {SMTP_SERVER}:{SMTP_PORT}...")  # Depuración

        # Habilitar el modo de depuración en el servidor SMTP
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.set_debuglevel(1)  # Habilitar depuración detallada en la conexión SMTP
            
            print("Iniciando sesión en Zoho SMTP...")  # Depuración
            server.login(ZOHO_USER, ZOHO_PASSWORD)
            print("Sesión iniciada correctamente.")  # Depuración

            print(f"Enviando correo a {to_email}...")  # Depuración
            server.sendmail(ZOHO_USER, to_email, message.as_string())
            print("Correo enviado correctamente.")  # Depuración

        return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"Error de autenticación SMTP: {e}")
        return False
    except smtplib.SMTPRecipientsRefused as e:
        print(f"Error: Destinatarios rechazados: {e}")
        return False
    except smtplib.SMTPSenderRefused as e:
        print(f"Error: Remitente rechazado: {e}")
        return False
    except smtplib.SMTPException as e:
        print(f"Error general de SMTP: {e}")
        return False
    except Exception as e:
        # Capturar cualquier otra excepción y mostrar el error
        print(f"Error al enviar el correo electrónico: {e}")
        return False
