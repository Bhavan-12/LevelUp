from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_db
from app.schemas import CheckInRequest, CheckInResponse, HabitLogResponse
from app.auth import get_current_user
from app import crud

router = APIRouter(prefix="/api/tracking", tags=["Tracking"])


@router.post("/checkin", response_model=CheckInResponse)
def habit_checkin(
    checkin_data: CheckInRequest,
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db)
):
    """Logs a daily habit check-in (completed, missed, or skipped)."""
    if checkin_data.status not in ["completed", "missed", "skipped"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status. Must be 'completed', 'missed', or 'skipped'"
        )

    if checkin_data.status == "missed" and not checkin_data.reason.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A reason must be provided when marking a habit as missed"
        )

    res = crud.log_habit_checkin(
        conn,
        user_id=current_user["id"],
        habit_id=checkin_data.habit_id,
        log_date=checkin_data.log_date,
        status=checkin_data.status,
        reason=checkin_data.reason
    )

    if not res.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.get("message"))

    return res


@router.get("/logs/{habit_id}", response_model=List[HabitLogResponse])
def get_habit_logs(
    habit_id: int,
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db)
):
    """Retrieves all check-in history logs for a specific habit."""
    habit = crud.get_habit_by_id(conn, habit_id, current_user["id"])
    if not habit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found")

    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM habit_logs
        WHERE habit_id = ? AND user_id = ?
        ORDER BY log_date DESC
    """, (habit_id, current_user["id"]))
    
    logs = [dict(row) for row in cursor.fetchall()]
    return logs