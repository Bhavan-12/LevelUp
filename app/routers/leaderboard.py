from typing import List
from fastapi import APIRouter, Depends, Query
from app.database import get_db
from app.schemas import LeaderboardEntry
from app.auth import get_current_user
from app import crud

router = APIRouter(prefix="/api/leaderboard", tags=["Leaderboard"])


@router.get("", response_model=List[LeaderboardEntry])
def get_leaderboard(
    timeframe: str = Query("all_time", regex="^(all_time|monthly|weekly)$"),
    metric: str = Query("xp", regex="^(xp|streak|completion_rate)$"),
    filter_friends: bool = Query(False),
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db)
):
    """Retrieves ranked users on the leaderboard based on chosen filters."""
    return crud.get_leaderboard(
        conn,
        current_user_id=current_user["id"],
        timeframe=timeframe,
        metric=metric,
        filter_friends=filter_friends
    )