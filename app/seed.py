from app.database import db_session

def seed_initial_data():
    """Seeds default achievements, badges, and challenges into the database."""
    with db_session() as conn:
        cursor = conn.cursor()
        
        # 1. Initial Achievements & Badges
        achievements = [
            ("FIRST_STEP", "First Step", "Complete your first habit check-in.", "bi-award", "#10b981", 50, "general"),
            ("HABIT_STARTER", "Habit Starter", "Create 3 active habits in your routine.", "bi-plus-circle", "#3b82f6", 75, "habits"),
            ("STREAK_7", "On Fire!", "Reach a 7-day streak on your habits.", "bi-fire", "#f97316", 150, "streaks"),
            ("STREAK_30", "Unstoppable", "Reach an impressive 30-day streak.", "bi-lightning-charge", "#eab308", 300, "streaks"),
            ("CENTURY_CLUB", "Century Club", "Log 100 total habit completions.", "bi-trophy", "#a855f7", 500, "milestones"),
            ("LEVEL_5", "Level 5 Champion", "Reach Level 5 on LevelUp.", "bi-star", "#ec4899", 200, "level"),
            ("LEVEL_10", "Grandmaster", "Reach Level 10 on LevelUp.", "bi-gem", "#06b6d4", 500, "level"),
            ("SOCIAL_BUTTERFLY", "Social Butterfly", "Connect with 3 friends on LevelUp.", "bi-people", "#6366f1", 100, "social")
        ]
        
        for ach in achievements:
            cursor.execute("""
                INSERT INTO achievements (code, title, description, icon, badge_color, xp_reward, category)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(code) DO UPDATE SET
                    title = excluded.title,
                    description = excluded.description,
                    icon = excluded.icon,
                    badge_color = excluded.badge_color,
                    xp_reward = excluded.xp_reward,
                    category = excluded.category
            """, ach)