from typing import Optional, cast

from sqlalchemy.orm import Session

from app.models import AdminUser
from app.utils.security import verify_password


def authenticate_user(db: Session, email: str, password: str) -> Optional[AdminUser]:
    """
    Authenticate a user by email and password.

    Args:
        db: Database session
        email: User email
        password: Plain text password

    Returns:
        AdminUser if authentication succeeds, None otherwise
    """
    user = db.query(AdminUser).filter(AdminUser.email == email).first()

    if not user:
        return None

    if not verify_password(password, cast(str, user.password_hash)):
        return None

    return user
