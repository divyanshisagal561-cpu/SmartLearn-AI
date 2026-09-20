import os
import json
import random
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_service")

# --------------------------------------------------------------------------
# AI provider setup.
#
# Supports TWO providers through the same OpenAI-compatible client:
#   1. Groq  (FREE, no credit card, no expiring trial credits) — used by
#      default if GROQ_API_KEY is set. Get a key at https://console.groq.com
#   2. OpenAI (paid) — used if OPENAI_API_KEY is set instead/as well.
#
# If neither key is present, `client` stays None and every function below
# falls back to the static offline demo templates (this was the cause of
# the "AI Tutor repeats itself" / "quiz questions don't change per topic"
# bugs — there was no .env file at all, so no real AI call was ever made).
# --------------------------------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

AI_PROVIDER = os.getenv("AI_PROVIDER", "").strip().lower()  # "groq" | "openai" | "" (auto)

client = None
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

def _valid(key, placeholder):
    return bool(key) and key != placeholder

try:
    from openai import OpenAI  # Groq's API is OpenAI-compatible, so the same SDK/class works for both.

    use_groq = _valid(GROQ_API_KEY, "your_groq_api_key_here") and AI_PROVIDER != "openai"
    use_openai = _valid(OPENAI_API_KEY, "your_openai_api_key_here") and AI_PROVIDER != "groq"

    if use_groq:
        client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
        OPENAI_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        logger.info(f"Groq client initialized successfully (model={OPENAI_MODEL}, free tier).")
    elif use_openai:
        client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info(f"OpenAI client initialized successfully (model={OPENAI_MODEL}).")
    else:
        logger.warning("No GROQ_API_KEY or OPENAI_API_KEY found — running in offline demo mode.")
except Exception as e:
    logger.warning(f"Failed to initialize AI client: {e}")

# Helper to clean JSON string from LLM responses (markdown code blocks removal)
def clean_json_string(text):
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text

# --------------------------------------------------------------------------
# Subject classification for the offline/fallback quiz generator.
#
# BUGFIX (Subject/Topic mismatch): the previous version matched subjects with
# a loose `"science" in subject_lower` check. Because "Computer Science"
# *contains* the substring "science", a Computer Science quiz used to fall
# through to the Physics/Chemistry/Biology question bank (e.g. the SI unit
# of force bug). Subjects are now classified with explicit, priority-ordered
# checks so "Computer Science" is matched as Computer Science FIRST, before
# any generic "science" substring check ever runs.
# --------------------------------------------------------------------------
def classify_subject(subject, topic):
    s = subject.strip().lower()
    t = topic.strip().lower()

    # 1. Computer Science / Programming — checked first so it can never be
    #    swallowed by the generic "science" check below.
    #    NOTE: no bare "cs" keyword here on purpose — it would match the
    #    trailing "...ics" in words like "Mathematics", causing a new
    #    false-positive misclassification.
    cs_keywords = ("computer", "programming", "coding", "informatics", "python",
                   "java", "c++", "data structure", "algorithm")
    if any(k in s for k in cs_keywords) or s in ("cs", "it", "ict"):
        return "computer_science"

    # 2. Mathematics
    math_keywords = ("math", "algebra", "arithmetic", "trigonometry", "geometry")
    if any(k in s for k in math_keywords) or any(k in t for k in ("equation", "quadratic", "algebra")):
        return "mathematics"

    # 3. Pure sciences (exact/near-exact subject names only — NOT a bare
    #    substring check, so "Computer Science" can never land here).
    science_keywords = ("physics", "chemistry", "biology")
    if any(k in s for k in science_keywords) or s == "science":
        return "science"

    # 4. Anything else (English, History, Geography, Commerce, etc.) uses a
    #    dynamic, topic-driven generic bank instead of guessing wrong.
    return "generic"


def get_fallback_quiz(class_level, subject, topic, difficulty, num_questions, language="English"):
    logger.info(f"Generating fallback quiz for {subject} - {topic} ({difficulty}) [{language}]")

    category = classify_subject(subject, topic)
    topic_lower = topic.lower()
    is_hindi = language.strip().lower().startswith("hindi") or language.strip() == "हिंदी"

    questions = []

    if category == "computer_science":
        is_loop_topic = "loop" in topic_lower or "iteration" in topic_lower or "for" in topic_lower.split() or "while" in topic_lower.split()

        if is_loop_topic:
            base_bank = _cs_loops_hi() if is_hindi else _cs_loops_en()
        else:
            base_bank = _cs_generic_hi(topic, class_level) if is_hindi else _cs_generic_en(topic, class_level)

    elif category == "mathematics":
        base_bank = _math_bank_hi(class_level) if is_hindi else _math_bank_en(class_level)

    elif category == "science":
        base_bank = _science_bank_hi(class_level) if is_hindi else _science_bank_en(class_level)

    else:
        base_bank = _generic_bank_hi(subject, topic, class_level, difficulty) if is_hindi else _generic_bank_en(subject, topic, class_level, difficulty)

    # Expand bank if num_questions > length of bank
    output = []
    for i in range(num_questions):
        template = base_bank[i % len(base_bank)]
        item = dict(template)
        item["difficulty"] = difficulty
        if i >= len(base_bank):
            prefix = f"[{topic} प्रश्न {i+1}] " if is_hindi else f"[{topic} Q{i+1}] "
            item["question"] = prefix + item["question"]
        output.append(item)

    return {"questions": output}


