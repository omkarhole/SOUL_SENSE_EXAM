import sqlite3
import tkinter as tk
from tkinter import messagebox
import time

import os
import sys

# Add the app directory to the path so we can import i18n_manager
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
from app.i18n_manager import get_i18n

# ================= DATABASE SETUP =================
# Use absolute path relative to the project root for consistency
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "soulsense.db")

# Import and initialize connection manager for TIME_WAIT prevention
from app.db_connection_manager import init_database_schema, execute_query, execute_write

# Initialize database schema using connection pooling
init_database_schema()

# Load language preference
result = execute_query("SELECT value FROM app_settings WHERE key = 'language'")
language = result[0][0] if result else 'en'

# Initialize i18n manager with saved language
i18n = get_i18n()
i18n.switch_language(language)

# ================= QUESTIONS =================
questions = [
    {"text": "You can recognize your emotions as they happen.", "age_min": 12, "age_max": 25},
    {"text": "You find it easy to understand why you feel a certain way.", "age_min": 14, "age_max": 30},
    {"text": "You can control your emotions even in stressful situations.", "age_min": 15, "age_max": 35},
    {"text": "You reflect on your emotional reactions to situations.", "age_min": 13, "age_max": 28},
    {"text": "You are aware of how your emotions affect others.", "age_min": 16, "age_max": 40}
]

# ================= ANALYTICS =================
def compute_analytics(responses, time_taken, total_questions):
    n = len(responses)
    if n == 0:
        return {
            "avg": 0, "max": 0, "min": 0, "variance": 0,
            "attempted": 0, "completion": 0, "avg_time": 0
        }

    avg = sum(responses) / n
    variance = sum((x - avg) ** 2 for x in responses) / n

    return {
        "avg": round(avg, 2),
        "max": max(responses),
        "min": min(responses),
        "variance": round(variance, 2),
        "attempted": n,
        "completion": round(n / total_questions, 2),
        "avg_time": round(time_taken / n, 2)
    }

# ================= SPLASH SCREEN =================
def show_splash():
    splash = tk.Tk()
    splash.title(i18n.get("app_title"))
    
    # Responsive sizing for splash screen
    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()
    window_width = min(500, int(screen_width * 0.3))
    window_height = min(300, int(screen_height * 0.3))
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    
    splash.geometry(f"{window_width}x{window_height}+{x}+{y}")
    splash.configure(bg="#1E1E2F")
    splash.minsize(400, 250)
    splash.resizable(True, True)

    tk.Label(
        splash,
        text=i18n.get("app_title"),
        font=("Arial", 32, "bold"),
        fg="white",
        bg="#1E1E2F"
    ).pack(pady=40)

    tk.Label(
        splash,
        text=i18n.get("welcome_message"),
        font=("Arial", 14),
        fg="#CCCCCC",
        bg="#1E1E2F"
    ).pack()

    tk.Label(
        splash,
        text=i18n.get("quiz.loading", loading="Loading..."),
        font=("Arial", 15),
        fg="white",
        bg="#1E1E2F"
    ).pack(pady=30)

    splash.after(2500, lambda: (splash.destroy(), show_user_details()))
    splash.mainloop()

# ================= USER DETAILS =================
def show_user_details():
    root = tk.Tk()
    root.title("SoulSense - User Details")
    
    # Responsive sizing
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    window_width = min(450, int(screen_width * 0.4))
    window_height = min(350, int(screen_height * 0.4))
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    root.minsize(400, 300)
    root.resizable(True, True)

    username = tk.StringVar()
    age = tk.StringVar()

    tk.Label(root, text="SoulSense Assessment",
             font=("Arial", 20, "bold")).pack(pady=20)

    tk.Label(root, text="Enter your name:", font=("Arial", 15)).pack()
    tk.Entry(root, textvariable=username,
             font=("Arial", 15), width=25).pack(pady=8)

    tk.Label(root, text="Enter your age:", font=("Arial", 15)).pack()
    tk.Entry(root, textvariable=age,
             font=("Arial", 15), width=25).pack(pady=8)

    def start():
        if not username.get() or not age.get().isdigit():
            messagebox.showerror("Error", "Please enter valid name and age")
            return
        root.destroy()
        start_quiz(username.get(), int(age.get()))

    tk.Button(
        root,
        text="Start Assessment",
        command=start,
        bg="#4CAF50",
        fg="white",
        font=("Arial", 14, "bold"),
        width=20
    ).pack(pady=25)

    root.mainloop()

