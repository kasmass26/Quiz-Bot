from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import requests  # type: ignore

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ─────────────────────────────────────────────
# Environment Setup
# ─────────────────────────────────────────────

def load_local_env():
    if os.environ.get("VERCEL"):
        return
    env_path = os.path.join(BASE_DIR, ".env")
    try:
        with open(env_path, encoding="utf-8") as env_file:
            for line in env_file:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                if key.startswith("export "):
                    key = key[7:].strip()
                if key and key not in os.environ:
                    os.environ[key] = value.strip().strip("'\"")
    except FileNotFoundError:
        pass


load_local_env()
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}" if BOT_TOKEN else None


# ─────────────────────────────────────────────
# App Content Data
# ─────────────────────────────────────────────

COURSES = [
    {
        "id": "python_basics",
        "emoji": "🐍",
        "title": "Python Basics",
        "description": "Variables, data types, loops, and functions.",
        "lessons": [
            "📌 Lesson 1 – Variables & Data Types",
            "📌 Lesson 2 – Conditionals (if/else)",
            "📌 Lesson 3 – Loops (for & while)",
            "📌 Lesson 4 – Functions & Scope",
            "📌 Lesson 5 – Modules & Packages",
        ]
    },
    {
        "id": "oop",
        "emoji": "🏗️",
        "title": "Object-Oriented Programming",
        "description": "Classes, inheritance, polymorphism, and more.",
        "lessons": [
            "📌 Lesson 1 – Classes & Objects",
            "📌 Lesson 2 – Constructors & Attributes",
            "📌 Lesson 3 – Inheritance",
            "📌 Lesson 4 – Polymorphism & Overriding",
            "📌 Lesson 5 – Encapsulation & Abstraction",
        ]
    },
    {
        "id": "data_structures",
        "emoji": "📦",
        "title": "Data Structures",
        "description": "Lists, stacks, queues, trees, and graphs.",
        "lessons": [
            "📌 Lesson 1 – Lists & Tuples",
            "📌 Lesson 2 – Dictionaries & Sets",
            "📌 Lesson 3 – Stacks & Queues",
            "📌 Lesson 4 – Linked Lists",
            "📌 Lesson 5 – Trees & Graphs",
        ]
    },
    {
        "id": "web_dev",
        "emoji": "🌐",
        "title": "Web Development",
        "description": "HTML, CSS, Flask, and REST APIs.",
        "lessons": [
            "📌 Lesson 1 – HTML & CSS Essentials",
            "📌 Lesson 2 – Intro to Flask",
            "📌 Lesson 3 – Routes & Templates",
            "📌 Lesson 4 – REST APIs",
            "📌 Lesson 5 – Deploying with Vercel",
        ]
    },
]

QUIZ_QUESTIONS = [
    {
        "question": "1️⃣ What is the output of `print(2 ** 3)` in Python?",
        "options": ["6", "8", "9", "12"],
        "correct": 1,
        "explanation": "The `**` operator in Python is for exponentiation. 2 raised to the power of 3 = 2×2×2 = 8."
    },
    {
        "question": "2️⃣ Which of these data types is immutable?",
        "options": ["List", "Dictionary", "Set", "Tuple"],
        "correct": 3,
        "explanation": "Tuples are immutable — their elements cannot be changed after creation. Lists, Dictionaries, and Sets are mutable."
    },
    {
        "question": "3️⃣ What is the correct way to create a function in Python?",
        "options": ["function myFunc():", "def myFunc():", "create myFunc():", "func myFunc():"],
        "correct": 1,
        "explanation": "In Python, use the `def` keyword followed by the function name and parentheses to define a function."
    },
    {
        "question": "4️⃣ Which keyword is used to handle exceptions in Python?",
        "options": ["catch", "handle", "try", "except"],
        "correct": 2,
        "explanation": "The `try` block lets you test code for errors; the `except` block handles the error."
    },
    {
        "question": "5️⃣ What does `len([1, 2, 3])` return?",
        "options": ["2", "3", "4", "1"],
        "correct": 1,
        "explanation": "`len()` returns the number of items in an object. The list has 3 items, so it returns 3."
    },
]


# ─────────────────────────────────────────────
# Main Keyboard (Persistent Bottom Bar)
# ─────────────────────────────────────────────

MAIN_KEYBOARD = {
    "keyboard": [
        [{"text": "🏠 Home"}, {"text": "📚 Courses"}],
        [{"text": "❓ Help"}, {"text": "ℹ️ About"}],
    ],
    "resize_keyboard": True,
    "persistent": True,
}


# ─────────────────────────────────────────────
# Webhook Handler
# ─────────────────────────────────────────────

