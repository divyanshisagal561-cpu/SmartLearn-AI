import json
from database.db import get_db

def evaluate_and_save_attempt(user_id, subject, topic, difficulty, user_answers, raw_questions, is_practice=0):
    """
    user_answers: dict of question_index (int) -> selected_option (str)
    raw_questions: list of question dicts from ai_service
    """
    conn = get_db()
    cursor = conn.cursor()
    
    total_questions = len(raw_questions)
    correct_count = 0
    
    concept_stats = {} # concept -> {"correct": 0, "total": 0}
    
    processed_questions = []
    
    for idx, q in enumerate(raw_questions):
        selected_ans = user_answers.get(str(idx), user_answers.get(idx, ""))
        correct_ans = q.get("correct_answer", "").strip()
        concept = q.get("concept", "General").strip()
        
        is_correct = 1 if (selected_ans and selected_ans.strip().lower() == correct_ans.lower()) else 0
        if is_correct:
            correct_count += 1
            
        if concept not in concept_stats:
            concept_stats[concept] = {"correct": 0, "total": 0}
        concept_stats[concept]["total"] += 1
        if is_correct:
            concept_stats[concept]["correct"] += 1
            
        processed_questions.append({
            "question": q.get("question"),
            "options_json": json.dumps(q.get("options", [])),
            "selected_answer": selected_ans,
            "correct_answer": correct_ans,
            "concept": concept,
            "difficulty": q.get("difficulty", difficulty),
            "is_correct": is_correct,
            "explanation": q.get("explanation", "")
        })
        
    score_pct = round((correct_count / total_questions) * 100, 1) if total_questions > 0 else 0.0
    
    # Categorize strong vs weak concepts
    strong_concepts = []
    weak_concepts = []
    
    for concept, stats in concept_stats.items():
        acc = stats["correct"] / stats["total"]
        if acc >= 0.7:
            strong_concepts.append(concept)
        else:
            weak_concepts.append(concept)
            
    # Insert attempt record
    cursor.execute("""
        INSERT INTO quiz_attempts (user_id, subject, topic, difficulty, score, total_questions, correct_count, weak_concepts, strong_concepts, is_practice)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        subject,
        topic,
        difficulty,
        score_pct,
        total_questions,
        correct_count,
        json.dumps(weak_concepts),
        json.dumps(strong_concepts),
        is_practice
    ))
    
    attempt_id = cursor.lastrowid
    
    # Insert individual questions
    for pq in processed_questions:
        cursor.execute("""
            INSERT INTO questions (attempt_id, question, options_json, selected_answer, correct_answer, concept, difficulty, is_correct, explanation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            attempt_id,
            pq["question"],
            pq["options_json"],
            pq["selected_answer"],
            pq["correct_answer"],
            pq["concept"],
            pq["difficulty"],
            pq["is_correct"],
            pq["explanation"]
        ))
        
    conn.commit()
    conn.close()
    
    return attempt_id, score_pct, weak_concepts, strong_concepts


def get_attempt_details(attempt_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM quiz_attempts WHERE id = ?", (attempt_id,))
    attempt = cursor.fetchone()
    if not attempt:
        conn.close()
        return None, []
        
    attempt_dict = dict(attempt)
    try:
        attempt_dict["weak_concepts"] = json.loads(attempt_dict.get("weak_concepts", "[]"))
        attempt_dict["strong_concepts"] = json.loads(attempt_dict.get("strong_concepts", "[]"))
    except:
        attempt_dict["weak_concepts"] = []
        attempt_dict["strong_concepts"] = []
        
    cursor.execute("SELECT * FROM questions WHERE attempt_id = ?", (attempt_id,))
    questions_rows = cursor.fetchall()
    
    questions = []
    for q in questions_rows:
        qd = dict(q)
        try:
            qd["options"] = json.loads(qd.get("options_json", "[]"))
        except:
            qd["options"] = []
        questions.append(qd)
        
    conn.close()
    return attempt_dict, questions