def _cs_loops_en():
    return [
        {
            "question": "Which loop is best suited when the number of iterations is known in advance?",
            "options": ["for loop", "while loop", "do-while loop", "if-else statement"],
            "correct_answer": "for loop",
            "concept": "Loop selection",
            "explanation": "A for loop is ideal when you already know exactly how many times the loop must run, such as looping a fixed number of times."
        },
        {
            "question": "What does the following pseudocode print?\ni = 0\nwhile i < 3:\n    print(i)\n    i = i + 1",
            "options": ["0 1 2", "1 2 3", "0 1 2 3", "Infinite loop"],
            "correct_answer": "0 1 2",
            "concept": "While loop execution",
            "explanation": "The loop starts at i=0 and runs while i < 3, printing 0, 1, and 2, then stops when i becomes 3."
        },
        {
            "question": "Which keyword immediately exits a loop before it finishes all iterations?",
            "options": ["break", "continue", "pass", "return"],
            "correct_answer": "break",
            "concept": "Loop control statements",
            "explanation": "'break' terminates the nearest enclosing loop immediately, skipping any remaining iterations."
        },
        {
            "question": "Which keyword skips the rest of the current iteration and moves to the next one?",
            "options": ["continue", "break", "exit", "stop"],
            "correct_answer": "continue",
            "concept": "Loop control statements",
            "explanation": "'continue' skips the remaining code in the current iteration and jumps to the loop's next iteration check."
        },
        {
            "question": "What is an 'infinite loop'?",
            "options": [
                "A loop whose condition never becomes false, so it never stops",
                "A loop that runs exactly once",
                "A loop with no body",
                "A loop that only works with arrays"
            ],
            "correct_answer": "A loop whose condition never becomes false, so it never stops",
            "concept": "Loop conditions",
            "explanation": "If the loop's stopping condition is never met (e.g. the counter is never updated), the loop keeps running forever."
        },
        {
            "question": "In a for loop 'for i in range(5):', how many times does the loop body execute?",
            "options": ["5", "4", "6", "Infinite"],
            "correct_answer": "5",
            "concept": "Iteration count",
            "explanation": "range(5) produces the values 0,1,2,3,4 — exactly 5 values — so the loop body runs 5 times."
        }
    ]


def _cs_loops_hi():
    return [
        {
            "question": "यदि पहले से पता हो कि लूप को कितनी बार चलाना है, तो कौन सा लूप सबसे उपयुक्त है?",
            "options": ["for लूप", "while लूप", "do-while लूप", "if-else स्टेटमेंट"],
            "correct_answer": "for लूप",
            "concept": "Loop selection",
            "explanation": "for लूप तब सबसे उपयुक्त है जब हमें पहले से पता हो कि लूप को कितनी बार चलाना है।"
        },
        {
            "question": "निम्न कोड क्या प्रिंट करेगा?\ni = 0\nwhile i < 3:\n    print(i)\n    i = i + 1",
            "options": ["0 1 2", "1 2 3", "0 1 2 3", "अनंत लूप (Infinite loop)"],
            "correct_answer": "0 1 2",
            "concept": "While loop execution",
            "explanation": "लूप i=0 से शुरू होता है और i < 3 तक चलता है, इसलिए यह 0, 1, 2 प्रिंट करता है और फिर रुक जाता है।"
        },
        {
            "question": "कौन सा keyword लूप को तुरंत समाप्त कर देता है, बाकी iterations चलाए बिना?",
            "options": ["break", "continue", "pass", "return"],
            "correct_answer": "break",
            "concept": "Loop control statements",
            "explanation": "'break' सबसे नज़दीकी लूप को तुरंत समाप्त कर देता है और बाकी बचे हुए iterations को छोड़ देता है।"
        },
        {
            "question": "कौन सा keyword वर्तमान iteration को छोड़कर सीधे अगले iteration पर चला जाता है?",
            "options": ["continue", "break", "exit", "stop"],
            "correct_answer": "continue",
            "concept": "Loop control statements",
            "explanation": "'continue' मौजूदा iteration का बचा हुआ कोड छोड़ देता है और अगले iteration की जांच पर चला जाता है।"
        },
        {
            "question": "'अनंत लूप' (Infinite loop) किसे कहते हैं?",
            "options": [
                "ऐसा लूप जिसकी शर्त (condition) कभी असत्य (false) नहीं होती, इसलिए वह कभी नहीं रुकता",
                "ऐसा लूप जो केवल एक बार चलता है",
                "ऐसा लूप जिसमें कोई body न हो",
                "ऐसा लूप जो केवल arrays के साथ काम करता है"
            ],
            "correct_answer": "ऐसा लूप जिसकी शर्त (condition) कभी असत्य (false) नहीं होती, इसलिए वह कभी नहीं रुकता",
            "concept": "Loop conditions",
            "explanation": "यदि लूप की रुकने की शर्त कभी पूरी न हो (जैसे काउंटर कभी अपडेट न हो), तो लूप हमेशा चलता रहता है।"
        },
        {
            "question": "'for i in range(5):' में लूप बॉडी कितनी बार चलेगी?",
            "options": ["5", "4", "6", "अनंत (Infinite)"],
            "correct_answer": "5",
            "concept": "Iteration count",
            "explanation": "range(5), 0,1,2,3,4 — यानी कुल 5 मान देता है, इसलिए लूप बॉडी 5 बार चलती है।"
        }
    ]


