from uuid import UUID

class RefreshToken:
    def __init__(self, token: str, user_id: UUID):
        self.token = token
        self.user_id = user_id

class ResetToken:
    def __init__(self, token: str, user_id: UUID, ttl: int):
        self.token = token
        self.user_id = user_id
        self.ttl = ttl