"""In-memory user store (demonstration only, no database yet)."""

from services.user_service.app.models.user import User

# Seed records so the API has something to return in this step.
_USERS: dict[int, User] = {
    1: User(id=1, name="Ada Lovelace", email="ada@example.com"),
    2: User(id=2, name="Grace Hopper", email="grace@example.com"),
    3: User(id=3, name="Alan Turing", email="alan@example.com", active=False),
}


def get_user(user_id: int) -> User | None:
    """Return the user with ``user_id``, or None when unknown."""
    return _USERS.get(user_id)