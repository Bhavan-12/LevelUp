from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_db
from app.schemas import UserUpdate, PasswordChange, UserProfileResponse
from app.auth import get_current_user, hash_password, verify_password
from app import crud

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/profile", response_model=UserProfileResponse)
def get_profile(current_user: dict = Depends(get_current_user), conn=Depends(get_db)):
    """Retrieves the full profile details and stats of the logged-in user."""
    user = crud.get_user_by_id(conn, current_user["id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put("/profile", response_model=UserProfileResponse)
def update_profile(
    update_data: UserUpdate,
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db)
):
    """Updates user profile bio, avatar image selection, or theme preference."""
    updated_user = crud.update_user_profile(
        conn,
        user_id=current_user["id"],
        bio=update_data.bio,
        avatar_url=update_data.avatar_url,
        theme_preference=update_data.theme_preference
    )
    return updated_user


@router.post("/change-password")
def change_password(
    pwd_data: PasswordChange,
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db)
):
    """Verifies the current password and sets a new hashed password."""
    if not verify_password(pwd_data.current_password, current_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
        
    new_hashed = hash_password(pwd_data.new_password)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET hashed_password = ? WHERE id = ?", (new_hashed, current_user["id"]))
    conn.commit()
    return {"success": True, "message": "Password updated successfully"}