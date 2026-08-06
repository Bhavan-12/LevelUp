import datetime
from datetime import date, timedelta
import math
from typing import List, Dict, Any, Optional

# ==========================================
# 1. GAMIFICATION ENGINE & HELPERS
# ==========================================

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


# ==========================================
# 2. USER OPERATIONS
# ==========================================

def create_user(conn, username: str, email: str, hashed_password: str, bio: str = "", avatar_url: str = "avatar-1") -> dict:
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (username, email, hashed_password, bio, avatar_url)
        VALUES (?, ?, ?, ?, ?)
    """, (username, email, hashed_password, bio, avatar_url))
    user_id = cursor.lastrowid
    log_activity(conn, user_id, "welcome", "Joined LevelUp!", "Started your journey to building better habits.")
    seed_user_challenges(conn, user_id)
    return get_user_by_id(conn, user_id)


def get_user_by_id(conn, user_id: int) -> Optional[dict]:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        return None
    user_dict = dict(user)

    cursor.execute("SELECT COUNT(*) as cnt FROM habits WHERE user_id = ? AND is_archived = 0", (user_id,))
    user_dict["total_habits"] = cursor.fetchone()["cnt"]

    today_str = date.today().isoformat()
    cursor.execute("""
        SELECT COUNT(*) as cnt FROM habit_logs
        WHERE user_id = ? AND log_date = ? AND status = 'completed'
    """, (user_id, today_str))
    user_dict["completed_today"] = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) as cnt FROM habit_logs WHERE user_id = ? AND status = 'completed'", (user_id,))
    user_dict["total_completions"] = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) as cnt FROM habit_logs WHERE user_id = ?", (user_id,))
    total_logs = cursor.fetchone()["cnt"]
    user_dict["overall_completion_rate"] = round((user_dict["total_completions"] / total_logs * 100), 1) if total_logs > 0 else 0.0

    return user_dict


def get_user_by_username_or_email(conn, identifier: str) -> Optional[dict]:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? OR email = ?", (identifier, identifier))
    user = cursor.fetchone()
    return dict(user) if user else None


def update_user_profile(conn, user_id: int, bio: Optional[str] = None, avatar_url: Optional[str] = None, theme_preference: Optional[str] = None) -> dict:
    cursor = conn.cursor()
    fields = []
    values = []
    if bio is not None:
        fields.append("bio = ?")
        values.append(bio)
    if avatar_url is not None:
        fields.append("avatar_url = ?")
        values.append(avatar_url)
    if theme_preference is not None:
        fields.append("theme_preference = ?")
        values.append(theme_preference)

    if fields:
        values.append(user_id)
        query = f"UPDATE users SET {', '.join(fields)} WHERE id = ?"
        cursor.execute(query, tuple(values))

    return get_user_by_id(conn, user_id)


# ==========================================
# 3. HABIT OPERATIONS
# ==========================================

def create_habit(conn, user_id: int, habit_data: dict) -> dict:
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO habits (user_id, title, description, frequency, category, color, icon, priority, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        habit_data.get("title"),
        habit_data.get("description", ""),
        habit_data.get("frequency", "daily"),
        habit_data.get("category", "General"),
        habit_data.get("color", "#4f46e5"),
        habit_data.get("icon", "bi-check-circle"),
        habit_data.get("priority", "medium"),
        habit_data.get("notes", "")
    ))
    habit_id = cursor.lastrowid
    log_activity(conn, user_id, "habit_created", f"Created new habit: {habit_data.get('title')}")
    check_and_unlock_achievements(conn, user_id)
    return get_habit_by_id(conn, habit_id, user_id)


def get_habits_by_user(conn, user_id: int, category: Optional[str] = None, include_archived: bool = False) -> List[dict]:
    cursor = conn.cursor()
    query = "SELECT * FROM habits WHERE user_id = ?"
    params = [user_id]

    if not include_archived:
        query += " AND is_archived = 0"
    if category and category != "All":
        query += " AND category = ?"
        params.append(category)

    query += " ORDER BY id DESC"
    cursor.execute(query, tuple(params))
    habits = [dict(row) for row in cursor.fetchall()]

    today_str = date.today().isoformat()
    for h in habits:
        h_id = h["id"]
        cursor.execute("SELECT status, reason FROM habit_logs WHERE habit_id = ? AND log_date = ?", (h_id, today_str))
        log = cursor.fetchone()
        if log:
            h["is_completed_today"] = (log["status"] == "completed")
            h["today_status"] = log["status"]
            h["missed_reason"] = log["reason"]
        else:
            h["is_completed_today"] = False
            h["today_status"] = None
            h["missed_reason"] = None

        cursor.execute("SELECT log_date FROM habit_logs WHERE habit_id = ? AND status = 'completed' ORDER BY log_date DESC", (h_id,))
        logs = cursor.fetchall()
        if not logs:
            h["current_streak"] = 0
            h["longest_streak"] = 0
            h["total_completions"] = 0
            h["completion_rate"] = 0.0
        else:
            h["total_completions"] = len(logs)
            log_dates = [datetime.datetime.strptime(l["log_date"], "%Y-%m-%d").date() for l in logs]
            cur_streak = 0
            check_d = date.today()
            date_set = set(log_dates)
            if check_d not in date_set and (check_d - timedelta(days=1)) in date_set:
                check_d = check_d - timedelta(days=1)
            while check_d in date_set:
                cur_streak += 1
                check_d -= timedelta(days=1)
            h["current_streak"] = cur_streak
            h["longest_streak"] = cur_streak

            cursor.execute("SELECT COUNT(*) as total FROM habit_logs WHERE habit_id = ?", (h_id,))
            tot = cursor.fetchone()["total"]
            h["completion_rate"] = round((h["total_completions"] / tot * 100), 1) if tot > 0 else 0.0

    return habits


def get_habit_by_id(conn, habit_id: int, user_id: int) -> Optional[dict]:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM habits WHERE id = ? AND user_id = ?", (habit_id, user_id))
    row = cursor.fetchone()
    if not row:
        return None
    h = dict(row)
    today_str = date.today().isoformat()
    cursor.execute("SELECT status, reason FROM habit_logs WHERE habit_id = ? AND log_date = ?", (habit_id, today_str))
    log = cursor.fetchone()
    h["is_completed_today"] = (log["status"] == "completed") if log else False
    h["today_status"] = log["status"] if log else None
    h["missed_reason"] = log["reason"] if log else None
    return h


def update_habit(conn, habit_id: int, user_id: int, update_data: dict) -> Optional[dict]:
    cursor = conn.cursor()
    fields = []
    values = []
    for k, v in update_data.items():
        if v is not None:
            fields.append(f"{k} = ?")
            values.append(v)

    if not fields:
        return get_habit_by_id(conn, habit_id, user_id)

    values.extend([habit_id, user_id])
    query = f"UPDATE habits SET {', '.join(fields)} WHERE id = ? AND user_id = ?"
    cursor.execute(query, tuple(values))
    return get_habit_by_id(conn, habit_id, user_id)


def delete_habit(conn, habit_id: int, user_id: int) -> bool:
    cursor = conn.cursor()
    cursor.execute("DELETE FROM habits WHERE id = ? AND user_id = ?", (habit_id, user_id))
    return cursor.rowcount > 0


# ==========================================
# 4. TRACKING OPERATIONS
# ==========================================

def log_habit_checkin(conn, user_id: int, habit_id: int, log_date: str, status: str, reason: str = "") -> dict:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM habits WHERE id = ? AND user_id = ?", (habit_id, user_id))
    habit = cursor.fetchone()
    if not habit:
        return {"success": False, "message": "Habit not found or unauthorized"}

    if not log_date:
        log_date = date.today().isoformat()

    xp_earned = 0
    if status == "completed":
        xp_earned = 15  # 15 XP base reward
        cursor.execute("SELECT current_streak FROM users WHERE id = ?", (user_id,))
        streak = cursor.fetchone()["current_streak"]
        if streak >= 3:
            xp_earned += 10  # 10 XP streak bonus

    cursor.execute("""
        INSERT INTO habit_logs (habit_id, user_id, log_date, status, reason, xp_earned)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(habit_id, log_date) DO UPDATE SET
            status = excluded.status,
            reason = excluded.reason,
            xp_earned = excluded.xp_earned
    """, (habit_id, user_id, log_date, status, reason, xp_earned))

    xp_res = {"new_xp": 0, "new_level": 1, "level_up": False}
    if xp_earned > 0:
        xp_res = award_xp(conn, user_id, xp_earned, f"Habit: {habit['title']}")
        log_activity(conn, user_id, "habit_completed", f"Completed: {habit['title']}", f"+{xp_earned} XP earned")

    update_user_streaks(conn, user_id)
    update_challenge_progress(conn, user_id, status)
    check_and_unlock_achievements(conn, user_id)

    cursor.execute("SELECT current_streak, xp, level FROM users WHERE id = ?", (user_id,))
    u_info = cursor.fetchone()

    return {
        "success": True,
        "status": status,
        "xp_earned": xp_earned,
        "new_xp": u_info["xp"],
        "new_level": u_info["level"],
        "level_up": xp_res["level_up"],
        "current_streak": u_info["current_streak"],
        "message": f"Habit marked as {status}!"
    }


# ==========================================
# 5. SOCIAL OPERATIONS
# ==========================================

def search_users(conn, current_user_id: int, query: str) -> List[dict]:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, bio, avatar_url, level, xp FROM users
        WHERE username LIKE ? AND id != ? LIMIT 20
    """, (f"%{query}%", current_user_id))
    users = [dict(row) for row in cursor.fetchall()]

    for u in users:
        u_id = u["id"]
        cursor.execute("""
            SELECT id FROM friendships
            WHERE (user_id_1 = ? AND user_id_2 = ?) OR (user_id_1 = ? AND user_id_2 = ?)
        """, (current_user_id, u_id, u_id, current_user_id))
        if cursor.fetchone():
            u["friendship_status"] = "friends"
            continue

        cursor.execute("""
            SELECT status, sender_id FROM friend_requests
            WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)
        """, (current_user_id, u_id, u_id, current_user_id))
        req = cursor.fetchone()
        if req:
            if req["sender_id"] == current_user_id:
                u["friendship_status"] = "pending_sent"
            else:
                u["friendship_status"] = "pending_received"
        else:
            u["friendship_status"] = "none"

    return users