def _cs_generic_en(topic, class_level):
    return [
        {
            "question": f"In Computer Science ({class_level}), which of these correctly describes a 'variable' in the context of '{topic}'?",
            "options": [
                "A named storage location that holds a value which can change",
                "A fixed value that never changes",
                "A type of hardware device",
                "A syntax error in code"
            ],
            "correct_answer": "A named storage location that holds a value which can change",
            "concept": "Variables",
            "explanation": "A variable is a named container in memory used to store data that can be read or updated while a program runs."
        },
        {
            "question": "Which of these is NOT a common programming data type?",
            "options": ["Paragraph", "Integer", "String", "Boolean"],
            "correct_answer": "Paragraph",
            "concept": "Data types",
            "explanation": "Integer, String, and Boolean are standard data types; 'Paragraph' is not a recognized programming data type."
        },
        {
            "question": "What is a 'function' in programming?",
            "options": [
                "A reusable block of code that performs a specific task",
                "A type of database",
                "An error message",
                "A hardware component"
            ],
            "correct_answer": "A reusable block of code that performs a specific task",
            "concept": "Functions",
            "explanation": "Functions let you group code into a reusable, named block that can be called whenever that task is needed."
        },
        {
            "question": "Which statement is used to make decisions in code based on a condition?",
            "options": ["if-else", "for", "print", "import"],
            "correct_answer": "if-else",
            "concept": "Conditional statements",
            "explanation": "An if-else statement runs different blocks of code depending on whether a condition is true or false."
        },
        {
            "question": f"For the topic '{topic}', which best describes an algorithm?",
            "options": [
                "A step-by-step procedure to solve a problem",
                "A type of computer virus",
                "A physical computer part",
                "A programming language"
            ],
            "correct_answer": "A step-by-step procedure to solve a problem",
            "concept": "Algorithms",
            "explanation": "An algorithm is a well-defined, ordered sequence of steps used to solve a problem or complete a task."
        }
    ]


def _cs_generic_hi(topic, class_level):
    return [
        {
            "question": f"कंप्यूटर साइंस ({class_level}) में, '{topic}' के संदर्भ में 'वेरिएबल (variable)' को सही तरीके से कौन बताता है?",
            "options": [
                "एक नामित स्टोरेज स्थान जो ऐसा मान रखता है जो बदल सकता है",
                "एक स्थिर मान जो कभी नहीं बदलता",
                "एक प्रकार का हार्डवेयर डिवाइस",
                "कोड में एक सिंटैक्स एरर"
            ],
            "correct_answer": "एक नामित स्टोरेज स्थान जो ऐसा मान रखता है जो बदल सकता है",
            "concept": "Variables",
            "explanation": "वेरिएबल मेमोरी में एक नामित कंटेनर होता है जिसका उपयोग डेटा स्टोर करने के लिए किया जाता है, जिसे प्रोग्राम चलते समय पढ़ा या बदला जा सकता है।"
        },
        {
            "question": "इनमें से कौन सा एक सामान्य प्रोग्रामिंग डेटा टाइप नहीं है?",
            "options": ["पैराग्राफ (Paragraph)", "Integer", "String", "Boolean"],
            "correct_answer": "पैराग्राफ (Paragraph)",
            "concept": "Data types",
            "explanation": "Integer, String और Boolean मानक डेटा टाइप हैं; 'पैराग्राफ' कोई मान्यता प्राप्त प्रोग्रामिंग डेटा टाइप नहीं है।"
        },
        {
            "question": "प्रोग्रामिंग में 'फंक्शन (function)' क्या होता है?",
            "options": [
                "कोड का एक पुन:प्रयोज्य (reusable) हिस्सा जो एक विशेष कार्य करता है",
                "एक प्रकार का डेटाबेस",
                "एक एरर मैसेज",
                "एक हार्डवेयर कंपोनेंट"
            ],
            "correct_answer": "कोड का एक पुन:प्रयोज्य (reusable) हिस्सा जो एक विशेष कार्य करता है",
            "concept": "Functions",
            "explanation": "फंक्शन कोड को एक पुन:प्रयोज्य, नामित हिस्से में समूहित करने देता है, जिसे जब भी वह कार्य चाहिए हो, बुलाया जा सकता है।"
        },
        {
            "question": "किसी शर्त (condition) के आधार पर कोड में निर्णय लेने के लिए कौन सा स्टेटमेंट उपयोग किया जाता है?",
            "options": ["if-else", "for", "print", "import"],
            "correct_answer": "if-else",
            "concept": "Conditional statements",
            "explanation": "if-else स्टेटमेंट शर्त सत्य है या असत्य, इसके आधार पर कोड के अलग-अलग हिस्सों को चलाता है।"
        },
        {
            "question": f"विषय '{topic}' के लिए, एल्गोरिथ्म (algorithm) को सबसे अच्छा कौन बताता है?",
            "options": [
                "किसी समस्या को हल करने की चरण-दर-चरण प्रक्रिया",
                "एक प्रकार का कंप्यूटर वायरस",
                "कंप्यूटर का एक भौतिक हिस्सा",
                "एक प्रोग्रामिंग भाषा"
            ],
            "correct_answer": "किसी समस्या को हल करने की चरण-दर-चरण प्रक्रिया",
            "concept": "Algorithms",
            "explanation": "एल्गोरिथ्म किसी समस्या को हल करने या कार्य पूरा करने के लिए चरणों का एक स्पष्ट, क्रमबद्ध क्रम है।"
        }
    ]


