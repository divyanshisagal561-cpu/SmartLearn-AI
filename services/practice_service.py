from services.ai_service import generate_personalized_practice
from services.analysis_service import calculate_next_difficulty
from database.db import get_db
import json

def generate_personalized_practice_for_user(user_id, attempt_id=None):
    conn = get_db()
    cursor = conn.cursor()
    
    # Get user details
    cursor.execute("SELECT class_level, language FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    class_level = user["class_level"] if user else "Class 10"
    language = user["language"] if (user and "language" in user.keys()) else "English"
    
    subject = "Mathematics"
    topic = "General Revision"
    weak_concepts = []
    target_difficulty = "Basic"
    
    if attempt_id:
        cursor.execute("SELECT * FROM quiz_attempts WHERE id = ?", (attempt_id,))
        attempt = cursor.fetchone()
        if attempt:
            subject = attempt["subject"]
            topic = attempt["topic"]
            score = attempt["score"]
            target_difficulty, _ = calculate_next_difficulty(score)
            try:
                weak_concepts = json.loads(attempt["weak_concepts"])
            except:
                weak_concepts = []
    else:
        # Get latest attempt for user
        cursor.execute("SELECT * FROM quiz_attempts WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", (user_id,))
        attempt = cursor.fetchone()
        if attempt:
            subject = attempt["subject"]
            topic = attempt["topic"]
            score = attempt["score"]
            target_difficulty, _ = calculate_next_difficulty(score)
            try:
                weak_concepts = json.loads(attempt["weak_concepts"])
            except:
                weak_concepts = []

    conn.close()
    
    quiz_data = generate_personalized_practice(
        class_level=class_level,
        subject=subject,
        topic=topic,
        weak_concepts=weak_concepts,
        target_difficulty=target_difficulty,
        num_questions=5,
        language=language
    )
    
    return {
        "subject": subject,
        "topic": topic,
        "difficulty": target_difficulty,
        "weak_concepts": weak_concepts,
        "questions": quiz_data.get("questions", [])
    }
