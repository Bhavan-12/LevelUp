import datetime
from datetime import date, timedelta
import math
from typing import List, Dict, Any, Optional

def calculate_level(xp: int) -> int:
    """Calculates user level based on total XP: Level = floor(sqrt(XP / 25)) + 1"""
    return int(math.floor(math.sqrt(xp / 25.0))) + 1


def log_activity(conn, user_id: int, activity_type: str, title: str, description: str = ""):
    """Logs an event to the user's activity feed."""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO activity_logs (user_id, activity_type, title, description)
        VALUES (?, ?, ?, ?)
    """, (user_id, activity_type, title, description))


def award_xp(conn, user_id: int, xp_amount: int, source_description: str = "") -> dict:
    """Awards XP to a user, updates their level, and logs level-up events."""
    cursor = conn.cursor()
    cursor.execute("SELECT xp, level, username FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        return {"new_xp": 0, "new_level": 1, "level_up": False}

    old_xp = user["xp"]
    old_level = user["level"]
    new_xp = old_xp + xp_amount
    new_level = calculate_level(new_xp)
    level_up = new_level > old_level

    cursor.execute("UPDATE users SET xp = ?, level = ? WHERE id = ?", (new_xp, new_level, user_id))

    if level_up:
        log_activity(
            conn, user_id, "level_up",
            f"Leveled Up to Level {new_level}!",
            f"Earned {xp_amount} XP from {source_description}"
        )
        check_and_unlock_achievements(conn, user_id)

    return {"new_xp": new_xp, "new_level": new_level, "level_up": level_up}


def check_and_unlock_achievements(conn, user_id: int) -> List[str]:
    """Evaluates criteria for locked achievements and awards unlocked badges."""
    cursor = conn.cursor()
    unlocked_titles = []

    cursor.execute("SELECT xp, level, current_streak, longest_streak FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        return unlocked_titles

    cursor.execute("SELECT COUNT(*) as count FROM habits WHERE user_id = ? AND is_archived = 0", (user_id,))
    active_habits_count = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM habit_logs WHERE user_id = ? AND status = 'completed'", (user_id,))
    total_completions = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM friendships WHERE user_id_1 = ? OR user_id_2 = ?", (user_id, user_id))
    friends_count = cursor.fetchone()["count"]

    cursor.execute("SELECT * FROM achievements")
    achievements = cursor.fetchall()

    cursor.execute("SELECT achievement_id FROM user_achievements WHERE user_id = ?", (user_id,))
    unlocked_ids = {row["achievement_id"] for row in cursor.fetchall()}

    for ach in achievements:
        ach_id = ach["id"]
        if ach_id in unlocked_ids:
            continue

        code = ach["code"]
        should_unlock = False

        if code == "FIRST_STEP" and total_completions >= 1:
            should_unlock = True
        elif code == "HABIT_STARTER" and active_habits_count >= 3:
            should_unlock = True
        elif code == "STREAK_7" and (user["current_streak"] >= 7 or user["longest_streak"] >= 7):
            should_unlock = True
        elif code == "STREAK_30" and (user["current_streak"] >= 30 or user["longest_streak"] >= 30):
            should_unlock = True
        elif code == "CENTURY_CLUB" and total_completions >= 100:
            should_unlock = True
        elif code == "LEVEL_5" and user["level"] >= 5:
            should_unlock = True
        elif code == "LEVEL_10" and user["level"] >= 10:
            should_unlock = True
        elif code == "SOCIAL_BUTTERFLY" and friends_count >= 3:
            should_unlock = True

        if should_unlock:
            cursor.execute("INSERT INTO user_achievements (user_id, achievement_id) VALUES (?, ?)", (user_id, ach_id))
            unlocked_titles.append(ach["title"])
            award_xp(conn, user_id, ach["xp_reward"], f"Achievement: {ach['title']}")
            log_activity(conn, user_id, "achievement_unlocked", f"Unlocked Achievement: {ach['title']}", ach["description"])

    return unlocked_titles


def update_user_streaks(conn, user_id: int):
    """Recalculates the user's current daily streak and updates longest streak."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT log_date FROM habit_logs
        WHERE user_id = ? AND status = 'completed'
        ORDER BY log_date DESC
    """, (user_id,))
    rows = cursor.fetchall()

    if not rows:
        cursor.execute("UPDATE users SET current_streak = 0 WHERE id = ?", (user_id,))
        return

    log_dates = [datetime.datetime.strptime(row["log_date"], "%Y-%m-%d").date() for row in rows]
    today = date.today()
    yesterday = today - timedelta(days=1)

    if log_dates[0] < yesterday:
        current_streak = 0
    else:
        current_streak = 0
        check_date = log_dates[0]
        date_set = set(log_dates)
        while check_date in date_set:
            current_streak += 1
            check_date -= timedelta(days=1)

    cursor.execute("SELECT longest_streak FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    longest_streak = max(user["longest_streak"], current_streak)

    cursor.execute("UPDATE users SET current_streak = ?, longest_streak = ? WHERE id = ?", (current_streak, longest_streak, user_id))

