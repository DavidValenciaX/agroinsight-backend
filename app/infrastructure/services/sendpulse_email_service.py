import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv(override=True)

SENDPULSE_USER = os.getenv('SENDPULSE_CLIENT_ID')
SENDPULSE_PASSWORD = os.getenv('SENDPULSE_CLIENT_SECRET')
SMTP_SERVER = os.getenv('SENDPULSE_SMTP_SERVER')
SMTP_PORT = int(os.getenv('SENDPULSE_SMTP_PORT', 587))  # Default to 587 if not set

def send_email(to_email: str, subject: str, text_content: str, html_content: str):
    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = SENDPULSE_USER
        message["To"] = to_email

        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")

        message.attach(part1)
        message.attach(part2)

        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(SENDPULSE_USER, SENDPULSE_PASSWORD)
            server.sendmail(SENDPULSE_USER, to_email, message.as_string())
        return True
    except Exception as e:
        print(f"Error al enviar el correo electrónico: {e}")
        return False
