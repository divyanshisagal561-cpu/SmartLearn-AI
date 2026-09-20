from database.db import get_db
import json

def calculate_next_difficulty(score_pct, current_difficulty="Adaptive"):
    """
    Adaptive Threshold prototype rules:
    0–40%    → Beginner
    41–60%   → Basic
    61–80%   → Intermediate
    81–100%  → Advanced
    """
    if score_pct <= 40.0:
        next_diff = "Beginner"
        reason = "Let's strengthen the fundamental concepts before moving to more difficult questions."
    elif score_pct <= 60.0:
        next_diff = "Basic"
        reason = "You have a solid foundation! Practice a bit more at the Basic level to build confidence."
    elif score_pct <= 80.0:
        next_diff = "Intermediate"
        reason = "Good performance! Moving up to Intermediate level for standard problem solving."
    else:
        next_diff = "Advanced"
        reason = "Outstanding score! Your recent performance supports moving to challenging application-based questions."
        
    return next_diff, reason


def get_user_performance_summary(user_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM quiz_attempts WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    attempts = cursor.fetchall()
    
    total_quizzes = len(attempts)
    if total_quizzes == 0:
        conn.close()
        return {
            "quizzes_completed": 0,
            "avg_score": 0.0,
            "highest_score": 0.0,
            "current_level": "Beginner",
            "weak_concepts": [],
            "strong_concepts": [],
            "recent_attempts": []
        }
        
    scores = [a["score"] for a in attempts]
    avg_score = round(sum(scores) / total_quizzes, 1)
    highest_score = round(max(scores), 1)
    
    # Calculate current level based on recent average score
    recent_scores = scores[:3]
    recent_avg = sum(recent_scores) / len(recent_scores)
    current_level, _ = calculate_next_difficulty(recent_avg)
    
    # Aggregate weak and strong concepts across recent attempts
    all_weak = []
    all_strong = []
    
    for a in attempts[:10]: # Look at recent 10 attempts
        try:
            w = json.loads(a["weak_concepts"])
            all_weak.extend(w)
        except:
            pass
        try:
            s = json.loads(a["strong_concepts"])
            all_strong.extend(s)
        except:
            pass
            
    # Deduplicate while preserving order of frequency
    unique_weak = list(dict.fromkeys(all_weak))
    unique_strong = list(dict.fromkeys(all_strong))
    
    # Remove concepts from weak if they became strong in recent attempt
    if len(attempts) > 0:
        try:
            latest_strong = json.loads(attempts[0]["strong_concepts"])
            unique_weak = [c for c in unique_weak if c not in latest_strong]
        except:
            pass

    conn.close()
    
    return {
        "quizzes_completed": total_quizzes,
        "avg_score": avg_score,
        "highest_score": highest_score,
        "current_level": current_level,
        "weak_concepts": unique_weak[:5],
        "strong_concepts": unique_strong[:5],
        "recent_attempts": [dict(a) for a in attempts[:5]]
    }
