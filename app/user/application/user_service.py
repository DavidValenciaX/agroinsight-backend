from app.core.security.security_utils import hash_password

class UserService:
    @staticmethod
    def hash_user_password(user):
        user.password = hash_password(user.password)
        return user