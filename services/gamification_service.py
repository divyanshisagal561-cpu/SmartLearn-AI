from database.db import get_db

BADGES = {
    "first_quiz": {"name": "First Quiz Completed", "desc": "Completed your very first AI Quiz!", "icon": "🏅"},
    "streak_3": {"name": "3-Day Streak", "desc": "Maintained a 3-day active learning streak!", "icon": "🔥"},
    "weakness_crusher": {"name": "Weakness Crusher", "desc": "Completed a targeted personalized practice set!", "icon": "🎯"},
    "quiz_10": {"name": "10 Quizzes Completed", "desc": "Showed dedication by completing 10 quizzes!", "icon": "📚"},
    "improvement_star": {"name": "Improvement Star", "desc": "Scored 80% or higher on a quiz!", "icon": "🚀"},
    "high_score": {"name": "High Score", "desc": "Achieved a perfect 100% score!", "icon": "🏆"}
}

def get_user_level(xp):
    if xp < 150:
        return "Learner", 1, 150
    elif xp < 400:
        return "Explorer", 2, 400
    elif xp < 800:
        return "Achiever", 3, 800
    else:
        return "Scholar", 4, 1500


def award_quiz_rewards(user_id, score_pct, is_practice=0):
    conn = get_db()
    cursor = conn.cursor()
    
    # Calculate XP
    base_xp = 75 if is_practice else 50
    score_bonus = int(score_pct * 0.5) # Up to +50 XP bonus for high score
    total_xp_earned = base_xp + score_bonus
    
    # Update user XP
    cursor.execute("UPDATE users SET xp = xp + ? WHERE id = ?", (total_xp_earned, user_id))
    
    # Check total quizzes completed for badge evaluations
    cursor.execute("SELECT COUNT(*) as cnt FROM quiz_attempts WHERE user_id = ?", (user_id,))
    total_quizzes = cursor.fetchone()["cnt"]
    
    cursor.execute("SELECT streak FROM users WHERE id = ?", (user_id,))
    user_row = cursor.fetchone()
    streak = user_row["streak"] if user_row else 1
    
    unlocked_badges = []
    
    # Check First Quiz
    if total_quizzes >= 1:
        unlocked_badges.append("first_quiz")
        
    # Check 10 Quizzes
    if total_quizzes >= 10:
        unlocked_badges.append("quiz_10")
        
    # Check Practice set badge
    if is_practice:
        unlocked_badges.append("weakness_crusher")
        
    # Check Score badges
    if score_pct >= 80:
        unlocked_badges.append("improvement_star")
    if score_pct >= 100:
        unlocked_badges.append("high_score")
        
    # Check Streak badge
    if streak >= 3:
        unlocked_badges.append("streak_3")
        
    # Insert badges into DB if not already unlocked
    newly_unlocked = []
    for code in unlocked_badges:
        cursor.execute("SELECT id FROM achievements WHERE user_id = ? AND badge_code = ?", (user_id, code))
        if not cursor.fetchone():
            b_info = BADGES[code]
            cursor.execute("""
                INSERT INTO achievements (user_id, badge_code, badge_name, description, icon)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, code, b_info["name"], b_info["desc"], b_info["icon"]))
            newly_unlocked.append(b_info)
            
    conn.commit()
    conn.close()
    
    return total_xp_earned, newly_unlocked


def get_user_achievements(user_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT badge_code FROM achievements WHERE user_id = ?", (user_id,))
    unlocked_codes = set([r["badge_code"] for r in cursor.fetchall()])
    
    all_achievements = []
    for code, info in BADGES.items():
        all_achievements.append({
            "code": code,
            "name": info["name"],
            "description": info["desc"],
            "icon": info["icon"],
            "is_unlocked": code in unlocked_codes
        })
        
    conn.close()
    return all_achievements
