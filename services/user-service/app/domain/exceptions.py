class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass

class UserNotFoundError(Exception):
    """Raised when a user is not found."""
    pass

class InvalidInputError(Exception):
    """Raised when input data is invalid."""
    pass