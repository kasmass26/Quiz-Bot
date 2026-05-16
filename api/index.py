from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import requests  # type: ignore

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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

# Quiz Data
QUIZ_QUESTIONS = [
    {
        "question": "1. What is the output of `print(2 ** 3)` in Python?",
        "options": ["6", "8", "9", "12"],
        "correct": 1,
        "explanation": "The `**` operator in Python is for exponentiation. 2 raised to the power of 3 is 2*2*2 = 8."
    },
    {
        "question": "2. Which of these data types is immutable?",
        "options": ["List", "Dictionary", "Set", "Tuple"],
        "correct": 3,
        "explanation": "Tuples are immutable, meaning their elements cannot be changed after creation. Lists, Dictionaries, and Sets are mutable."
    },
    {
        "question": "3. What is the correct way to create a function in Python?",
        "options": ["function myFunc():", "def myFunc():", "create myFunc():", "func myFunc():"],
        "correct": 1,
        "explanation": "In Python, you use the `def` keyword followed by the function name and parentheses to define a function."
    },
    {
        "question": "4. Which keyword is used to handle exceptions in Python?",
        "options": ["catch", "handle", "try", "except"],
        "correct": 2,
        "explanation": "The `try` block lets you test a block of code for errors, while the `except` block lets you handle the error."
    }
]


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

        token_status = "configured" if os.environ.get("BOT_TOKEN") else "missing"
        self.wfile.write(
            f"Bot webhook is running. BOT_TOKEN is {token_status}.".encode("utf-8")
        )

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            update = json.loads(body)

            # Handle Messages
            if "message" in update:
                message = update["message"]
                chat_id = message.get("chat", {}).get("id")
                text = message.get("text", "")

                if text.startswith("/start"):
                    send_message(chat_id, "Welcome to the Python Quiz Bot! 🐍\n\nUse /quiz to start a new session.")
                elif text.startswith("/quiz"):
                    start_quiz(chat_id)

            # Handle Callback Queries (Button Clicks)
            elif "callback_query" in update:
                callback_query = update["callback_query"]
                chat_id = callback_query["message"]["chat"]["id"]
                message_id = callback_query["message"]["message_id"]
                data = callback_query.get("data", "")

                handle_callback(chat_id, message_id, data, callback_query["id"])

        except json.JSONDecodeError as e:
            print("BAD_JSON:", str(e))
        except Exception as e:
            print("ERROR:", str(e))

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")


def start_quiz(chat_id):
    """Starts the quiz by sending the first question."""
    send_question(chat_id, 0, 0)


def send_question(chat_id, q_idx, score):
    """Sends a specific question with options."""
    if q_idx >= len(QUIZ_QUESTIONS):
        send_message(chat_id, f"🏆 Quiz Finished!\n\nYour final score: *{score}/{len(QUIZ_QUESTIONS)}*", parse_mode="Markdown")
        return

    q_data = QUIZ_QUESTIONS[q_idx]
    text = f"*{q_data['question']}*"

    keyboard = []
    for i, opt in enumerate(q_data["options"]):
        # Callback data format: ans:{question_index}:{current_score}:{selected_option_index}
        callback_data = f"ans:{q_idx}:{score}:{i}"
        keyboard.append([{"text": opt, "callback_data": callback_data}])

    reply_markup = {"inline_keyboard": keyboard}
    send_message(chat_id, text, reply_markup=reply_markup, parse_mode="Markdown")


def handle_callback(chat_id, message_id, data, cb_id):
    """Processes the user's answer or navigation."""
    answer_callback_query(cb_id)  # Remove loading state from button

    parts = data.split(":")
    action = parts[0]

    if action == "ans":
        q_idx = int(parts[1])
        score = int(parts[2])
        selected_idx = int(parts[3])

        q_data = QUIZ_QUESTIONS[q_idx]
        is_correct = (selected_idx == q_data["correct"])
        new_score = score + 1 if is_correct else score

        result_text = "✅ *Correct!*" if is_correct else "❌ *Incorrect.*"
        correct_opt = q_data["options"][q_data["correct"]]
        
        explanation_text = (
            f"{result_text}\n\n"
            f"The correct answer was: *{correct_opt}*\n\n"
            f"💡 *Explanation:*\n{q_data['explanation']}"
        )

        # Next button
        next_q_idx = q_idx + 1
        keyboard = [[{"text": "Next Question ➡️" if next_q_idx < len(QUIZ_QUESTIONS) else "See Final Score 🏁", 
                      "callback_data": f"next:{next_q_idx}:{new_score}"}]]
        
        edit_message(chat_id, message_id, explanation_text, reply_markup={"inline_keyboard": keyboard}, parse_mode="Markdown")

    elif action == "next":
        q_idx = int(parts[1])
        score = int(parts[2])
        # Delete the explanation message to keep chat clean (optional) or just send new
        send_question(chat_id, q_idx, score)


def send_message(chat_id, text, reply_markup=None, parse_mode=None):
    if not TELEGRAM_API_URL:
        return False
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    if parse_mode:
        payload["parse_mode"] = parse_mode

    try:
        requests.post(url, json=payload, timeout=10).raise_for_status()
        return True
    except Exception as e:
        print("SEND_ERROR:", str(e))
        return False


def edit_message(chat_id, message_id, text, reply_markup=None, parse_mode=None):
    if not TELEGRAM_API_URL:
        return False
    url = f"{TELEGRAM_API_URL}/editMessageText"
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    if parse_mode:
        payload["parse_mode"] = parse_mode

    try:
        requests.post(url, json=payload, timeout=10).raise_for_status()
        return True
    except Exception as e:
        print("EDIT_ERROR:", str(e))
        return False


def answer_callback_query(callback_query_id):
    if not TELEGRAM_API_URL:
        return False
    url = f"{TELEGRAM_API_URL}/answerCallbackQuery"
    payload = {"callback_query_id": callback_query_id}
    try:
        requests.post(url, json=payload, timeout=10)
        return True
    except:
        return False


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    server = HTTPServer(("", port), handler)
    print(f"Serving webhook locally on http://localhost:{port}")
    server.serve_forever()

