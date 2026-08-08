from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_db
from app.schemas import UserRegister, UserLogin, TokenResponse
from app.auth import hash_password, verify_password, create_access_token, get_current_user
from app import crud

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse)
def register(user_data: UserRegister, conn=Depends(get_db)):
    """Registers a new user account and returns a JWT access token."""
    cursor = conn.cursor()
    
    # Check if username exists
    cursor.execute("SELECT id FROM users WHERE username = ?", (user_data.username,))
    if cursor.fetchone():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already taken"
        )
        
    # Check if email exists
    cursor.execute("SELECT id FROM users WHERE email = ?", (user_data.email,))
    if cursor.fetchone():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )
        
    hashed_pwd = hash_password(user_data.password)
    new_user = crud.create_user(
        conn,
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_pwd,
        bio=user_data.bio or "",
        avatar_url=user_data.avatar_url or "avatar-1"
    )
    
    access_token = create_access_token({"sub": new_user["id"]})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": new_user
    }


@router.post("/login", response_model=TokenResponse)
def login(login_data: UserLogin, conn=Depends(get_db)):
    """Authenticates user credentials and returns a JWT access token."""
    user = crud.get_user_by_username_or_email(conn, login_data.username_or_email)
    if not user or not verify_password(login_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password"
        )
        
    access_token = create_access_token({"sub": user["id"]})
    user_full = crud.get_user_by_id(conn, user["id"])
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_full
    }


@router.get("/me")
def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Returns details for the currently authenticated user."""
    return current_user