def send_friend_request(conn, sender_id: int, receiver_id: int) -> dict:
    if sender_id == receiver_id:
        return {"success": False, "message": "Cannot send friend request to yourself"}
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO friend_requests (sender_id, receiver_id, status)
        VALUES (?, ?, 'pending')
        ON CONFLICT(sender_id, receiver_id) DO UPDATE SET status = 'pending'
    """, (sender_id, receiver_id))
    return {"success": True, "message": "Friend request sent"}


def respond_friend_request(conn, user_id: int, request_id: int, action: str) -> dict:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM friend_requests WHERE id = ? AND receiver_id = ?", (request_id, user_id))
    req = cursor.fetchone()
    if not req:
        return {"success": False, "message": "Request not found"}

    sender_id = req["sender_id"]
    if action == "accept":
        cursor.execute("UPDATE friend_requests SET status = 'accepted' WHERE id = ?", (request_id,))
        u1, u2 = min(sender_id, user_id), max(sender_id, user_id)
        cursor.execute("INSERT OR IGNORE INTO friendships (user_id_1, user_id_2) VALUES (?, ?)", (u1, u2))

        log_activity(conn, user_id, "social", "New Friend Added!", "You are now connected.")
        log_activity(conn, sender_id, "social", "New Friend Added!", "Friend request was accepted.")

        check_and_unlock_achievements(conn, user_id)
        check_and_unlock_achievements(conn, sender_id)
        return {"success": True, "message": "Friend request accepted"}
    else:
        cursor.execute("DELETE FROM friend_requests WHERE id = ?", (request_id,))
        return {"success": True, "message": "Friend request rejected"}


def get_friends_list(conn, user_id: int) -> List[dict]:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.username, u.bio, u.avatar_url, u.level, u.xp, u.current_streak, u.longest_streak
        FROM users u
        JOIN friendships f ON (f.user_id_1 = u.id OR f.user_id_2 = u.id)
        WHERE (f.user_id_1 = ? OR f.user_id_2 = ?) AND u.id != ?
    """, (user_id, user_id, user_id))
    friends = [dict(row) for row in cursor.fetchall()]

    for f in friends:
        cursor.execute("SELECT COUNT(*) as cnt FROM habits WHERE user_id = ? AND is_archived = 0", (f["id"],))
        f["active_habits_count"] = cursor.fetchone()["cnt"]

    return friends


