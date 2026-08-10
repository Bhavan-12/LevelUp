from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from app.database import get_db
from app.schemas import AnalyticsSummary
from app.auth import get_current_user
from app import crud

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
def get_summary(current_user: dict = Depends(get_current_user), conn=Depends(get_db)):
    """Retrieves overall dashboard summary statistics."""
    return crud.get_analytics_summary(conn, current_user["id"])


@router.get("/weekly")
def get_weekly_trends(current_user: dict = Depends(get_current_user), conn=Depends(get_db)):
    """Retrieves 7-day habit completion trends."""
    return crud.get_weekly_analytics(conn, current_user["id"])


@router.get("/categories")
def get_category_stats(current_user: dict = Depends(get_current_user), conn=Depends(get_db)):
    """Retrieves category distribution breakdown."""
    return crud.get_category_breakdown(conn, current_user["id"])


@router.get("/heatmap")
def get_heatmap(current_user: dict = Depends(get_current_user), conn=Depends(get_db)):
    """Retrieves 60-day daily check-in contribution heatmap data."""
    return crud.get_habit_heatmap(conn, current_user["id"])