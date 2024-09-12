import os
import secrets
import hashlib
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.user.infrastructure.user_orm_model import User
from app.user.infrastructure.user_state_orm_model import EstadoUsuario
from app.user.infrastructure.user_confirmation_orm_model import ConfirmacionUsuario
from app.user.infrastructure.two_factor_verify_orm_model import VerificacionDospasos
from app.user.infrastructure.sql_user_repository import UserRepository
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.sendmail(GMAIL_USER, to_email, message.as_string())

        print(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

def send_confirmation_email(email: str, pin: str):
    subject = "Confirma tu registro en AgroInSight"
    text_content = f"Tu PIN de confirmación es: {pin}\nEste PIN expirará en 10 minutos."
    html_content = f"<html><body><p><strong>Tu PIN de confirmación es: {pin}</strong></p><p>Este PIN expirará en 10 minutos.</p></body></html>"
    
    return send_email(email, subject, text_content, html_content)

def send_two_factor_pin(email: str, pin: str):
    subject = "Código de verificación en dos pasos - AgroInSight"
    text_content = f"Tu código de verificación en dos pasos es: {pin}\nEste código expirará en 5 minutos."
    html_content = f"<html><body><p><strong>Tu código de verificación en dos pasos es: {pin}</strong></p><p>Este código expirará en 5 minutos.</p></body></html>"
    
    return send_email(email, subject, text_content, html_content)

def create_user_with_confirmation(db: Session, user: User) -> bool:
    try:
        # Eliminar confirmaciones anteriores si existen
        db.query(ConfirmacionUsuario).filter(ConfirmacionUsuario.usuario_id == user.id).delete()
        
        pin, pin_hash = generate_pin()
        confirmation = ConfirmacionUsuario(
            usuario_id=user.id,
            pin=pin_hash,
            expiracion=datetime.utcnow() + timedelta(minutes=10)
        )
        db.add(confirmation)
        db.commit()
        
        if send_confirmation_email(user.email, pin):
            return True
        else:
            db.rollback()
            return False
    except Exception as e:
        db.rollback()
        print(f"Error al crear la confirmación del usuario: {str(e)}")
        return False

def create_two_factor_verification(db: Session, user: User) -> bool:
    try:
        db.query(VerificacionDospasos).filter(VerificacionDospasos.usuario_id == user.id).delete()
        
        pin, pin_hash = generate_pin()
        
        verification = VerificacionDospasos(
            usuario_id=user.id,
            pin=pin_hash,
            expiracion=datetime.utcnow() + timedelta(minutes=5)
        )
        db.add(verification)
        db.commit()
        
        if send_two_factor_pin(user.email, pin):
            return True
        else:
            db.rollback()
            return False
    except Exception as e:
        db.rollback()
        print(f"Error al crear la verificación en dos pasos: {str(e)}")
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

def resend_confirmation_pin(db: Session, email: str) -> bool:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return False
    
    # Eliminar la confirmación existente si la hay
    db.query(ConfirmacionUsuario).filter(ConfirmacionUsuario.usuario_id == user.id).delete()
    
    # Crear una nueva confirmación
    pin, pin_hash = generate_pin()
    confirmation = ConfirmacionUsuario(
        usuario_id=user.id,
        pin=pin_hash,
        expiracion=datetime.utcnow() + timedelta(minutes=10)
    )
    db.add(confirmation)
    db.commit()
    
    # Enviar el nuevo PIN por correo electrónico
    return send_confirmation_email(email, pin)

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