def _math_bank_en(class_level):
    return [
        {
            "question": f"What is the value of x if 2x + 4 = 10 for {class_level} Algebra?",
            "options": ["2", "3", "4", "5"],
            "correct_answer": "3",
            "concept": "Linear equations",
            "explanation": "Subtract 4 from both sides: 2x = 6. Divide both sides by 2: x = 3."
        },
        {
            "question": "In quadratic equation ax² + bx + c = 0, what does the discriminant (b² - 4ac) determine?",
            "options": ["The number and nature of roots", "The y-intercept", "The vertex height", "The slope of tangent"],
            "correct_answer": "The number and nature of roots",
            "concept": "Discriminant",
            "explanation": "If b² - 4ac > 0 there are 2 real roots, if 0 there is 1 real root, if < 0 there are complex roots."
        },
        {
            "question": "Which of the following is the quadratic formula to solve ax² + bx + c = 0?",
            "options": ["x = (-b ± √(b² - 4ac)) / (2a)", "x = (-b ± √(b + 4ac)) / a", "x = (b ± √(b² - 4ac)) / 2", "x = -b / (2a)"],
            "correct_answer": "x = (-b ± √(b² - 4ac)) / (2a)",
            "concept": "Quadratic formula",
            "explanation": "The standard quadratic formula is x = (-b ± √(b² - 4ac)) / (2a)."
        },
        {
            "question": "If the roots of x² - 5x + 6 = 0 are p and q, what are the values of p and q?",
            "options": ["2 and 3", "1 and 6", "-2 and -3", "-1 and -6"],
            "correct_answer": "2 and 3",
            "concept": "Factorization",
            "explanation": "Factorize into (x - 2)(x - 3) = 0. Therefore x = 2 or x = 3."
        },
        {
            "question": "What is the degree of the polynomial P(x) = 3x³ + 5x² - 7?",
            "options": ["3", "2", "1", "5"],
            "correct_answer": "3",
            "concept": "Polynomial degree",
            "explanation": "The degree of a polynomial is the highest power of the variable x, which is 3."
        }
    ]


def _math_bank_hi(class_level):
    return [
        {
            "question": f"यदि 2x + 4 = 10 है, तो {class_level} बीजगणित (Algebra) में x का मान क्या होगा?",
            "options": ["2", "3", "4", "5"],
            "correct_answer": "3",
            "concept": "Linear equations",
            "explanation": "दोनों पक्षों से 4 घटाएँ: 2x = 6। अब दोनों पक्षों को 2 से भाग दें: x = 3।"
        },
        {
            "question": "द्विघात समीकरण (quadratic equation) ax² + bx + c = 0 में, विविक्तकर (discriminant) b² - 4ac क्या निर्धारित करता है?",
            "options": ["मूलों की संख्या और प्रकृति (nature)", "y-अंतःखंड (y-intercept)", "शीर्ष की ऊँचाई", "स्पर्शरेखा का ढलान"],
            "correct_answer": "मूलों की संख्या और प्रकृति (nature)",
            "concept": "Discriminant",
            "explanation": "यदि b² - 4ac > 0 है तो 2 वास्तविक मूल हैं, यदि 0 है तो 1 वास्तविक मूल है, और यदि < 0 है तो मूल काल्पनिक (complex) हैं।"
        },
        {
            "question": "ax² + bx + c = 0 को हल करने का द्विघात सूत्र (quadratic formula) निम्न में से कौन सा है?",
            "options": ["x = (-b ± √(b² - 4ac)) / (2a)", "x = (-b ± √(b + 4ac)) / a", "x = (b ± √(b² - 4ac)) / 2", "x = -b / (2a)"],
            "correct_answer": "x = (-b ± √(b² - 4ac)) / (2a)",
            "concept": "Quadratic formula",
            "explanation": "मानक द्विघात सूत्र x = (-b ± √(b² - 4ac)) / (2a) है।"
        },
        {
            "question": "यदि x² - 5x + 6 = 0 के मूल p और q हैं, तो p और q के मान क्या हैं?",
            "options": ["2 और 3", "1 और 6", "-2 और -3", "-1 और -6"],
            "correct_answer": "2 और 3",
            "concept": "Factorization",
            "explanation": "गुणनखंड करने पर (x - 2)(x - 3) = 0 मिलता है। इसलिए x = 2 या x = 3।"
        },
        {
            "question": "बहुपद (polynomial) P(x) = 3x³ + 5x² - 7 की घात (degree) क्या है?",
            "options": ["3", "2", "1", "5"],
            "correct_answer": "3",
            "concept": "Polynomial degree",
            "explanation": "बहुपद की घात, चर x की सबसे बड़ी घात होती है, जो यहाँ 3 है।"
        }
    ]