def get_pending_friend_requests(conn, user_id: int) -> List[dict]:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT fr.id, fr.sender_id, fr.created_at, u.username as sender_username, u.avatar_url as sender_avatar, u.level as sender_level
        FROM friend_requests fr
        JOIN users u ON u.id = fr.sender_id
        WHERE fr.receiver_id = ? AND fr.status = 'pending'
    """, (user_id,))
    return [dict(row) for row in cursor.fetchall()]


def get_friend_profile(conn, current_user_id: int, friend_id: int) -> Optional[dict]:
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, bio, avatar_url, level, xp, current_streak, longest_streak FROM users WHERE id = ?", (friend_id,))
    friend = cursor.fetchone()
    if not friend:
        return None

    f_dict = dict(friend)
    cursor.execute("SELECT COUNT(*) as cnt FROM habits WHERE user_id = ? AND is_archived = 0", (friend_id,))
    f_dict["active_habits_count"] = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) as cnt FROM habit_logs WHERE user_id = ? AND status = 'completed'", (friend_id,))
    f_dict["total_completions"] = cursor.fetchone()["cnt"]
    f_dict["friendship_status"] = "friends"
    return f_dict


# ==========================================
# 6. LEADERBOARD OPERATIONS
# ==========================================

def get_leaderboard(conn, current_user_id: int, timeframe: str = "all_time", metric: str = "xp", filter_friends: bool = False) -> List[dict]:
    cursor = conn.cursor()
    user_ids = []
    if filter_friends:
        friends = get_friends_list(conn, current_user_id)
        user_ids = [f["id"] for f in friends]
        user_ids.append(current_user_id)

    if metric == "xp":
        query = "SELECT id, username, avatar_url, level, xp as score_value FROM users"
        if user_ids:
            query += f" WHERE id IN ({','.join(str(i) for i in user_ids)})"
        query += " ORDER BY xp DESC LIMIT 50"
        cursor.execute(query)
        rows = cursor.fetchall()
    elif metric == "streak":
        query = "SELECT id, username, avatar_url, level, current_streak as score_value FROM users"
        if user_ids:
            query += f" WHERE id IN ({','.join(str(i) for i in user_ids)})"
        query += " ORDER BY current_streak DESC, xp DESC LIMIT 50"
        cursor.execute(query)
        rows = cursor.fetchall()
    elif metric == "completion_rate":
        date_limit = None
        today = date.today()
        if timeframe == "weekly":
            date_limit = (today - timedelta(days=7)).isoformat()
        elif timeframe == "monthly":
            date_limit = (today - timedelta(days=30)).isoformat()

        sql = """
            SELECT u.id, u.username, u.avatar_url, u.level,
                   COUNT(CASE WHEN hl.status = 'completed' THEN 1 END) as completed_cnt,
                   COUNT(hl.id) as total_cnt
            FROM users u
            LEFT JOIN habit_logs hl ON hl.user_id = u.id
        """
        conditions = []
        if date_limit:
            conditions.append(f"hl.log_date >= '{date_limit}'")
        if user_ids:
            conditions.append(f"u.id IN ({','.join(str(i) for i in user_ids)})")

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        sql += " GROUP BY u.id ORDER BY (CASE WHEN COUNT(hl.id) > 0 THEN (COUNT(CASE WHEN hl.status = 'completed' THEN 1 END) * 100.0 / COUNT(hl.id)) ELSE 0 END) DESC LIMIT 50"
        cursor.execute(sql)
        raw_rows = cursor.fetchall()

        results = []
        for rank, r in enumerate(raw_rows, start=1):
            tot = r["total_cnt"]
            rate = round((r["completed_cnt"] / tot * 100), 1) if tot > 0 else 0.0
            results.append({
                "rank": rank,
                "user_id": r["id"],
                "username": r["username"],
                "avatar_url": r["avatar_url"],
                "level": r["level"],
                "score_value": f"{rate}%",
                "metric_label": "Completion Rate",
                "is_current_user": (r["id"] == current_user_id)
            })
        return results

    results = []
    metric_map = {"xp": "XP", "streak": "Days"}
    for rank, r in enumerate(rows, start=1):
        results.append({
            "rank": rank,
            "user_id": r["id"],
            "username": r["username"],
            "avatar_url": r["avatar_url"],
            "level": r["level"],
            "score_value": f"{r['score_value']} {metric_map.get(metric, '')}",
            "metric_label": metric.upper(),
            "is_current_user": (r["id"] == current_user_id)
        })

    return results


# ==========================================
# 7. GAMIFICATION & CHALLENGES OPERATIONS
# ==========================================

def seed_user_challenges(conn, user_id: int):
    cursor = conn.cursor()
    today_str = date.today().isoformat()
    cursor.execute("SELECT id FROM challenges")
    challenges = cursor.fetchall()
    for ch in challenges:
        cursor.execute("""
            INSERT OR IGNORE INTO user_challenges (user_id, challenge_id, progress, completed, assigned_date)
            VALUES (?, ?, 0, 0, ?)
        """, (user_id, ch["id"], today_str))


def update_challenge_progress(conn, user_id: int, status: str):
    if status != "completed":
        return
    cursor = conn.cursor()
    today_str = date.today().isoformat()
    cursor.execute("""
        SELECT uc.id, uc.progress, uc.completed, c.target_count, c.xp_reward, c.title
        FROM user_challenges uc
        JOIN challenges c ON c.id = uc.challenge_id
        WHERE uc.user_id = ? AND uc.assigned_date = ? AND uc.completed = 0
    """, (user_id, today_str))
    user_challenges = cursor.fetchall()

    for uc in user_challenges:
        new_prog = uc["progress"] + 1
        is_completed = new_prog >= uc["target_count"]
        cursor.execute("UPDATE user_challenges SET progress = ?, completed = ? WHERE id = ?", (new_prog, is_completed, uc["id"]))
        if is_completed:
            award_xp(conn, user_id, uc["xp_reward"], f"Challenge: {uc['title']}")
            log_activity(conn, user_id, "challenge_completed", f"Challenge Completed: {uc['title']}", f"+{uc['xp_reward']} XP Reward")


def get_user_achievements(conn, user_id: int) -> List[dict]:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.*, CASE WHEN ua.id IS NOT NULL THEN 1 ELSE 0 END as unlocked, ua.unlocked_at
        FROM achievements a
        LEFT JOIN user_achievements ua ON ua.achievement_id = a.id AND ua.user_id = ?
        ORDER BY a.id ASC
    """, (user_id,))
    return [dict(row) for row in cursor.fetchall()]


