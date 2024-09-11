import os
import secrets
import hashlib
from datetime import datetime, timedelta
from mailersend import emails
from sqlalchemy.orm import Session
from app.user.infrastructure.user_orm_model import User
from app.user.infrastructure.estado_usuario_orm_model import EstadoUsuario
from app.user.infrastructure.confirmacion_usuario_orm_model import ConfirmacionUsuario
from app.user.infrastructure.verificacion_dos_pasos_orm_model import VerificacionDospasos
from app.user.infrastructure.sql_user_repository import UserRepository
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Cambiar estas variables para utilizar MailerSend
MAILERSEND_API_KEY = os.getenv('MAILERSEND_API_KEY')  # API Key de MailerSend
FROM_EMAIL = os.getenv('FROM_EMAIL')  # El email de envío verificado en MailerSend

# Configuración de Gmail SMTP
GMAIL_USER = os.getenv('GMAIL_USER')
GMAIL_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def generate_pin():
    # Generar un PIN de 4 dígitos
    pin = ''.join(secrets.choice('0123456789') for _ in range(4))
    # Crear un hash del PIN
    pin_hash = hashlib.sha256(pin.encode()).hexdigest()
    return pin, pin_hash

def send_confirmation_email(email: str, pin: str):
    try:
        # Crear mensaje
        message = MIMEMultipart("alternative")
        message["Subject"] = "Confirma tu registro en AgroInSight"
        message["From"] = GMAIL_USER
        message["To"] = email

        # Crear versiones HTML y de texto plano del mensaje
        text = f"Tu PIN de confirmación es: {pin}\nEste PIN expirará en 10 minutos."
        html = f"<html><body><p><strong>Tu PIN de confirmación es: {pin}</strong></p><p>Este PIN expirará en 10 minutos.</p></body></html>"

        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")

        message.attach(part1)
        message.attach(part2)

        # Iniciar conexión segura con el servidor SMTP de Gmail
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.sendmail(GMAIL_USER, email, message.as_string())

        print(f"Email sent successfully to {email}")
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

def create_user_with_confirmation(db: Session, user: User) -> bool:
    try:
        # Generar PIN y su hash
        pin, pin_hash = generate_pin()
        confirmation = ConfirmacionUsuario(
            usuario_id=user.id,
            pin=pin_hash,
            expiracion=datetime.utcnow() + timedelta(minutes=10)
        )
        db.add(confirmation)
        db.commit()
        
        # Enviar el email de confirmación con el PIN de 4 dígitos
        if send_confirmation_email(user.email, pin):
            return True
        else:
            db.rollback()
            return False
    except Exception as e:
        db.rollback()
        print(f"Error al crear la confirmación del usuario: {str(e)}")
        return False

def confirm_user(db: Session, user_id: int, pin_hash: str):
    confirmation = db.query(ConfirmacionUsuario).filter(
        ConfirmacionUsuario.usuario_id == user_id,
        ConfirmacionUsuario.pin == pin_hash,
        ConfirmacionUsuario.expiracion > datetime.utcnow()
    ).first()
    
    if not confirmation:
        return False
    
    user_repository = UserRepository(db)
    user = db.query(User).filter(User.id == user_id).first()
    active_state = db.query(EstadoUsuario).filter(EstadoUsuario.nombre == 'active').first()
    user.state_id = active_state.id
    
    # Cambiar el rol del usuario
    user_repository.change_user_role(user.id, "Usuario No Confirmado", "Usuario")
    
    db.delete(confirmation)
    db.commit()
    
    return True

def handle_failed_confirmation(db: Session, user_id: int):
    confirmation = db.query(ConfirmacionUsuario).filter(ConfirmacionUsuario.usuario_id == user_id).first()
    if confirmation:
        confirmation.intentos += 1
        if confirmation.intentos >= 3:
            user = db.query(User).filter(User.id == user_id).first()
            db.delete(user)  # Esto también eliminará la confirmación debido a ON DELETE CASCADE
        else:
            db.commit()

def clean_expired_registrations(db: Session):
    expired_confirmations = db.query(ConfirmacionUsuario).filter(
        ConfirmacionUsuario.expiracion < datetime.utcnow()
    ).all()
    
    for confirmation in expired_confirmations:
        user = db.query(User).filter(User.id == confirmation.usuario_id).first()
        if user:
            db.delete(user)  # Esto también eliminará la confirmación debido a ON DELETE CASCADE
    
    db.commit()
    
def send_two_factor_pin(email: str, pin: str):
    mailer = emails.NewEmail(MAILERSEND_API_KEY)
    
    try:
        response = mailer.send(
            {
                "from": {
                    "email": FROM_EMAIL,
                    "name": "AgroInSight"
                },
                "to": [
                    {
                        "email": email
                    }
                ],
                "subject": "Código de verificación en dos pasos - AgroInSight",
                "html": f"<strong>Tu código de verificación en dos pasos es: {pin}</strong><br>Este código expirará en 5 minutos."
            }
        )
        print(f"Email sent. Status Code: {response}")
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

def create_two_factor_verification(db: Session, user: User) -> bool:
    try:
        # Eliminar cualquier verificación anterior
        db.query(VerificacionDospasos).filter(VerificacionDospasos.usuario_id == user.id).delete()
        
        # Generar un PIN de 4 dígitos
        pin = ''.join(secrets.choice('0123456789') for _ in range(4))
        
        # Crear el hash del PIN
        pin_hash = hashlib.sha256(pin.encode()).hexdigest()
        
        verification = VerificacionDospasos(
            usuario_id=user.id,
            pin=pin_hash,  # Almacenamos el hash, no el PIN original
            expiracion=datetime.utcnow() + timedelta(minutes=5)
        )
        db.add(verification)
        db.commit()
        
        # Enviar el PIN original (no el hash) por correo electrónico
        if send_two_factor_pin(user.email, pin):
            return True
        else:
            db.rollback()
            return False
    except Exception as e:
        db.rollback()
        print(f"Error al crear la verificación en dos pasos: {str(e)}")
        return False