def _science_bank_en(class_level):
    return [
        {
            "question": f"What is the SI unit of force suitable for {class_level} Science?",
            "options": ["Newton (N)", "Joule (J)", "Watt (W)", "Pascal (Pa)"],
            "correct_answer": "Newton (N)",
            "concept": "Units and Measurement",
            "explanation": "Force is measured in Newtons (N) in honor of Sir Isaac Newton."
        },
        {
            "question": "Which organelle is known as the powerhouse of the cell?",
            "options": ["Mitochondria", "Nucleus", "Ribosome", "Golgi apparatus"],
            "correct_answer": "Mitochondria",
            "concept": "Cell structure",
            "explanation": "Mitochondria produce ATP through cellular respiration, earning them the nickname powerhouse of the cell."
        },
        {
            "question": "What is the pH value of pure distilled water at room temperature?",
            "options": ["7 (Neutral)", "0 (Strong Acid)", "14 (Strong Base)", "5 (Weak Acid)"],
            "correct_answer": "7 (Neutral)",
            "concept": "Acids and Bases",
            "explanation": "Pure water has a neutral pH of 7 because H+ and OH- ion concentrations are equal."
        },
        {
            "question": "According to Newton's Second Law of Motion, Force equals:",
            "options": ["Mass × Acceleration (F = ma)", "Mass ÷ Velocity", "Work × Time", "Energy ÷ Distance"],
            "correct_answer": "Mass × Acceleration (F = ma)",
            "concept": "Laws of Motion",
            "explanation": "Newton's Second Law states F = m * a."
        },
        {
            "question": "What process do green plants use to synthesize food using sunlight?",
            "options": ["Photosynthesis", "Respiration", "Transpiration", "Fermentation"],
            "correct_answer": "Photosynthesis",
            "concept": "Plant Physiology",
            "explanation": "Photosynthesis converts carbon dioxide, water, and sunlight into glucose and oxygen."
        }
    ]


def _science_bank_hi(class_level):
    return [
        {
            "question": f"{class_level} विज्ञान (Science) के लिए बल (force) का SI मात्रक क्या है?",
            "options": ["न्यूटन (N)", "जूल (J)", "वाट (W)", "पास्कल (Pa)"],
            "correct_answer": "न्यूटन (N)",
            "concept": "Units and Measurement",
            "explanation": "बल को न्यूटन (N) में मापा जाता है, जो सर आइज़क न्यूटन के सम्मान में रखा गया नाम है।"
        },
        {
            "question": "कोशिका का 'पावरहाउस' किस अंगक (organelle) को कहा जाता है?",
            "options": ["माइटोकॉन्ड्रिया (Mitochondria)", "केंद्रक (Nucleus)", "राइबोसोम (Ribosome)", "गॉल्जी उपकरण"],
            "correct_answer": "माइटोकॉन्ड्रिया (Mitochondria)",
            "concept": "Cell structure",
            "explanation": "माइटोकॉन्ड्रिया कोशिकीय श्वसन के द्वारा ATP का निर्माण करते हैं, इसलिए इन्हें कोशिका का पावरहाउस कहा जाता है।"
        },
        {
            "question": "कमरे के तापमान पर शुद्ध आसुत जल (distilled water) का pH मान क्या होता है?",
            "options": ["7 (उदासीन)", "0 (प्रबल अम्ल)", "14 (प्रबल क्षार)", "5 (दुर्बल अम्ल)"],
            "correct_answer": "7 (उदासीन)",
            "concept": "Acids and Bases",
            "explanation": "शुद्ध जल का pH उदासीन यानी 7 होता है क्योंकि इसमें H+ और OH- आयनों की सांद्रता बराबर होती है।"
        },
        {
            "question": "न्यूटन के गति के दूसरे नियम (Second Law of Motion) के अनुसार, बल (Force) बराबर होता है:",
            "options": ["द्रव्यमान × त्वरण (F = ma)", "द्रव्यमान ÷ वेग", "कार्य × समय", "ऊर्जा ÷ दूरी"],
            "correct_answer": "द्रव्यमान × त्वरण (F = ma)",
            "concept": "Laws of Motion",
            "explanation": "न्यूटन का दूसरा नियम कहता है F = m × a।"
        },
        {
            "question": "हरे पौधे सूर्य के प्रकाश का उपयोग करके भोजन बनाने के लिए कौन सी प्रक्रिया अपनाते हैं?",
            "options": ["प्रकाश संश्लेषण (Photosynthesis)", "श्वसन (Respiration)", "वाष्पोत्सर्जन (Transpiration)", "किण्वन (Fermentation)"],
            "correct_answer": "प्रकाश संश्लेषण (Photosynthesis)",
            "concept": "Plant Physiology",
            "explanation": "प्रकाश संश्लेषण, कार्बन डाइऑक्साइड, जल और सूर्य के प्रकाश को ग्लूकोज़ और ऑक्सीजन में बदलने की प्रक्रिया है।"
        }
    ]