# ================= QUIZ =================
def start_quiz(username, age):
    filtered_questions = [q for q in questions if q["age_min"] <= age <= q["age_max"]]
    total_questions = len(filtered_questions)

    quiz = tk.Tk()
    quiz.title(i18n.get("app_title") + " " + i18n.get("quiz.question_counter", current=1, total=total_questions).split(" ")[-1])
    
    # Responsive sizing for quiz window
    screen_width = quiz.winfo_screenwidth()
    screen_height = quiz.winfo_screenheight()
    window_width = min(750, int(screen_width * 0.6))
    window_height = min(600, int(screen_height * 0.7))
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    
    quiz.geometry(f"{window_width}x{window_height}+{x}+{y}")
    quiz.minsize(600, 500)
    quiz.resizable(True, True)

    responses = []
    score = 0
    current_q = 0
    var = tk.IntVar()

    start_time = time.time()

    timer_label = tk.Label(quiz, font=("Arial", 14, "bold"), fg="#1E88E5")
    timer_label.pack(pady=5)

    def update_timer():
        elapsed = int(time.time() - start_time)
        m, s = divmod(elapsed, 60)
        timer_label.config(text=f"Time: {m:02d}:{s:02d}")
        quiz.after(1000, update_timer)

    update_timer()

    question_counter = tk.Label(quiz, font=("Arial", 12), fg="#666")
    question_counter.pack(pady=(10, 0))

    question_label = tk.Label(quiz, wraplength=700, font=("Arial", 16))
    question_label.pack(pady=20)

    options = [
        (i18n.get("quiz.strongly_disagree"), 1),
        (i18n.get("quiz.disagree"), 2),
        (i18n.get("quiz.neutral"), 3),
        (i18n.get("quiz.agree"), 4),
        (i18n.get("quiz.strongly_agree"), 5)
    ]

    for text, val in options:
        tk.Radiobutton(
            quiz,
            text=text,
            variable=var,
            value=val,
            font=("Arial", 14)
        ).pack(anchor="w", padx=60)

    def load_question():
        question_counter.config(text=i18n.get("quiz.question_counter", current=current_q+1, total=total_questions))
        question_label.config(text=i18n.get_question(current_q))

    def finish(title):
        elapsed = int(time.time() - start_time)
        analytics = compute_analytics(responses, elapsed, total_questions)

        # Use connection manager for TIME_WAIT prevention
        execute_write("""
            INSERT INTO scores
            (username, age, total_score, avg_response, max_response, min_response,
             score_variance, questions_attempted, completion_ratio,
             avg_time_per_question, time_taken_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            username, age, score,
            analytics["avg"], analytics["max"], analytics["min"],
            analytics["variance"], analytics["attempted"],
            analytics["completion"], analytics["avg_time"], elapsed
        ))

        messagebox.showinfo(
            i18n.get("results.completed"),
            f"Score: {score}\n"
            f"Questions Attempted: {analytics['attempted']}\n"
            f"Time Taken: {elapsed} sec"
        )

        quiz.destroy()

    def next_question():
        nonlocal current_q, score
        if var.get() == 0:
            messagebox.showwarning(i18n.get("quiz.warning"), i18n.get("errors.select_option"))
            return

        responses.append(var.get())
        score += var.get()
        var.set(0)
        current_q += 1

        if current_q < total_questions:
            load_question()
        else:
            finish(i18n.get("results.completed"))

    def stop_test():
        if messagebox.askyesno(i18n.get("quiz.warning"), i18n.get("quiz.stop_test", stop="Stop test and save progress?")):
            finish(i18n.get("quiz.stopped", stopped="Quiz Stopped"))

    tk.Button(
        quiz,
        text=i18n.get("quiz.next"),
        command=next_question,
        bg="#4CAF50",
        fg="white",
        font=("Arial", 14, "bold"),
        width=15
    ).pack(pady=15)

    tk.Button(
        quiz,
        text=i18n.get("quiz.stop_test", stop="Stop Test"),
        command=stop_test,
        bg="#E53935",
        fg="white",
        font=("Arial", 13, "bold"),
        width=15
    ).pack()

    load_question()
    quiz.mainloop()

# ================= START APP =================
show_splash()