class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        status = "configured" if BOT_TOKEN else "missing"
        self.wfile.write(f"Bot is running. BOT_TOKEN is {status}.".encode("utf-8"))

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            update = json.loads(body)

            # ── Text / Command Messages ──────────────────────────
            if "message" in update:
                msg = update["message"]
                chat_id = msg.get("chat", {}).get("id")
                first_name = msg.get("from", {}).get("first_name", "there")
                text = msg.get("text", "")

                if text.startswith("/start"):
                    show_home(chat_id, first_name)

                # ── Bottom Navigation Bar ────────────────────────
                elif text == "🏠 Home":
                    show_home(chat_id, first_name)
                elif text == "📚 Courses":
                    show_courses(chat_id)
                elif text == "❓ Help":
                    show_help(chat_id)
                elif text == "ℹ️ About":
                    show_about(chat_id)

                # ── Legacy commands ──────────────────────────────
                elif text.startswith("/quiz"):
                    start_quiz(chat_id)
                elif text.startswith("/courses"):
                    show_courses(chat_id)

            # ── Inline Button Callbacks ──────────────────────────
            elif "callback_query" in update:
                cq = update["callback_query"]
                chat_id = cq["message"]["chat"]["id"]
                message_id = cq["message"]["message_id"]
                data = cq.get("data", "")
                handle_callback(chat_id, message_id, data, cq["id"])

        except json.JSONDecodeError as e:
            print("BAD_JSON:", str(e))
        except Exception as e:
            print("ERROR:", str(e))

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass  # Silence default request logging


# ─────────────────────────────────────────────
# Page Renderers
# ─────────────────────────────────────────────

def show_home(chat_id, first_name="there"):
    text = (
        f"👋 Welcome back, *{first_name}*!\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🎓 *Python Learning Bot*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Your all-in-one bot for learning Python programming. "
        "Explore courses, test yourself with quizzes, and track your progress!\n\n"
        "*What would you like to do?*"
    )
    keyboard = {
        "inline_keyboard": [
            [{"text": "📚 Browse Courses", "callback_data": "page:courses"}],
            [{"text": "🧠 Take a Quiz", "callback_data": "page:quiz"}],
            [{"text": "❓ Help", "callback_data": "page:help"}],
        ]
    }
    send_message(chat_id, text, reply_markup=MAIN_KEYBOARD, parse_mode="Markdown")
    send_message(chat_id, "👇 *Quick Actions:*", reply_markup=keyboard, parse_mode="Markdown")


def show_courses(chat_id):
    text = (
        "📚 *Available Courses*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Choose a course to see its lessons:\n"
    )
    keyboard_rows = []
    for course in COURSES:
        keyboard_rows.append([{
            "text": f"{course['emoji']} {course['title']}",
            "callback_data": f"course:{course['id']}"
        }])
    keyboard_rows.append([{"text": "🏠 Back to Home", "callback_data": "page:home"}])

    send_message(chat_id, text, reply_markup={"inline_keyboard": keyboard_rows}, parse_mode="Markdown")


def show_course_detail(chat_id, message_id, course_id):
    course = next((c for c in COURSES if c["id"] == course_id), None)
    if not course:
        return

    lessons_text = "\n".join(course["lessons"])
    text = (
        f"{course['emoji']} *{course['title']}*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 _{course['description']}_\n\n"
        f"*Lessons:*\n{lessons_text}\n\n"
        f"🧠 Ready to test your knowledge?"
    )
    keyboard = {
        "inline_keyboard": [
            [{"text": "🧠 Take Quiz for this Course", "callback_data": "page:quiz"}],
            [{"text": "⬅️ Back to Courses", "callback_data": "page:courses"}],
        ]
    }
    edit_message(chat_id, message_id, text, reply_markup=keyboard, parse_mode="Markdown")


def show_help(chat_id):
    text = (
        "❓ *Help & Commands*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "*Navigation:*\n"
        "• 🏠 Home — Main menu\n"
        "• 📚 Courses — Browse all courses\n"
        "• ❓ Help — This page\n"
        "• ℹ️ About — About this bot\n\n"
        "*Commands:*\n"
        "• /start — Restart & show home\n"
        "• /courses — Browse courses\n"
        "• /quiz — Start a quiz\n\n"
        "*How to use:*\n"
        "Use the buttons at the bottom of your screen to navigate. "
        "Tap any course to see its lessons, or jump into a quiz to test your knowledge!"
    )
    keyboard = {
        "inline_keyboard": [
            [{"text": "📚 Go to Courses", "callback_data": "page:courses"}],
            [{"text": "🧠 Start Quiz", "callback_data": "page:quiz"}],
        ]
    }
    send_message(chat_id, text, reply_markup=keyboard, parse_mode="Markdown")