def _generic_bank_en(subject, topic, class_level, difficulty):
    base_bank = []
    for i in range(1, 6):
        base_bank.append({
            "question": f"Question {i} on '{topic}' ({class_level} {subject}): Which core principle applies here?",
            "options": [
                f"Fundamental Concept of {topic}",
                f"Secondary Rule of {subject}",
                f"Alternative Hypothesis in {topic}",
                f"Standard Exception in {class_level}"
            ],
            "correct_answer": f"Fundamental Concept of {topic}",
            "concept": f"{topic} Core Rules",
            "explanation": f"In {class_level} {subject}, the fundamental concept of {topic} is essential for accurate problem solving."
        })
    return base_bank


def _generic_bank_hi(subject, topic, class_level, difficulty):
    base_bank = []
    for i in range(1, 6):
        base_bank.append({
            "question": f"'{topic}' ({class_level} {subject}) पर प्रश्न {i}: यहाँ कौन सा मूल सिद्धांत लागू होता है?",
            "options": [
                f"{topic} की मूल अवधारणा (Fundamental Concept)",
                f"{subject} का द्वितीयक नियम",
                f"{topic} में वैकल्पिक परिकल्पना",
                f"{class_level} में मानक अपवाद"
            ],
            "correct_answer": f"{topic} की मूल अवधारणा (Fundamental Concept)",
            "concept": f"{topic} Core Rules",
            "explanation": f"{class_level} {subject} में, {topic} की मूल अवधारणा को समझना सटीक समस्या-समाधान के लिए आवश्यक है।"
        })
    return base_bank


def generate_quiz_questions(class_level, subject, topic, difficulty, num_questions, language="English", weak_concepts=None):
    if not client:
        return get_fallback_quiz(class_level, subject, topic, difficulty, num_questions, language=language)

    weak_context = ""
    if weak_concepts and len(weak_concepts) > 0:
        weak_context = f"Special Focus: The student previously struggled with these concepts: {', '.join(weak_concepts)}. Make sure to include questions testing these concepts!"

    prompt = f"""
You are an expert school textbook creator and AI tutor for school students in {class_level}.
Generate a school-level quiz in JSON format based on:
- Class/Grade: {class_level}
- Subject: {subject}
- Topic: {topic}
- Target Difficulty Level: {difficulty} (Beginner / Basic / Intermediate / Advanced)
- Number of Questions: {num_questions}
- Language: {language}
{weak_context}

CRITICAL RULES:
1. Return strictly valid JSON containing a key "questions" which is an array of objects.
2. Each question object MUST have:
   - "question": string
   - "options": array of 4 distinct string choices
   - "correct_answer": string (exact match to one of the 4 options)
   - "concept": short 2-4 word concept name (e.g., "Discriminant", "Newton's Second Law", "Factorization")
   - "difficulty": string ("Beginner", "Basic", "Intermediate", or "Advanced")
   - "explanation": string giving concise, student-friendly explanation of why the correct answer is right.
3. Keep language appropriate for {class_level} students.
4. STRICT SUBJECT/TOPIC RULE: every single question MUST be strictly and only about Subject "{subject}", Topic "{topic}".
   Do NOT generate questions about any other subject (for example, if the subject is "Computer Science", do NOT
   generate Physics, Chemistry, Biology or generic "Science" questions — generate programming/computing questions only).
   If "{topic}" is narrow (e.g. "Loops"), every question must specifically test that exact topic
   (e.g. for/while loops, iteration, loop control) and not unrelated topics from the same subject.
5. STRICT LANGUAGE RULE: Generate the ENTIRE quiz — every question, every option, every explanation, and every
   concept name — in {language}. Do not output English unless {language} is English, EXCEPT for technical or
   programming keywords that must stay in their original form (e.g. for, while, break, continue, class, function),
   which may remain in English while the surrounding explanation is written naturally in {language}.
6. Also include top-level keys "echo_subject" and "echo_topic" that restate the Subject and Topic given above
   exactly, so the caller can verify the quiz matches what was requested.
"""

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful school education API that returns strict JSON format only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        data = json.loads(clean_json_string(content))

        questions_ok = "questions" in data and isinstance(data["questions"], list) and len(data["questions"]) > 0

        # Lightweight subject/topic validation: reject and fall back to the
        # (now-correct) offline bank rather than showing a mismatched quiz.
        echo_subject = str(data.get("echo_subject", subject)).strip().lower()
        echo_topic = str(data.get("echo_topic", topic)).strip().lower()
        subject_ok = subject.strip().lower() in echo_subject or echo_subject in subject.strip().lower()
        topic_ok = topic.strip().lower() in echo_topic or echo_topic in topic.strip().lower()

        if questions_ok and subject_ok and topic_ok:
            return data
        else:
            logger.warning(
                f"AI quiz output failed subject/topic validation "
                f"(requested {subject}/{topic}, got {echo_subject}/{echo_topic}). Using fallback bank."
            )
            return get_fallback_quiz(class_level, subject, topic, difficulty, num_questions, language=language)
    except Exception as e:
        logger.error(f"Error calling OpenAI API for quiz generation: {e}")
        return get_fallback_quiz(class_level, subject, topic, difficulty, num_questions, language=language)


