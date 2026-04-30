from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_admin
from app.models import AdminUser
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, AdminUser as AdminUserSchema
from app.services.auth_service import authenticate_user
from app.utils.security import create_access_token, hash_password
from app.config import settings

router = APIRouter()


@router.post("/register", response_model=AdminUserSchema, status_code=status.HTTP_201_CREATED)
def register(
    register_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register new admin user.

    Args:
        register_data: Registration data (email, password, name)
        db: Database session

    Returns:
        Created admin user profile

    Raises:
        HTTPException: 409 if email already exists
    """
    # Check if email already exists
    existing_user = db.query(AdminUser).filter(AdminUser.email == register_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    # Create new admin user
    new_admin = AdminUser(
        email=register_data.email,
        password_hash=hash_password(register_data.password),
        name=register_data.name
    )

    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    return AdminUserSchema(
        id=new_admin.id,
        email=new_admin.email,
        name=new_admin.name
    )


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login endpoint - authenticate user and return JWT token.

    Args:
        login_data: Login credentials (email and password)
        db: Database session

    Returns:
        JWT access token

    Raises:
        HTTPException: 401 if credentials are invalid
    """
    # Authenticate user
    user = authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
    )


@router.get("/me", response_model=AdminUserSchema, status_code=status.HTTP_200_OK)
def get_current_user(
    current_user: AdminUser = Depends(get_current_admin)
):
    """
    Get current authenticated admin user profile.

    Args:
        current_user: Current authenticated admin (from JWT token)

    Returns:
        Admin user profile
    """
    return current_user
