from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.database import get_db
from app.schemas import UserSearchResponse, FriendRequestCreate, FriendRequestAction, FriendProfileResponse
from app.auth import get_current_user
from app import crud

router = APIRouter(prefix="/api/social", tags=["Social"])


@router.get("/search", response_model=List[UserSearchResponse])
def search_users(
    query: str = Query(..., min_length=1),
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db)
):
    """Searches for users by username and returns relationship statuses."""
    return crud.search_users(conn, current_user["id"], query)


@router.post("/request")
def send_friend_request(
    request_data: FriendRequestCreate,
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db)
):
    """Sends a friend request to another user."""
    res = crud.send_friend_request(conn, current_user["id"], request_data.receiver_id)
    if not res.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.get("message"))
    return res


@router.post("/respond")
def respond_friend_request(
    action_data: FriendRequestAction,
    action: str = Query(..., regex="^(accept|reject)$"),
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db)
):
    """Accepts or rejects an incoming friend request."""
    res = crud.respond_friend_request(conn, current_user["id"], action_data.request_id, action)
    if not res.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.get("message"))
    return res


@router.get("/friends")
def get_friends(current_user: dict = Depends(get_current_user), conn=Depends(get_db)):
    """Retrieves the list of confirmed friends."""
    return crud.get_friends_list(conn, current_user["id"])


@router.get("/pending")
def get_pending_requests(current_user: dict = Depends(get_current_user), conn=Depends(get_db)):
    """Retrieves all pending incoming friend requests."""
    return crud.get_pending_friend_requests(conn, current_user["id"])


@router.get("/profile/{friend_id}", response_model=FriendProfileResponse)
def get_friend_profile(
    friend_id: int,
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db)
):
    """Retrieves profile stats for a friend."""
    profile = crud.get_friend_profile(conn, current_user["id"], friend_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Friend profile not found")
    return profile