def explain_mistake(class_level, question_text, selected_ans, correct_ans, concept, explanation_base="", language="English"):
    if not client:
        is_hindi = language.strip().lower().startswith("hindi") or language.strip() == "हिंदी"
        if is_hindi:
            return {
                "correct_answer": correct_ans,
                "your_choice": selected_ans,
                "why_incorrect": f"आपने '{selected_ans}' चुना, लेकिन सही उत्तर '{correct_ans}' है। यह गलती किसी मुख्य चरण या अवधारणा को छोड़ने के कारण हुई।",
                "concept_name": concept,
                "simple_explanation": f"{class_level} में, {concept} को समझने के लिए समस्या को चरण-दर-चरण हल करना ज़रूरी है।",
                "step_by_step_reasoning": [
                    f"1. प्रश्न में दिए गए शब्दों को पहचानें: '{question_text}'।",
                    f"2. {concept} के लिए मूल सूत्र या नियम लागू करें।",
                    f"3. गणना किए गए मान की तुलना उपलब्ध विकल्पों से करें और '{correct_ans}' चुनें।"
                ],
                "real_life_example": f"{concept} को एक रेसिपी की तरह समझें — यदि आप एक भी चरण छोड़ते हैं, तो परिणाम बदल जाता है!",
                "common_mistake": "छात्र अक्सर समीकरण के दोनों ओर पद ले जाते समय चिन्ह बदलना भूल जाते हैं या गणना के क्रम में गलती कर देते हैं।",
                "memory_tip": f"💡 याद रखें: अंतिम उत्तर चुनने से पहले हमेशा {concept} के नियमों की दोबारा जाँच करें!",
                "practice_question": {
                    "question": f"त्वरित जाँच: {concept} लागू करते समय मुख्य नियम क्या है?",
                    "options": ["दोनों पक्षों को हमेशा समान रखें", "ऋणात्मक चिन्हों को अनदेखा करें", "कोष्ठक से पहले भाग करें", "सब कुछ 0 से गुणा करें"],
                    "correct_answer": "दोनों पक्षों को हमेशा समान रखें",
                    "explanation": "दोनों पक्षों को संतुलित रखने से समीकरण की समानता बनी रहती है!"
                }
            }
        return {
            "correct_answer": correct_ans,
            "your_choice": selected_ans,
            "why_incorrect": f"You chose '{selected_ans}', but the correct answer is '{correct_ans}'. The mistake happened by missing key algebraic or conceptual steps.",
            "concept_name": concept,
            "simple_explanation": f"In {class_level}, understanding {concept} requires breaking the problem down step by step.",
            "step_by_step_reasoning": [
                f"1. Identify the given terms in the question: '{question_text}'.",
                f"2. Apply the fundamental formula or rule for {concept}.",
                f"3. Compare calculated value with available options to select '{correct_ans}'."
            ],
            "real_life_example": f"Think of {concept} like following a recipe—if you skip balancing the equation, the result changes!",
            "common_mistake": "Students often forget to swap signs when moving terms across the equals sign or miscalculate order of operations.",
            "memory_tip": f"💡 Remember: Always double-check {concept} rules before finalizing your choice!",
            "practice_question": {
                "question": f"Quick Check: What is the primary rule when applying {concept}?",
                "options": ["Always balance both sides equally", "Ignore negative signs", "Divide before parenthesis", "Multiply everything by 0"],
                "correct_answer": "Always balance both sides equally",
                "explanation": "Balancing both sides preserves equality!"
            }
        }

    prompt = f"""
You are an encouraging school tutor for a student in {class_level}.
The student answered a quiz question incorrectly. Generate a comprehensive "Explain My Mistake" guide in JSON format.

Question: "{question_text}"
Student's Incorrect Answer: "{selected_ans}"
Correct Answer: "{correct_ans}"
Concept Involved: "{concept}"
Base Explanation: "{explanation_base}"
Language: {language}

STRICT LANGUAGE RULE: Write every string value in {language}. Do not output English unless {language} is English,
except for technical/programming keywords that must stay in their original form.

Return a strict JSON object with the following keys:
- "correct_answer": string
- "your_choice": string
- "why_incorrect": string (clear explanation of why student's choice was wrong and where the mistake likely occurred)
- "concept_name": string
- "simple_explanation": string (very simple 2-3 sentence explanation of the concept for a {class_level} student)
- "step_by_step_reasoning": list of strings (3-4 step-by-step reasoning points)
- "real_life_example": string (relatable example or analogy)
- "common_mistake": string (what students frequently mess up here)
- "memory_tip": string (a catchy tip or mnemonic)
- "practice_question": object with "question", "options" (array of 4 choices), "correct_answer", and "explanation"
"""

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a friendly AI tutor API returning JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        return json.loads(clean_json_string(content))
    except Exception as e:
        logger.error(f"Error in explain_mistake AI call: {e}")
        return {
            "correct_answer": correct_ans,
            "your_choice": selected_ans,
            "why_incorrect": f"You selected '{selected_ans}', but '{correct_ans}' is correct.",
            "concept_name": concept,
            "simple_explanation": f"Let me break down {concept} simply for {class_level}.",
            "step_by_step_reasoning": ["Step 1: Read carefully.", f"Step 2: Note that {correct_ans} satisfies the equation."],
            "real_life_example": "Practice makes perfect!",
            "common_mistake": "Rushing through calculation steps.",
            "memory_tip": "💡 Tip: Write out all steps on scratch paper!",
            "practice_question": {
                "question": f"Quick Check on {concept}: Which option is correct?",
                "options": [correct_ans, "Incorrect Option A", "Incorrect Option B", "Incorrect Option C"],
                "correct_answer": correct_ans,
                "explanation": "This directly reinforces the concept."
            }
        }


