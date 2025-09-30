import tkinter as tk
from tkinter import messagebox
import sqlite3
import random
import requests
import html

# -------------------- DATABASE SETUP --------------------
conn = sqlite3.connect("quiz_app.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    best_score INTEGER DEFAULT 0
)
""")
conn.commit()

# -------------------- GLOBAL VARIABLES --------------------
current_user = None
score = 0
question_list = []
current_index = 0

# -------------------- FETCH QUESTIONS FROM API --------------------
def fetch_questions(amount=10):
    url = f"https://opentdb.com/api.php?amount={amount}&type=multiple"
    try:
        response = requests.get(url)
        data = response.json()
        questions = []
        for item in data['results']:
            question_text = html.unescape(item['question'])
            correct = html.unescape(item['correct_answer'])
            incorrect = [html.unescape(ans) for ans in item['incorrect_answers']]
            options = incorrect + [correct]
            random.shuffle(options)
            questions.append({
                "question": question_text,
                "type": "mcq",
                "options": ",".join(options),
                "answer": correct
            })
        return questions
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch questions: {e}")
        return []

# -------------------- REGISTER --------------------
def register():
    def attempt_register():
        username = username_entry.get()
        password = password_entry.get()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?,?)", (username, password))
            conn.commit()
            messagebox.showinfo("Success", "User registered successfully")
            register_window.destroy()
            login()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists")

    register_window = tk.Toplevel(root, bg="#f9f9f9")
    register_window.title("Sign Up")
    register_window.geometry("1000x500")

    tk.Label(register_window, text="📝 Sign Up", font=("Arial", 18, "bold"), bg="#f9f9f9", fg="#333").pack(pady=10)
    tk.Label(register_window, text="Username:", bg="#f9f9f9", fg="#444").pack(pady=5)
    username_entry = tk.Entry(register_window, font=("Arial", 12), bd=2, relief="groove")
    username_entry.pack(pady=5)
    tk.Label(register_window, text="Password:", bg="#f9f9f9", fg="#444").pack(pady=5)
    password_entry = tk.Entry(register_window, show="*", font=("Arial", 12), bd=2, relief="groove")
    password_entry.pack(pady=5)
    tk.Button(register_window, text="✅ Sign Up", font=("Arial", 12, "bold"), bg="#4caf50", fg="white", width=15, relief="ridge", command=attempt_register).pack(pady=15)

# -------------------- LOGIN --------------------
def login():
    def attempt_login():
        global current_user, question_list, current_index, score
        username = username_entry.get()
        password = password_entry.get()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        if user:
            messagebox.showinfo("Login Success", f"Welcome {username}")
            current_user = user
            login_window.destroy()
            # Fetch questions from API
            question_list.clear()
            question_list.extend(fetch_questions(amount=10))
            current_index = 0
            score = 0
            show_question()
        else:
            messagebox.showerror("Error", "Invalid credentials")

    login_window = tk.Toplevel(root, bg="#f9f9f9")
    login_window.title("Login")
    login_window.geometry("400x300")

    tk.Label(login_window, text="🔑 Login", font=("Arial", 18, "bold"), bg="#f9f9f9", fg="#333").pack(pady=10)
    tk.Label(login_window, text="Username:", bg="#f9f9f9", fg="#444").pack(pady=5)
    username_entry = tk.Entry(login_window, font=("Arial", 12), bd=2, relief="groove")
    username_entry.pack(pady=5)
    tk.Label(login_window, text="Password:", bg="#f9f9f9", fg="#444").pack(pady=5)
    password_entry = tk.Entry(login_window, show="*", font=("Arial", 12), bd=2, relief="groove")
    password_entry.pack(pady=5)
    tk.Button(login_window, text="➡ Login", font=("Arial", 12, "bold"), bg="#2196f3", fg="white", width=15, relief="ridge", command=attempt_login).pack(pady=15)

# -------------------- QUIZ LOGIC --------------------
def show_question():
    global current_index, question_list, score
    for widget in quiz_frame.winfo_children():
        widget.destroy()

    if current_index >= len(question_list):
        messagebox.showinfo("Quiz Finished", f"Your score: {score}")
        update_best_score()
        return

    q = question_list[current_index]
    q_text, q_type, q_options, q_answer = q["question"], q["type"], q["options"], q["answer"]

    tk.Label(quiz_frame, text=f"Question {current_index+1}/{len(question_list)}", 
             font=("Arial", 14, "bold"), bg="#fff", fg="#222").pack(pady=5)
    tk.Label(quiz_frame, text=q_text, font=("Arial", 14), wraplength=480, bg="#fff", fg="#333").pack(pady=10)

    answer_var = tk.StringVar()

    if q_type == "mcq":
        options = q_options.split(",")
        for opt in options:
            tk.Radiobutton(quiz_frame, text=opt, variable=answer_var, value=opt,
                           font=("Arial", 12), bg="#fff", anchor="w").pack(fill="x", padx=20, pady=2)
    else:
        tk.Entry(quiz_frame, textvariable=answer_var, font=("Arial", 12), bd=2, relief="groove").pack(pady=5)

    def submit():
        nonlocal q_answer
        global current_index, score
        ans = answer_var.get()
        if ans.strip().lower() == q_answer.strip().lower():
            score += 1
        current_index += 1
        show_question()

    tk.Button(quiz_frame, text="Submit Answer", font=("Arial", 12, "bold"), bg="#ff5722", fg="white", width=20, relief="ridge", command=submit).pack(pady=15)
    tk.Label(quiz_frame, text=f"Current Score: {score}", font=("Arial", 12, "bold"), bg="#fff", fg="#444").pack(pady=5)

# -------------------- SCOREBOARD --------------------
def update_best_score():
    global current_user, score
    if score > current_user[3]:
        cursor.execute("UPDATE users SET best_score=? WHERE id=?", (score, current_user[0]))
        conn.commit()
        current_user = (current_user[0], current_user[1], current_user[2], score)
        messagebox.showinfo("New Best Score!", f"Congrats! New best score: {score}")

def show_scoreboard():
    scoreboard = tk.Toplevel(root, bg="#f0f8ff")
    scoreboard.title("Leaderboard")
    scoreboard.geometry("350x400")
    tk.Label(scoreboard, text="🏆 Leaderboard", font=("Arial", 16, "bold"), bg="#f0f8ff", fg="#222").pack(pady=10)
    cursor.execute("SELECT username, best_score FROM users ORDER BY best_score DESC")
    records = cursor.fetchall()
    for idx, rec in enumerate(records, start=1):
        tk.Label(scoreboard, text=f"{idx}. {rec[0]} - {rec[1]}", font=("Arial", 12), bg="#f0f8ff", fg="#333").pack(anchor="w", padx=20, pady=2)

# -------------------- ABOUT --------------------
def show_about():
    messagebox.showinfo("About", "✨ Quiz App\nBuilt with Python & Tkinter\nPowered by Open Trivia API")

# -------------------- MAIN GUI --------------------
root = tk.Tk()
root.title("Quiz App")
root.geometry("650x520")
root.configure(bg="#e3f2fd")

# ---- MENU BAR ----
menubar = tk.Menu(root)

account_menu = tk.Menu(menubar, tearoff=0)
account_menu.add_command(label="Sign Up", command=register)
account_menu.add_command(label="Login", command=login)
account_menu.add_command(label="Leaderboard", command=show_scoreboard)
menubar.add_cascade(label="Account", menu=account_menu)

file_menu = tk.Menu(menubar, tearoff=0)
file_menu.add_command(label="Exit", command=root.destroy)
menubar.add_cascade(label="File", menu=file_menu)

help_menu = tk.Menu(menubar, tearoff=0)
help_menu.add_command(label="About", command=show_about)
menubar.add_cascade(label="Help", menu=help_menu)

root.config(menu=menubar)

# ---- HEADER ----
header = tk.Label(root, text="🎯 Welcome to the Quiz App 🎯", font=("Arial", 22, "bold"),
                  bg="#1565c0", fg="white", pady=15)
header.pack(fill="x")

# ---- QUIZ AREA ----
quiz_frame = tk.Frame(root, bg="#fff", bd=3, relief="ridge")
quiz_frame.pack(pady=30, padx=20, fill="both", expand=True)

tk.Label(quiz_frame, text="👉 Login from 'Account' menu to Start the Quiz",
         font=("Arial", 14, "italic"), bg="#fff", fg="#444").pack(pady=100)

root.mainloop() 
