class DomainException(Exception):
    def __init__(self, message: str = "Error", status_code: int = 500, user_state: str = None):
        self.message = message
        self.status_code = status_code
        self.user_state = user_state
        super().__init__(self.message)