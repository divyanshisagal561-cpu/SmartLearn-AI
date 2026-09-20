import os
import json
import logging
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

from database.db import init_db, get_db
from services.ai_service import (
    generate_quiz_questions,
    explain_mistake,
    generate_study_plan,
    ask_ai_tutor
)
from services.quiz_service import evaluate_and_save_attempt, get_attempt_details
from services.analysis_service import calculate_next_difficulty, get_user_performance_summary
from services.practice_service import generate_personalized_practice_for_user
from services.study_plan_service import create_user_study_plan, get_latest_user_study_plan, toggle_task_completion
from services.gamification_service import award_quiz_rewards, get_user_achievements, get_user_level

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "smartlearn_ai_secret_key_hackathon_2026")

# Ensure database is initialized on start
with app.app_context():
    init_db()


def login_required(f):
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please login to access this feature.", "info")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        class_level = request.form.get('class_level', '').strip()

        if not name or not email or not password or not class_level:
            flash("All fields (Name, Email, Password, Class) are required.", "error")
            return render_template('register.html')

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            flash("An account with this email already exists. Please login.", "error")
            return render_template('register.html')

        password_hash = generate_password_hash(password)
        cursor.execute("""
            INSERT INTO users (name, email, password_hash, class_level, xp, streak)
            VALUES (?, ?, ?, ?, 50, 1)
        """, (name, email, password_hash, class_level))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Log user in
        session['user_id'] = user_id
        session['user_name'] = name
        session['class_level'] = class_level
        session['streak'] = 1
        session['xp'] = 50
        session['language'] = 'English'

        flash(f"Welcome to SmartLearn AI, {name}! Your learning journey begins now.", "success")
        return redirect(url_for('dashboard'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash("Email and password are required.", "error")
            return render_template('login.html')

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['class_level'] = user['class_level']
            session['streak'] = user['streak']
            session['xp'] = user['xp']
            session['language'] = user['language'] or 'English'

            flash(f"Welcome back, {user['name']} 👋", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password. Please try again.", "error")
            return render_template('login.html')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = dict(cursor.fetchone())
    conn.close()

    # Refresh session values
    session['xp'] = user['xp']
    session['streak'] = user['streak']

    stats = get_user_performance_summary(user_id)
    achievements = get_user_achievements(user_id)
    level_title, level_num, next_xp = get_user_level(user['xp'])

    return render_template(
        'dashboard.html',
        user=user,
        stats=stats,
        achievements=achievements,
        level_title=level_title,
        level_num=level_num
    )


@app.route('/setup')
@login_required
def setup():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = dict(cursor.fetchone())
    conn.close()
    return render_template('setup.html', user=user)


@app.route('/generate_quiz', methods=['POST'])
@login_required
def generate_quiz_route():
    subject = request.form.get('subject', '').strip()
    topic = request.form.get('topic', '').strip()
    num_questions = int(request.form.get('num_questions', 5))
    difficulty = request.form.get('difficulty', 'Adaptive')

    if not subject or not topic:
        flash("Subject and topic cannot be empty.", "error")
        return redirect(url_for('setup'))

    class_level = session.get('class_level', 'Class 10')
    language = session.get('language', 'English')

    # If adaptive selected, resolve difficulty based on past performance
    resolved_difficulty = difficulty
    if difficulty == "Adaptive":
        stats = get_user_performance_summary(session['user_id'])
        if stats['quizzes_completed'] > 0:
            resolved_difficulty, _ = calculate_next_difficulty(stats['avg_score'])
        else:
            resolved_difficulty = "Basic"

    # Call AI Service
    quiz_data = generate_quiz_questions(
        class_level=class_level,
        subject=subject,
        topic=topic,
        difficulty=resolved_difficulty,
        num_questions=num_questions,
        language=language,
        weak_concepts=None
    )

    questions = quiz_data.get('questions', [])
    if not questions:
        flash("Could not generate quiz questions. Switching to Demo Quiz fallback.", "info")

    # Store temp quiz session state
    session['current_quiz'] = {
        "subject": subject,
        "topic": topic,
        "difficulty": resolved_difficulty,
        "questions": questions,
        "is_practice": 0
    }

    user = {"class_level": class_level, "name": session.get('user_name')}

    return render_template(
        'quiz.html',
        user=user,
        quiz_meta={"subject": subject, "topic": topic, "difficulty": resolved_difficulty},
        questions=questions
    )


@app.route('/submit_quiz', methods=['POST'])
@login_required
def submit_quiz_route():
    user_answers_raw = request.form.get('user_answers', '{}')
    try:
        user_answers = json.loads(user_answers_raw)
    except:
        user_answers = {}

    current_quiz = session.get('current_quiz')
    if not current_quiz:
        flash("Quiz session expired. Please start a new quiz.", "error")
        return redirect(url_for('setup'))

    user_id = session['user_id']
    subject = current_quiz['subject']
    topic = current_quiz['topic']
    difficulty = current_quiz['difficulty']
    raw_questions = current_quiz['questions']
    is_practice = current_quiz.get('is_practice', 0)

    # Evaluate attempt
    attempt_id, score_pct, weak, strong = evaluate_and_save_attempt(
        user_id=user_id,
        subject=subject,
        topic=topic,
        difficulty=difficulty,
        user_answers=user_answers,
        raw_questions=raw_questions,
        is_practice=is_practice
    )

    # Award XP & evaluate achievements
    xp_earned, new_badges = award_quiz_rewards(user_id, score_pct, is_practice)

    badge_msg = f" (+{xp_earned} XP)"
    if new_badges:
        b_names = ", ".join([b['name'] for b in new_badges])
        badge_msg += f" 🎉 New Badge Unlocked: {b_names}!"

    flash(f"Quiz completed! Score: {score_pct}%{badge_msg}", "success")
    return redirect(url_for('quiz_results', attempt_id=attempt_id))


@app.route('/results/<int:attempt_id>')
@login_required
def quiz_results(attempt_id):
    attempt, questions = get_attempt_details(attempt_id)
    if not attempt or attempt['user_id'] != session['user_id']:
        flash("Quiz attempt not found.", "error")
        return redirect(url_for('dashboard'))

    return render_template('results.html', attempt=attempt, questions=questions)


@app.route('/analysis/<int:attempt_id>')
@login_required
def learning_analysis(attempt_id):
    attempt, _ = get_attempt_details(attempt_id)
    if not attempt or attempt['user_id'] != session['user_id']:
        flash("Quiz attempt not found.", "error")
        return redirect(url_for('dashboard'))

    current_level, _ = calculate_next_difficulty(attempt['score'])
    next_difficulty, next_reason = calculate_next_difficulty(attempt['score'], attempt['difficulty'])

    user = {"name": session.get('user_name'), "class_level": session.get('class_level')}

    return render_template(
        'analysis.html',
        attempt=attempt,
        current_level=current_level,
        next_difficulty=next_difficulty,
        next_reason=next_reason,
        user=user
    )


@app.route('/practice')
@login_required
def personalized_practice():
    attempt_id = request.args.get('attempt_id')
    user_id = session['user_id']
    
    practice_data = generate_personalized_practice_for_user(user_id, attempt_id)

    # Store temp quiz state
    session['current_quiz'] = {
        "subject": practice_data['subject'],
        "topic": practice_data['topic'],
        "difficulty": practice_data['difficulty'],
        "questions": practice_data['questions'],
        "is_practice": 1
    }

    user = {"class_level": session.get('class_level'), "name": session.get('user_name')}

    return render_template('practice.html', user=user, practice_data=practice_data)


@app.route('/history')
@login_required
def history():
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM quiz_attempts WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()

    attempts = []
    for r in rows:
        d = dict(r)
        try:
            d['weak_concepts'] = json.loads(d['weak_concepts'])
        except:
            d['weak_concepts'] = []
        attempts.append(d)

    return render_template('history.html', attempts=attempts)


@app.route('/study_plan')
@login_required
def study_plan():
    user_id = session['user_id']
    plan, tasks = get_latest_user_study_plan(user_id)
    duration = plan['duration'] if plan else 7

    return render_template('study_plan.html', plan=plan, tasks=tasks, current_duration=duration)


@app.route('/generate_study_plan', methods=['POST'])
@login_required
def generate_new_study_plan():
    duration = int(request.form.get('duration', 7))
    user_id = session['user_id']

    create_user_study_plan(user_id, duration_days=duration)
    flash(f"New {duration}-Day Personalized AI Study Plan generated!", "success")
    return redirect(url_for('study_plan'))


@app.route('/api/toggle_task/<int:task_id>', methods=['POST'])
@login_required
def api_toggle_task(task_id):
    user_id = session['user_id']
    success, is_completed = toggle_task_completion(task_id, user_id)
    xp_awarded = 20 if is_completed else 0
    return jsonify({"success": success, "is_completed": is_completed, "xp_awarded": xp_awarded})


@app.route('/chatbot')
@login_required
def chatbot():
    user = {"name": session.get('user_name'), "class_level": session.get('class_level')}
    return render_template('chatbot.html', user=user)


@app.route('/api/ask_tutor', methods=['POST'])
@login_required
def api_ask_tutor():
    data = request.get_json() or {}
    query = data.get('query', '').strip()
    if not query:
        return jsonify({"reply": "Please type a valid question!"})

    class_level = session.get('class_level', 'Class 10')
    language = session.get('language', 'English')

    # Keep short conversation history per session so follow-up questions
    # get real context instead of a one-off reply.
    history = session.get('chat_history', [])
    reply = ask_ai_tutor(class_level, query, conversation_history=history, language=language)

    history.append({"role": "user", "content": query})
    history.append({"role": "assistant", "content": reply})
    session['chat_history'] = history[-12:]  # keep last 12 messages (6 exchanges)

    return jsonify({"reply": reply})


@app.route('/api/explain_mistake/<int:question_id>')
@login_required
def api_explain_mistake(question_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM questions WHERE id = ?", (question_id,))
    q_row = cursor.fetchone()
    conn.close()

    if not q_row:
        return jsonify({"error": "Question not found"}), 404

    q = dict(q_row)
    class_level = session.get('class_level', 'Class 10')
    language = session.get('language', 'English')

    explanation_data = explain_mistake(
        class_level=class_level,
        question_text=q['question'],
        selected_ans=q['selected_answer'] or 'None',
        correct_ans=q['correct_answer'],
        concept=q['concept'],
        explanation_base=q['explanation'],
        language=language
    )

    return jsonify(explanation_data)


@app.route('/set_language', methods=['POST'])
def set_language():
    lang = request.form.get('language', 'English')
    session['language'] = lang
    if 'user_id' in session:
        conn = get_db()
        conn.execute("UPDATE users SET language = ? WHERE id = ?", (lang, session['user_id']))
        conn.commit()
        conn.close()
    flash(f"Language set to {lang}", "success")
    return redirect(request.referrer or url_for('dashboard'))


@app.route('/demo')
def demo_mode():
    """
    1-Click Demo Launcher for Hackathon Judges
    Creates / logs into sample student 'Rahul Sharma', seeds sample attempts & weak concepts,
    and redirects directly to the dashboard.
    """
    conn = get_db()
    cursor = conn.cursor()

    demo_email = "rahul.demo@smartlearn.ai"
    cursor.execute("SELECT * FROM users WHERE email = ?", (demo_email,))
    user = cursor.fetchone()

    if not user:
        # Create demo user
        pass_hash = generate_password_hash("demo1234")
        cursor.execute("""
            INSERT INTO users (name, email, password_hash, class_level, xp, streak)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("Rahul Sharma", demo_email, pass_hash, "Class 10", 240, 3))
        user_id = cursor.lastrowid
        conn.commit()

        # Seed initial quiz attempt (so dashboard chart & weak concepts look rich!)
        weak_c = json.dumps(["Discriminant", "Quadratic Formula"])
        strong_c = json.dumps(["Standard form", "Factorization"])
        cursor.execute("""
            INSERT INTO quiz_attempts (user_id, subject, topic, difficulty, score, total_questions, correct_count, weak_concepts, strong_concepts)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, "Mathematics", "Quadratic Equations", "Intermediate", 60.0, 5, 3, weak_c, strong_c))
        attempt_id = cursor.lastrowid

        # Seed questions
        sample_q = [
            ("What is the discriminant of 2x² - 4x + 3 = 0?", json.dumps(["-8", "8", "-16", "16"]), "8", "-8", "Discriminant", "Intermediate", 0, "b² - 4ac = (-4)² - 4(2)(3) = 16 - 24 = -8."),
            ("What are the roots of x² - 5x + 6 = 0?", json.dumps(["2, 3", "1, 6", "-2, -3", "3, 4"]), "2, 3", "2, 3", "Factorization", "Basic", 1, "(x - 2)(x - 3) = 0"),
            ("Which part of quadratic formula is under the square root?", json.dumps(["b² - 4ac", "-b", "2a", "ac"]), "-b", "b² - 4ac", "Quadratic Formula", "Basic", 0, "The term inside √(b² - 4ac) is the discriminant.")
        ]
        for sq in sample_q:
            cursor.execute("""
                INSERT INTO questions (attempt_id, question, options_json, selected_answer, correct_answer, concept, difficulty, is_correct, explanation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (attempt_id, sq[0], sq[1], sq[2], sq[3], sq[4], sq[5], sq[6], sq[7]))

        conn.commit()
        conn.close()

        # Seed study plan
        create_user_study_plan(user_id, duration_days=7)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
    else:
        conn.close()

    session['user_id'] = user['id']
    session['user_name'] = user['name']
    session['class_level'] = user['class_level']
    session['streak'] = user['streak']
    session['xp'] = user['xp']
    session['language'] = 'English'

    flash("🚀 Hackathon Demo Mode Active! Logged in as Sample Student 'Rahul Sharma' (Class 10).", "success")
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    print("Starting SmartLearn AI Server on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
