from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.database import get_db
from app.schemas import HabitCreate, HabitUpdate, HabitResponse
from app.auth import get_current_user
from app import crud

router = APIRouter(prefix="/api/habits", tags=["Habits"])


@router.get("", response_model=List[HabitResponse])
def get_habits(
    category: Optional[str] = Query(None),
    include_archived: bool = Query(False),
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db)
):
    """Retrieves all habits for the authenticated user."""
    return crud.get_habits_by_user(conn, current_user["id"], category=category, include_archived=include_archived)


@router.post("", response_model=HabitResponse, status_code=status.HTTP_201_CREATED)
def create_habit(
    habit_data: HabitCreate,
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db)
):
    """Creates a new habit for the authenticated user."""
    return crud.create_habit(conn, current_user["id"], habit_data.dict())


@router.get("/{habit_id}", response_model=HabitResponse)
def get_habit(
    habit_id: int,
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db)
):
    """Retrieves details for a single habit."""
    habit = crud.get_habit_by_id(conn, habit_id, current_user["id"])
    if not habit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found")
    return habit


@router.put("/{habit_id}", response_model=HabitResponse)
def update_habit(
    habit_id: int,
    update_data: HabitUpdate,
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db)
):
    """Updates an existing habit or toggles its archive state."""
    habit = crud.get_habit_by_id(conn, habit_id, current_user["id"])
    if not habit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found")
    
    updated_habit = crud.update_habit(conn, habit_id, current_user["id"], update_data.dict(exclude_unset=True))
    return updated_habit


@router.delete("/{habit_id}")
def delete_habit(
    habit_id: int,
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db)
):
    """Deletes a habit and its check-in history."""
    habit = crud.get_habit_by_id(conn, habit_id, current_user["id"])
    if not habit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found")
        
    crud.delete_habit(conn, habit_id, current_user["id"])
    return {"success": True, "message": "Habit deleted successfully"}