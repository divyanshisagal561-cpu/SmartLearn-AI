# 🧠 SmartLearn AI

> **AI-powered personalized learning platform that adapts to every student's learning journey.**

SmartLearn AI is an intelligent learning platform designed to make education **personalized, adaptive, interactive, and engaging**.

Instead of giving every student the same learning experience, SmartLearn AI analyzes quiz performance, identifies weak concepts, adjusts difficulty, generates personalized practice, creates study plans, and provides an AI-powered tutor to support students throughout their learning journey.

---

## 🚀 Why SmartLearn AI?

Traditional learning platforms often follow a **one-size-fits-all** approach.

But every student learns differently.

Some students need stronger fundamentals, while others are ready for advanced problems. SmartLearn AI uses a student's performance to continuously adapt their learning experience.

### Our approach

**Learn → Practice → Analyze → Adapt → Improve**

SmartLearn AI turns this cycle into an intelligent and personalized learning system.

---

## ✨ Key Features

### 🤖 AI-Powered Quiz Generation

Generate quizzes based on:

* Subject
* Topic
* Class/academic level
* Difficulty level
* Preferred language
* Number of questions

The platform can use **Groq or OpenAI** as its AI provider.

---

### 📊 Adaptive Difficulty

SmartLearn AI analyzes quiz performance and automatically adjusts the next difficulty level.

| Score   | Next Difficulty |
| ------- | --------------- |
| 0–40%   | Beginner        |
| 41–60%  | Basic           |
| 61–80%  | Intermediate    |
| 81–100% | Advanced        |

This allows students to gradually progress according to their demonstrated performance.

---

### 🎯 Personalized Practice

After a quiz, the system identifies:

* Weak concepts
* Strong concepts
* Current performance level

It then generates a **targeted practice set** focused on areas where the student needs improvement.

---

### 🧑‍🏫 AI Tutor

Students can ask questions through the built-in AI Tutor.

The tutor supports conversational follow-up questions and maintains short-term conversation context to make explanations more useful.

---

### 📚 Personalized Study Plans

SmartLearn AI can generate personalized:

* 7-day study plans
* 14-day study plans
* 30-day study plans

Study plans are generated using the student's recent performance, weak concepts, subjects, and academic level.

Students can mark tasks as completed and earn XP for completing them.

---

### 📈 Learning Analytics

Students can track their learning progress through:

* Average score
* Highest score
* Completed quizzes
* Current difficulty level
* Strong concepts
* Weak concepts
* Recent quiz attempts

This helps students understand **what they know and what they need to improve**.

---

### 🎮 Gamification

Learning is made more engaging through an XP and achievement system.

Students can unlock badges such as:

* 🏅 First Quiz Completed
* 🔥 3-Day Streak
* 🎯 Weakness Crusher
* 📚 10 Quizzes Completed
* 🚀 Improvement Star
* 🏆 High Score

The system also provides different learner levels based on XP:

**Learner → Explorer → Achiever → Scholar**

---

### 🌐 Multilingual Learning

The platform supports learning in:

* English
* Hindi

The language preference can be selected by the student and is used for AI-generated learning content.

---

### 🔐 User Authentication

SmartLearn AI includes:

* User registration
* Login/logout
* Password hashing
* Session-based authentication
* Individual learning history

---

### 🧪 Offline Demo / Fallback Mode

SmartLearn AI can continue working even when an external AI API key is not configured.

The project includes fallback quiz generation for subjects such as:

* Mathematics
* Computer Science
* Science
* General subjects

This makes the application suitable for **hackathon demonstrations even without an active AI API connection**.

---

## 🏗️ System Architecture

```text
                    ┌─────────────────────┐
                    │      Student        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   SmartLearn AI     │
                    │    Web Interface    │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
        ┌──────────┐     ┌──────────┐     ┌──────────┐
        │ AI Quiz  │     │ AI Tutor │     │  Study   │
        │ Generator│     │          │     │   Plan   │
        └────┬─────┘     └────┬─────┘     └────┬─────┘
             │                │                │
             └────────────────┼────────────────┘
                              ▼
                    ┌─────────────────────┐
                    │ Performance Analysis│
                    │ & Adaptive Learning │
                    └──────────┬──────────┘
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
          ┌──────────┐   ┌──────────┐   ┌──────────┐
          │  Weak    │   │ Difficulty│   │Personalized│
          │ Concepts │   │ Adjustment│   │ Practice │
          └──────────┘   └──────────┘   └──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    SQLite Database  │
                    └─────────────────────┘
```

---

## 🛠️ Tech Stack

### Frontend

* HTML5
* CSS3
* JavaScript
* Jinja2 Templates

### Backend

* Python
* Flask

### Database

* SQLite

### AI

* Claude
* ChatGPT
* OpenAI API
* OpenAI-compatible Python SDK

### Additional Technologies

* Werkzeug
* python-dotenv
* Requests

---

## 📁 Project Structure

```text
SmartLearn-AI/
│
├── app.py                         # Main Flask application
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variable template
├── .gitignore
│
├── database/
│   ├── db.py                      # Database connection & initialization
│   └── schema.sql                 # Database schema
│
├── services/
│   ├── ai_service.py              # AI generation & AI tutor
│   ├── analysis_service.py        # Performance analysis
│   ├── gamification_service.py   # XP & achievements
│   ├── practice_service.py       # Personalized practice
│   ├── quiz_service.py            # Quiz evaluation & storage
│   └── study_plan_service.py      # AI study plan generation
│
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── setup.html
│   ├── quiz.html
│   ├── results.html
│   ├── analysis.html
│   ├── practice.html
│   ├── study_plan.html
│   ├── chatbot.html
│   └── history.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── main.js
│       ├── quiz.js
│       └── study_plan.js
│
└── test_app.py                    # Application tests
```