def show_about(chat_id):
    text = (
        "ℹ️ *About This Bot*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🤖 *Python Learning Bot* is an interactive Telegram-based platform for learning Python programming.\n\n"
        "*Features:*\n"
        "✅ Structured courses with lessons\n"
        "✅ Multiple-choice quizzes with explanations\n"
        "✅ Score tracking per quiz session\n"
        "✅ Easy navigation with a persistent menu\n\n"
        "*Built with:* Python · Telegram Bot API · Vercel\n\n"
        "📬 Questions or feedback? Contact the developer!"
    )
    keyboard = {
        "inline_keyboard": [
            [{"text": "🏠 Go to Home", "callback_data": "page:home"}],
        ]
    }
    send_message(chat_id, text, reply_markup=keyboard, parse_mode="Markdown")


# ─────────────────────────────────────────────
# Quiz Logic
# ─────────────────────────────────────────────

def start_quiz(chat_id):
    text = (
        "🧠 *Quiz Time!*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"You'll be asked *{len(QUIZ_QUESTIONS)} questions* about Python.\n"
        "Pick the best answer for each one. Good luck! 🚀"
    )
    keyboard = {
        "inline_keyboard": [
            [{"text": "▶️ Start Quiz!", "callback_data": "next:0:0"}],
            [{"text": "⬅️ Back to Home", "callback_data": "page:home"}],
        ]
    }
    send_message(chat_id, text, reply_markup=keyboard, parse_mode="Markdown")


def send_question(chat_id, q_idx, score):
    if q_idx >= len(QUIZ_QUESTIONS):
        show_final_score(chat_id, score)
        return

    q_data = QUIZ_QUESTIONS[q_idx]
    progress = f"Question {q_idx + 1}/{len(QUIZ_QUESTIONS)} • Score: {score}"
    text = f"📊 _{progress}_\n\n*{q_data['question']}*"

    keyboard = []
    for i, opt in enumerate(q_data["options"]):
        callback_data = f"ans:{q_idx}:{score}:{i}"
        keyboard.append([{"text": opt, "callback_data": callback_data}])

    send_message(chat_id, text, reply_markup={"inline_keyboard": keyboard}, parse_mode="Markdown")


def show_final_score(chat_id, score):
    total = len(QUIZ_QUESTIONS)
    pct = int((score / total) * 100)

    if pct == 100:
        grade, badge = "Outstanding!", "🥇"
    elif pct >= 80:
        grade, badge = "Great Job!", "🥈"
    elif pct >= 60:
        grade, badge = "Good Effort!", "🥉"
    else:
        grade, badge = "Keep Practicing!", "📖"

    text = (
        f"🏆 *Quiz Complete!*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{badge} *{grade}*\n\n"
        f"Your Score: *{score}/{total}* ({pct}%)\n\n"
        f"{'⭐' * score}{'☆' * (total - score)}"
    )
    keyboard = {
        "inline_keyboard": [
            [{"text": "🔄 Try Again", "callback_data": "next:0:0"}],
            [{"text": "📚 Browse Courses", "callback_data": "page:courses"}],
            [{"text": "🏠 Home", "callback_data": "page:home"}],
        ]
    }
    send_message(chat_id, text, reply_markup=keyboard, parse_mode="Markdown")


