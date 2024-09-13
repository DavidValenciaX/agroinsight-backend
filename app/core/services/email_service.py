import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv(override=True)

# Configuración de Gmail SMTP
GMAIL_USER = os.getenv('GMAIL_USER')
GMAIL_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

def send_email(to_email: str, subject: str, text_content: str, html_content: str):
    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = GMAIL_USER
        message["To"] = to_email

        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")

        message.attach(part1)
        message.attach(part2)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.sendmail(GMAIL_USER, to_email, message.as_string())
        return True
    except Exception as e:
        print(f"Error al enviar el correo electrónico: {e}")
        return False