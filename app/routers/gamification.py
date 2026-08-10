from typing import List
from fastapi import APIRouter, Depends
from app.database import get_db
from app.schemas import AchievementResponse, ChallengeResponse, ActivityLogResponse
from app.auth import get_current_user
from app import crud

router = APIRouter(prefix="/api/gamification", tags=["Gamification"])


@router.get("/achievements", response_model=List[AchievementResponse])
def get_achievements(current_user: dict = Depends(get_current_user), conn=Depends(get_db)):
    """Retrieves all achievements with user unlock status."""
    return crud.get_user_achievements(conn, current_user["id"])


@router.get("/challenges", response_model=List[ChallengeResponse])
def get_challenges(current_user: dict = Depends(get_current_user), conn=Depends(get_db)):
    """Retrieves active daily and weekly challenges."""
    return crud.get_user_challenges(conn, current_user["id"])


@router.get("/activity", response_model=List[ActivityLogResponse])
def get_activity_feed(current_user: dict = Depends(get_current_user), conn=Depends(get_db)):
    """Retrieves recent user activity logs."""
    return crud.get_recent_activity(conn, current_user["id"])