def handle_callback(chat_id, message_id, data, cb_id):
    answer_callback_query(cb_id)

    parts = data.split(":")
    action = parts[0]

    # ── Page Navigation ─────────────────────────────
    if action == "page":
        page = parts[1]
        if page == "home":
            # Re-send home inline actions (keep bottom bar intact)
            text = "👇 *Quick Actions:*"
            keyboard = {
                "inline_keyboard": [
                    [{"text": "📚 Browse Courses", "callback_data": "page:courses"}],
                    [{"text": "🧠 Take a Quiz", "callback_data": "page:quiz"}],
                    [{"text": "❓ Help", "callback_data": "page:help"}],
                ]
            }
            edit_message(chat_id, message_id, text, reply_markup=keyboard, parse_mode="Markdown")
        elif page == "courses":
            text = (
                "📚 *Available Courses*\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "Choose a course to see its lessons:\n"
            )
            keyboard_rows = []
            for course in COURSES:
                keyboard_rows.append([{
                    "text": f"{course['emoji']} {course['title']}",
                    "callback_data": f"course:{course['id']}"
                }])
            keyboard_rows.append([{"text": "🏠 Back to Home", "callback_data": "page:home"}])
            edit_message(chat_id, message_id, text, reply_markup={"inline_keyboard": keyboard_rows}, parse_mode="Markdown")
        elif page == "quiz":
            text = (
                "🧠 *Quiz Time!*\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                f"You'll be asked *{len(QUIZ_QUESTIONS)} questions* about Python.\n"
                "Pick the best answer for each one. Good luck! 🚀"
            )
            keyboard = {
                "inline_keyboard": [
                    [{"text": "▶️ Start Quiz!", "callback_data": "next:0:0"}],
                    [{"text": "⬅️ Back to Home", "callback_data": "page:home"}],
                ]
            }
            edit_message(chat_id, message_id, text, reply_markup=keyboard, parse_mode="Markdown")
        elif page == "help":
            text = (
                "❓ *Help & Commands*\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "*Navigation:*\n"
                "• 🏠 Home — Main menu\n"
                "• 📚 Courses — Browse all courses\n"
                "• ❓ Help — This page\n"
                "• ℹ️ About — About this bot\n\n"
                "*Commands:*\n"
                "• /start — Restart & show home\n"
                "• /courses — Browse courses\n"
                "• /quiz — Start a quiz\n\n"
                "*How to use:*\n"
                "Use the bottom buttons to navigate. "
                "Tap any course to view lessons, or start a quiz to test your knowledge!"
            )
            keyboard = {
                "inline_keyboard": [
                    [{"text": "📚 Go to Courses", "callback_data": "page:courses"}],
                    [{"text": "🧠 Start Quiz", "callback_data": "page:quiz"}],
                    [{"text": "🏠 Back to Home", "callback_data": "page:home"}],
                ]
            }
            edit_message(chat_id, message_id, text, reply_markup=keyboard, parse_mode="Markdown")

    # ── Course Detail ───────────────────────────────
    elif action == "course":
        course_id = parts[1]
        show_course_detail(chat_id, message_id, course_id)

    # ── Quiz: Answer ────────────────────────────────
    elif action == "ans":
        q_idx = int(parts[1])
        score = int(parts[2])
        selected_idx = int(parts[3])

        q_data = QUIZ_QUESTIONS[q_idx]
        is_correct = (selected_idx == q_data["correct"])
        new_score = score + 1 if is_correct else score

        result_icon = "✅" if is_correct else "❌"
        result_label = "Correct!" if is_correct else "Incorrect."
        correct_opt = q_data["options"][q_data["correct"]]

        text = (
            f"{result_icon} *{result_label}*\n\n"
            f"The correct answer was: *{correct_opt}*\n\n"
            f"💡 *Explanation:*\n{q_data['explanation']}"
        )

        next_q_idx = q_idx + 1
        btn_label = "Next Question ➡️" if next_q_idx < len(QUIZ_QUESTIONS) else "See Final Score 🏁"
        keyboard = {
            "inline_keyboard": [
                [{"text": btn_label, "callback_data": f"next:{next_q_idx}:{new_score}"}]
            ]
        }
        edit_message(chat_id, message_id, text, reply_markup=keyboard, parse_mode="Markdown")

    # ── Quiz: Next Question ─────────────────────────
    elif action == "next":
        q_idx = int(parts[1])
        score = int(parts[2])
        send_question(chat_id, q_idx, score)


# ─────────────────────────────────────────────
# Telegram API Helpers
# ─────────────────────────────────────────────

def send_message(chat_id, text, reply_markup=None, parse_mode=None):
    if not TELEGRAM_API_URL:
        return False
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    if parse_mode:
        payload["parse_mode"] = parse_mode
    try:
        requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload, timeout=10).raise_for_status()
        return True
    except Exception as e:
        print("SEND_ERROR:", str(e))
        return False


def edit_message(chat_id, message_id, text, reply_markup=None, parse_mode=None):
    if not TELEGRAM_API_URL:
        return False
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    if parse_mode:
        payload["parse_mode"] = parse_mode
    try:
        requests.post(f"{TELEGRAM_API_URL}/editMessageText", json=payload, timeout=10).raise_for_status()
        return True
    except Exception as e:
        print("EDIT_ERROR:", str(e))
        return False


def answer_callback_query(callback_query_id):
    if not TELEGRAM_API_URL:
        return False
    try:
        requests.post(
            f"{TELEGRAM_API_URL}/answerCallbackQuery",
            json={"callback_query_id": callback_query_id},
            timeout=10,
        )
        return True
    except Exception:
        return False


# ─────────────────────────────────────────────
# Local Dev Server
# ─────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    server = HTTPServer(("", port), handler)
    print(f"Serving webhook locally on http://localhost:{port}")
    server.serve_forever()
