from pydantic import BaseModel, Field
from typing import Optional, List, Any


class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    email: str
    password: str = Field(..., min_length=6)
    bio: Optional[str] = ""
    avatar_url: Optional[str] = "avatar-1"

class UserLogin(BaseModel):
    username_or_email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class UserUpdate(BaseModel):
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    theme_preference: Optional[str] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)

class UserProfileResponse(BaseModel):
    id: int
    username: str
    email: str
    bio: str
    avatar_url: str
    theme_preference: str
    xp: int
    level: int
    current_streak: int
    longest_streak: int
    created_at: str
    total_habits: Optional[int] = 0
    completed_today: Optional[int] = 0
    total_completions: Optional[int] = 0
    overall_completion_rate: Optional[float] = 0.0


class HabitCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = ""
    frequency: str = "daily"  # daily, weekly, monthly
    category: str = "General"
    color: Optional[str] = "#4f46e5"
    icon: Optional[str] = "bi-check-circle"
    priority: Optional[str] = "medium"  # low, medium, high
    notes: Optional[str] = ""

class HabitUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    frequency: Optional[str] = None
    category: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    priority: Optional[str] = None
    notes: Optional[str] = None
    is_archived: Optional[bool] = None

class HabitResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: str
    frequency: str
    category: str
    color: str
    icon: str
    priority: str
    notes: str
    is_archived: bool
    created_at: str
    is_completed_today: bool = False
    today_status: Optional[str] = None  # completed, missed, skipped, null
    missed_reason: Optional[str] = None
    current_streak: int = 0
    longest_streak: int = 0
    total_completions: int = 0
    completion_rate: float = 0.0



class CheckInRequest(BaseModel):
    habit_id: int
    log_date: Optional[str] = None  # YYYY-MM-DD
    status: str  # completed, missed, skipped
    reason: Optional[str] = ""

class CheckInResponse(BaseModel):
    success: bool
    status: str
    xp_earned: int
    new_xp: int
    new_level: int
    level_up: bool
    current_streak: int
    message: str

class HabitLogResponse(BaseModel):
    id: int
    habit_id: int
    log_date: str
    status: str
    reason: str
    xp_earned: int
    created_at: str


class UserSearchResponse(BaseModel):
    id: int
    username: str
    bio: str
    avatar_url: str
    level: int
    xp: int
    friendship_status: str  # 'none', 'friends', 'pending_sent', 'pending_received'

class FriendRequestCreate(BaseModel):
    receiver_id: int

class FriendRequestAction(BaseModel):
    request_id: int

class FriendProfileResponse(BaseModel):
    id: int
    username: str
    bio: str
    avatar_url: str
    level: int
    xp: int
    current_streak: int
    longest_streak: int
    active_habits_count: int
    total_completions: int
    friendship_status: str

class AchievementResponse(BaseModel):
    id: int
    code: str
    title: str
    description: str
    icon: str
    badge_color: str
    xp_reward: int
    category: str
    unlocked: bool
    unlocked_at: Optional[str] = None

class ChallengeResponse(BaseModel):
    id: int
    title: str
    description: str
    type: str
    target_count: int
    xp_reward: int
    icon: str
    progress: int
    completed: bool

class ActivityLogResponse(BaseModel):
    id: int
    activity_type: str
    title: str
    description: str
    created_at: str

class AnalyticsSummary(BaseModel):
    total_habits: int
    completed_today: int
    today_completion_rate: float
    current_streak: int
    longest_streak: int
    total_checkins: int
    total_xp: int
    level: int

class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    username: str
    avatar_url: str
    level: int
    score_value: Any
    metric_label: str
    is_current_user: bool = False