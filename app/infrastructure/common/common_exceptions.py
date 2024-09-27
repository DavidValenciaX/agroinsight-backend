class DomainException(Exception):
    def __init__(self, message: str = "Error", status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class UserStateException(Exception):
    def __init__(self, message: str, status_code: int, user_state: str):
        self.message = message
        self.status_code = status_code
        self.user_state = user_state
        super().__init__(self.message)