def get_user_challenges(conn, user_id: int) -> List[dict]:
    seed_user_challenges(conn, user_id)
    cursor = conn.cursor()
    today_str = date.today().isoformat()
    cursor.execute("""
        SELECT c.id, c.title, c.description, c.type, c.target_count, c.xp_reward, c.icon, uc.progress, uc.completed
        FROM user_challenges uc
        JOIN challenges c ON c.id = uc.challenge_id
        WHERE uc.user_id = ? AND uc.assigned_date = ?
    """, (user_id, today_str))
    return [dict(row) for row in cursor.fetchall()]


def get_recent_activity(conn, user_id: int, limit: int = 10) -> List[dict]:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM activity_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT ?
    """, (user_id, limit))
    return [dict(row) for row in cursor.fetchall()]


# ==========================================
# 8. ANALYTICS OPERATIONS
# ==========================================

def get_analytics_summary(conn, user_id: int) -> dict:
    user = get_user_by_id(conn, user_id)
    today_str = date.today().isoformat()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as cnt FROM habits WHERE user_id = ? AND is_archived = 0", (user_id,))
    total_habits = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) as cnt FROM habit_logs WHERE user_id = ? AND log_date = ? AND status = 'completed'", (user_id, today_str))
    completed_today = cursor.fetchone()["cnt"]

    today_rate = round((completed_today / total_habits * 100), 1) if total_habits > 0 else 0.0

    cursor.execute("SELECT COUNT(*) as cnt FROM habit_logs WHERE user_id = ? AND status = 'completed'", (user_id,))
    total_checkins = cursor.fetchone()["cnt"]

    return {
        "total_habits": total_habits,
        "completed_today": completed_today,
        "today_completion_rate": today_rate,
        "current_streak": user["current_streak"],
        "longest_streak": user["longest_streak"],
        "total_checkins": total_checkins,
        "total_xp": user["xp"],
        "level": user["level"]
    }


def get_weekly_analytics(conn, user_id: int) -> dict:
    cursor = conn.cursor()
    today = date.today()
    day_names = []
    completions_by_day = []

    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        d_str = d.isoformat()
        day_names.append(d.strftime("%a"))
        cursor.execute("SELECT COUNT(*) as cnt FROM habit_logs WHERE user_id = ? AND log_date = ? AND status = 'completed'", (user_id, d_str))
        cnt = cursor.fetchone()["cnt"]
        completions_by_day.append(cnt)

    return {
        "day_names": day_names,
        "completions_by_day": completions_by_day
    }


def get_category_breakdown(conn, user_id: int) -> List[dict]:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT category, COUNT(*) as habit_count FROM habits
        WHERE user_id = ? AND is_archived = 0 GROUP BY category
    """, (user_id,))
    cats = cursor.fetchall()

    result = []
    for c in cats:
        cat_name = c["category"]
        cursor.execute("""
            SELECT COUNT(hl.id) as completion_count FROM habit_logs hl
            JOIN habits h ON h.id = hl.habit_id
            WHERE hl.user_id = ? AND h.category = ? AND hl.status = 'completed'
        """, (user_id, cat_name))
        comp = cursor.fetchone()["completion_count"]
        result.append({
            "category": cat_name,
            "habit_count": c["habit_count"],
            "completion_count": comp
        })

    return result


def get_habit_heatmap(conn, user_id: int, days: int = 60) -> List[dict]:
    cursor = conn.cursor()
    today = date.today()
    heatmap = []

    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        d_str = d.isoformat()
        cursor.execute("SELECT COUNT(*) as cnt FROM habit_logs WHERE user_id = ? AND log_date = ? AND status = 'completed'", (user_id, d_str))
        cnt = cursor.fetchone()["cnt"]

        lvl = 0
        if cnt >= 7:
            lvl = 4
        elif cnt >= 5:
            lvl = 3
        elif cnt >= 3:
            lvl = 2
        elif cnt >= 1:
            lvl = 1

        heatmap.append({
            "date": d_str,
            "count": cnt,
            "level": lvl
        })

    return heatmap