def generate_personalized_practice(class_level, subject, topic, weak_concepts, target_difficulty, num_questions=5, language="English"):
    # Pass weak_concepts to quiz generator
    return generate_quiz_questions(
        class_level=class_level,
        subject=subject,
        topic=topic,
        difficulty=target_difficulty,
        num_questions=num_questions,
        language=language,
        weak_concepts=weak_concepts
    )


def generate_study_plan(class_level, duration_days, weak_concepts, subject_topics, language="English"):
    if not client:
        # Generate robust mock plan for 7, 14, or 30 days
        plan_days = []
        concepts_to_use = weak_concepts if (weak_concepts and len(weak_concepts) > 0) else ["Fundamentals", "Core Concepts", "Problem Solving", "Advanced Application"]
        
        for d in range(1, duration_days + 1):
            concept = concepts_to_use[(d - 1) % len(concepts_to_use)]
            if d == 1:
                title = f"Day 1: Concept Mastery - {concept}"
                desc = f"Read textbook overview and review core definitions for {concept} in {class_level} curriculum."
            elif d == duration_days:
                title = f"Day {d}: Final AI Assessment & Mastery Test"
                desc = "Take a full mixed practice test on all target weak areas to confirm 90%+ mastery."
            elif d % 3 == 0:
                title = f"Day {d}: Weak Area Targeted Practice"
                desc = f"Solve 10 targeted practice questions specifically on {concept} and review explanations."
            else:
                title = f"Day {d}: Solved Examples & Step-by-Step Breakdown"
                desc = f"Work through 5 step-by-step solved examples focusing on {concept}."
                
            plan_days.append({
                "day_number": d,
                "title": title,
                "description": desc,
                "concept": concept,
                "is_completed": False
            })
            
        return {
            "duration": duration_days,
            "title": f"{duration_days}-Day Smart Study Plan for {class_level}",
            "days": plan_days
        }

    prompt = f"""
Generate a personalized {duration_days}-day study plan for a school student in {class_level}.
Student's weak concepts to focus on: {', '.join(weak_concepts) if weak_concepts else 'General Core Curriculum'}
Subjects/Topics: {subject_topics}
Language: {language}

Return a strict JSON object with:
- "duration": integer ({duration_days})
- "title": string (e.g. "{duration_days}-Day Smart AI Study Plan")
- "days": array of objects for each day from Day 1 to Day {duration_days}. Each object MUST have:
  - "day_number": integer
  - "title": string (e.g. "Day 1: Quadratic Formula - Concept Learning")
  - "description": string (clear actionable task)
  - "concept": string
"""

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a school study planner API returning strict JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        return json.loads(clean_json_string(content))
    except Exception as e:
        logger.error(f"Error in generate_study_plan AI call: {e}")
        return generate_study_plan(class_level, duration_days, weak_concepts, subject_topics, language)


def ask_ai_tutor(class_level, user_query, conversation_history=None, language="English"):
    if not client:
        is_hindi = language.strip().lower().startswith("hindi") or language.strip() == "हिंदी"
        if is_hindi:
            return f"🤖 **SmartLearn AI ट्यूटर ({class_level})**:\n\n'{user_query}' के बारे में बढ़िया सवाल है!\n\n{class_level} में, मुख्य विचार यह है कि चीज़ों को चरण-दर-चरण हल करें। समस्या को छोटे हिस्सों में बाँटें, दिया गया डेटा पहचानें, मुख्य सूत्र या नियम लागू करें, और अपने उत्तर की जाँच करें!\n\nक्या आप चाहेंगे कि मैं इस विषय पर 3 प्रश्नों का त्वरित अभ्यास सेट बनाऊँ?"
        return f"🤖 **SmartLearn AI Tutor ({class_level})**:\n\nGreat question about '{user_query}'!\n\nIn {class_level}, the key idea is to take things step-by-step. Break the problem into small parts, identify what is given, use the core formula or rule, and verify your answer!\n\nWould you like me to generate a 3-question quick practice set on this topic?"

    messages = [
        {
            "role": "system",
            "content": f"You are 'Ask SmartLearn AI', a friendly, encouraging, and highly knowledgeable AI tutor for school students in {class_level}. Use clear, simple language, step-by-step reasoning, markdown formatting, emojis, real-life analogies, and quick check questions. Respond in {language}."
        }
    ]
    
    if conversation_history:
        for msg in conversation_history[-6:]:
            messages.append(msg)
            
    messages.append({"role": "user", "content": user_query})

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error calling OpenAI API for chatbot: {e}")
        return f"🤖 **SmartLearn AI Tutor**:\n\nI'm currently running in Demo Mode. Here is the key insight for '{user_query}': Always start by writing down what you know, identifying the core concept, and checking each step!"
