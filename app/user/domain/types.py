from pydantic_core import PydanticCustomError
import re

class EmailStrCustom(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate_email

    @classmethod
    def validate_email(cls, v: str, info) -> str:
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, v):
            raise PydanticCustomError(
                'email_validation',
                'El correo electrónico no es válido. Debe contener un @ y un dominio válido.'
            )
        return cls(v)
    
class PasswordStrCustom(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate_password

    @classmethod
    def validate_password(cls, v: str, info) -> str:
        errors = []
        if len(v) < 12:
            errors.append('La contraseña debe tener al menos 12 caracteres.')
        if not re.search(r'\d', v):
            errors.append('La contraseña debe contener al menos un número.')
        if not re.search(r'[a-zA-Z]', v):
            errors.append('La contraseña debe contener al menos una letra.')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            errors.append('La contraseña debe contener al menos un carácter especial.')

        if errors:
            # Unir los errores en un solo mensaje separado por saltos de línea
            message = '\n'.join(errors)
            raise PydanticCustomError('password_validation', message)
        
        return cls(v)