"""Authentication endpoints: register, login, current user, admin user list."""
from fastapi import APIRouter, Depends, HTTPException, status

from backend.auth import service
from backend.auth.dependencies import get_current_user, require_admin
from backend.auth.schemas import LoginRequest, RegisterRequest, TokenResponse, UserOut
from backend.auth.security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest):
    try:
        return service.create_user(body.username, body.password)
    except service.UserExistsError:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Username already taken")


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    try:
        user = service.authenticate(body.username, body.password)
    except service.TooManyAttemptsError:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed attempts. Try again in a few minutes.",
        )
    if user is None:
        # Same message for unknown user and wrong password.
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(user["user_id"], user["role"])
    return TokenResponse(access_token=token, user=user)


@router.get("/me", response_model=UserOut)
def me(user: dict = Depends(get_current_user)):
    return user


@router.get("/users", response_model=list[UserOut])
def users(_: dict = Depends(require_admin)):
    return service.list_users()
