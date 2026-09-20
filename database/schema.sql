-- Database Schema for SmartLearn AI

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    class_level TEXT NOT NULL,
    language TEXT DEFAULT 'English',
    xp INTEGER DEFAULT 0,
    streak INTEGER DEFAULT 1,
    last_login_date TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS quiz_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    subject TEXT NOT NULL,
    topic TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    score REAL DEFAULT 0,
    total_questions INTEGER NOT NULL,
    correct_count INTEGER DEFAULT 0,
    weak_concepts TEXT, -- JSON string or comma-separated
    strong_concepts TEXT, -- JSON string or comma-separated
    is_practice INTEGER DEFAULT 0, -- 1 if personalized practice set
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL,
    question TEXT NOT NULL,
    options_json TEXT NOT NULL, -- JSON array of 4 options
    selected_answer TEXT,
    correct_answer TEXT NOT NULL,
    concept TEXT NOT NULL,
    difficulty TEXT DEFAULT 'Basic',
    is_correct INTEGER DEFAULT 0,
    explanation TEXT,
    FOREIGN KEY(attempt_id) REFERENCES quiz_attempts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS study_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    duration INTEGER NOT NULL, -- 7, 14, or 30 days
    plan_data_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS study_plan_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    day_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    concept TEXT,
    is_completed INTEGER DEFAULT 0,
    FOREIGN KEY(plan_id) REFERENCES study_plans(id) ON DELETE CASCADE,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    badge_code TEXT NOT NULL,
    badge_name TEXT NOT NULL,
    description TEXT,
    icon TEXT,
    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
