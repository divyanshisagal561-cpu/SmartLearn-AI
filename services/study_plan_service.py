import json
from database.db import get_db
from services.ai_service import generate_study_plan

def create_user_study_plan(user_id, duration_days=7):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT class_level, language FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    class_level = user["class_level"] if user else "Class 10"
    language = user["language"] if (user and "language" in user.keys()) else "English"
    
    # Collect weak concepts and recent subjects
    cursor.execute("SELECT subject, topic, weak_concepts FROM quiz_attempts WHERE user_id = ? ORDER BY created_at DESC LIMIT 5", (user_id,))
    attempts = cursor.fetchall()
    
    weak_concepts = []
    subjects_topics = set()
    
    for a in attempts:
        subjects_topics.add(f"{a['subject']} ({a['topic']})")
        try:
            w = json.loads(a["weak_concepts"])
            weak_concepts.extend(w)
        except:
            pass
            
    unique_weak = list(dict.fromkeys(weak_concepts))
    subject_str = ", ".join(list(subjects_topics)) if subjects_topics else "Mathematics & Science"
    
    plan_data = generate_study_plan(class_level, duration_days, unique_weak, subject_str, language)
    
    # Save plan to database
    cursor.execute("""
        INSERT INTO study_plans (user_id, duration, plan_data_json)
        VALUES (?, ?, ?)
    """, (user_id, duration_days, json.dumps(plan_data)))
    
    plan_id = cursor.lastrowid
    
    # Insert individual tasks into study_plan_tasks
    days = plan_data.get("days", [])
    for d in days:
        cursor.execute("""
            INSERT INTO study_plan_tasks (plan_id, user_id, day_number, title, description, concept, is_completed)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        """, (
            plan_id,
            user_id,
            d.get("day_number", 1),
            d.get("title", "Study Task"),
            d.get("description", "Complete practice exercises."),
            d.get("concept", "General"),
        ))
        
    conn.commit()
    conn.close()
    
    return plan_id, plan_data


def get_latest_user_study_plan(user_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM study_plans WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", (user_id,))
    plan = cursor.fetchone()
    if not plan:
        conn.close()
        return None, []
        
    plan_id = plan["id"]
    cursor.execute("SELECT * FROM study_plan_tasks WHERE plan_id = ? ORDER BY day_number ASC", (plan_id,))
    tasks = [dict(t) for t in cursor.fetchall()]
    
    conn.close()
    return dict(plan), tasks


def toggle_task_completion(task_id, user_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT is_completed FROM study_plan_tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
    task = cursor.fetchone()
    if not task:
        conn.close()
        return False, 0
        
    new_status = 1 if task["is_completed"] == 0 else 0
    cursor.execute("UPDATE study_plan_tasks SET is_completed = ? WHERE id = ?", (new_status, task_id))
    
    # Award XP if completed
    xp_awarded = 20 if new_status == 1 else 0
    if xp_awarded > 0:
        cursor.execute("UPDATE users SET xp = xp + ? WHERE id = ?", (xp_awarded, user_id))
        
    conn.commit()
    conn.close()
    
    return True, new_status