---

## ⚙️ Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/SmartLearn-AI.git
cd SmartLearn-AI
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it:

**Windows**

```bash
venv\Scripts\activate
```

**macOS / Linux**

```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file using `.env.example` as a template.

For Groq:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

Or for OpenAI:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

You can optionally specify the provider:

```env
AI_PROVIDER=groq
```

If no API key is provided, SmartLearn AI can run using its built-in fallback/demo functionality.

> ⚠️ **Never commit your `.env` file or API keys to GitHub.**

### 5. Run the Application

```bash
python app.py
```

The application will start at:

```text
http://127.0.0.1:5000
```

---

## 🧪 Running Tests

Run the included test suite with:

```bash
python -m unittest test_app.py
```

The tests cover important functionality including:

* Landing page
* Demo mode
* Adaptive difficulty
* Fallback quiz generation
* AI mistake explanation

---

## 🎬 Hackathon Demo

SmartLearn AI includes a dedicated **Demo Mode** for quick presentations.

Open:

```text
http://127.0.0.1:5000/demo
```

Demo Mode automatically creates/logs into a sample student account with existing learning data, allowing judges to immediately explore:

* Dashboard
* Quiz performance
* Weak concepts
* Learning analysis
* Personalized practice
* Study plans
* Gamification

This makes the project easier to demonstrate during a hackathon without requiring manual setup of student data.

---

## 🔄 How SmartLearn AI Works

### Step 1 — Student Setup

The student provides their academic/class level, subject, topic, difficulty, and language preference.

### Step 2 — AI Generates Learning Content

SmartLearn AI generates a quiz based on the selected learning parameters.

### Step 3 — Performance Evaluation

After submission, the system calculates:

* Score
* Correct answers
* Weak concepts
* Strong concepts

### Step 4 — Adaptive Learning

The student's performance determines the recommended difficulty for future learning.

### Step 5 — Personalized Practice

Weak concepts are used to generate targeted practice questions.

### Step 6 — Continuous Improvement

Performance data is stored and used to create personalized study plans and learning insights.

---

## 🗄️ Database Design

SmartLearn AI uses SQLite with the following primary tables:

```text
users
  │
  ├── quiz_attempts
  │      │
  │      └── questions
  │
  ├── study_plans
  │      │
  │      └── study_plan_tasks
  │
  └── achievements
```

### Main Data Stored

**Users**

* Profile information
* Class level
* Language
* XP
* Learning streak

**Quiz Attempts**

* Subject
* Topic
* Difficulty
* Score
* Strong concepts
* Weak concepts

**Questions**

* Question
* Options
* Selected answer
* Correct answer
* Concept
* Explanation

**Study Plans**

* Duration
* AI-generated plan
* Individual tasks
* Completion status

**Achievements**

* Badge
* Description
* Unlock status
* Unlock timestamp

---

## 🔑 AI Provider Support

SmartLearn AI supports two AI providers through an OpenAI-compatible interface:

### Groq

Recommended for the hackathon demo because the application can use a Groq API key with a compatible model.

### OpenAI

The application can alternatively use an OpenAI API key.

The provider can be selected using:

```env
AI_PROVIDER=groq
```

or:

```env
AI_PROVIDER=openai
```

If no provider is configured, the application automatically falls back to its built-in learning content.

---

## 🎯 Core Innovation

The key idea behind SmartLearn AI is not simply **AI-generated questions**.

It is the **learning feedback loop**:

```text
        Student
           ↓
      Take Quiz
           ↓
   Analyze Performance
           ↓
  Identify Weak Concepts
           ↓
  Adjust Difficulty
           ↓
 Generate Personalized
       Practice
           ↓
     Study Plan
           ↓
     Take Quiz Again
           ↺
```

This transforms AI from a simple content generator into a **personalized learning assistant**.

---

## 🌱 Future Scope

Potential future improvements include:

* 📱 Mobile application
* 🎙️ Voice-based AI Tutor
* 📄 PDF/notes-based quiz generation
* 🧠 More advanced knowledge tracing
* 📊 Advanced learning analytics
* 🏫 Teacher/educator dashboard
* 👥 Classroom management
* 📝 AI-generated assignments
* 🔔 Smart study reminders
* 🏆 Leaderboards and collaborative challenges
* 🌐 Support for additional Indian languages
* ☁️ Cloud database and deployment
* 📚 Integration with external learning resources

---

## 🔒 Security Notes

For production deployment, additional security measures should be implemented, including:

* Secure production secret keys
* HTTPS
* Stronger session configuration
* CSRF protection
* API rate limiting
* Production-grade database
* Input validation
* Secure deployment configuration

**Do not expose API keys, `.env` files, or local database files in the public repository.**

---

## 🏆 Hackathon Project

**Project:** SmartLearn AI
**Category:** Artificial Intelligence / EdTech
**Focus:** Personalized & Adaptive Learning

### Built with

**Python • Flask • SQLite • JavaScript • AI • Groq/OpenAI**


```
