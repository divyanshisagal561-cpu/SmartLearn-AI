import unittest
import os
import json
from app import app, init_db
from services.analysis_service import calculate_next_difficulty
from services.ai_service import get_fallback_quiz, explain_mistake

class SmartLearnTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test_secret'
        self.client = app.test_client()
        init_db()

    def test_landing_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'SmartLearn AI', response.data)

    def test_demo_mode_launcher(self):
        response = self.client.get('/demo', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Rahul Sharma', response.data)
        self.assertIn(b'Dashboard', response.data)

    def test_adaptive_difficulty_thresholds(self):
        diff1, _ = calculate_next_difficulty(35.0)
        self.assertEqual(diff1, "Beginner")

        diff2, _ = calculate_next_difficulty(55.0)
        self.assertEqual(diff2, "Basic")

        diff3, _ = calculate_next_difficulty(75.0)
        self.assertEqual(diff3, "Intermediate")

        diff4, _ = calculate_next_difficulty(90.0)
        self.assertEqual(diff4, "Advanced")

    def test_ai_fallback_quiz_generator(self):
        data = get_fallback_quiz("Class 10", "Mathematics", "Quadratic Equations", "Basic", 5)
        self.assertIn("questions", data)
        self.assertEqual(len(data["questions"]), 5)
        q1 = data["questions"][0]
        self.assertIn("question", q1)
        self.assertIn("options", q1)
        self.assertIn("correct_answer", q1)

    def test_explain_mistake_fallback(self):
        exp = explain_mistake(
            class_level="Class 10",
            question_text="What is 2x + 4 = 10?",
            selected_ans="2",
            correct_ans="3",
            concept="Linear equations"
        )
        self.assertEqual(exp["correct_answer"], "3")
        self.assertIn("why_incorrect", exp)
        self.assertIn("step_by_step_reasoning", exp)

if __name__ == '__main__':
    unittest.main()
