import os
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from aiosmtplib import SMTP
from dotenv import load_dotenv

load_dotenv(override=True)

GMAIL_USER = os.getenv('GMAIL_USER')
GMAIL_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

async def send_email(to_email: str, subject: str, text_content: str, html_content: str):
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
        smtp = SMTP(hostname=SMTP_SERVER, port=SMTP_PORT, use_tls=True)

        # Conectar usando el contexto SSL
        await smtp.connect(tls_context=context)
        await smtp.login(GMAIL_USER, GMAIL_PASSWORD)
        await smtp.sendmail(GMAIL_USER, to_email, message.as_string())
        return True
    except Exception as e:
        print(f"Error al enviar el correo electrónico: {e}")
        return False
