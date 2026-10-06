
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent
DB = BASE / "pocketsmart.db"

app = Flask(__name__)
app.secret_key = "pocketsmart-college-project-key"

CATEGORIES = ["Food", "Travel", "Shopping", "Bills", "Education", "Health", "Entertainment", "Other"]

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        kind TEXT NOT NULL CHECK(kind IN ('income','expense')),
        amount REAL NOT NULL,
        category TEXT NOT NULL,
        note TEXT,
        tx_date TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS budgets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        monthly_budget REAL NOT NULL DEFAULT 0,
        updated_at TEXT NOT NULL,
        UNIQUE(user_id),
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    """)
    conn.commit()
    conn.close()

def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    conn = get_db()
    u = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    conn.close()
    return u

def recommendations(income, expense, budget, by_category):
    tips = []
    savings = income - expense
    if income <= 0:
        tips.append("Add an income entry to get a personalized saving suggestion.")
    else:
        if savings < 0:
            tips.append("Your current expenses are higher than your income. Review non-essential spending.")
        elif savings < income * 0.10:
            tips.append("Your current saving level is below 10% of income. Try reducing one non-essential category.")
        else:
            tips.append(f"Good progress: your current balance after expenses is ₹{savings:,.0f}.")
    if budget > 0:
        if expense > budget:
            tips.append(f"You have crossed your monthly budget by ₹{expense-budget:,.0f}.")
        else:
            tips.append(f"You have ₹{budget-expense:,.0f} left in the budget.")
    if by_category:
        top = max(by_category.items(), key=lambda x: x[1])
        share = (top[1] / expense * 100) if expense else 0
        tips.append(f"{top[0]} is your highest expense category ({share:.0f}% of total expenses).")
        if share >= 40:
            tips.append(f"Consider setting a smaller limit for {top[0]} next month.")
    if not tips:
        tips.append("Add a few transactions to receive smart recommendations.")
    return tips

@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return render_template("landing.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        if not name or not email or not password:
            flash("Please fill all fields.", "error")
            return redirect(url_for("register"))
        conn = get_db()
        try:
            conn.execute("INSERT INTO users(name,email,password,created_at) VALUES(?,?,?,?)",
                         (name,email,password,datetime.now().isoformat(timespec="seconds")))
            conn.commit()
            user = conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
            session["user_id"] = user["id"]
            conn.execute("INSERT OR IGNORE INTO budgets(user_id,monthly_budget,updated_at) VALUES(?,?,?)",
                         (user["id"],0,datetime.now().isoformat(timespec="seconds")))
            conn.commit()
        except sqlite3.IntegrityError:
            flash("Email already registered. Please login.", "error")
            conn.close()
            return redirect(url_for("login"))
        conn.close()
        return redirect(url_for("dashboard"))
    return render_template("auth.html", mode="register")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email=? AND password=?", (email,password)).fetchone()
        conn.close()
        if user:
            session["user_id"] = user["id"]
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("auth.html", mode="login")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/dashboard")
def dashboard():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    conn = get_db()
    txs = conn.execute("SELECT * FROM transactions WHERE user_id=? ORDER BY tx_date DESC, id DESC",
                       (user["id"],)).fetchall()
    budget_row = conn.execute("SELECT monthly_budget FROM budgets WHERE user_id=?", (user["id"],)).fetchone()
    conn.close()

    income = sum(x["amount"] for x in txs if x["kind"]=="income")
    expense = sum(x["amount"] for x in txs if x["kind"]=="expense")
    budget = budget_row["monthly_budget"] if budget_row else 0
    by_category = {}
    for x in txs:
        if x["kind"] == "expense":
            by_category[x["category"]] = by_category.get(x["category"], 0) + x["amount"]

    tips = recommendations(income, expense, budget, by_category)
    labels = list(by_category.keys())
    values = [by_category[k] for k in labels]
    return render_template("dashboard.html", user=user, txs=txs, income=income, expense=expense,
                           savings=income-expense, budget=budget, tips=tips,
                           categories=CATEGORIES, labels=json.dumps(labels), values=json.dumps(values))

@app.route("/add", methods=["POST"])
def add_transaction():
    user = current_user()
    if not user: return redirect(url_for("login"))
    kind = request.form["kind"]
    amount = float(request.form["amount"])
    category = request.form["category"]
    note = request.form.get("note","").strip()
    tx_date = request.form.get("tx_date") or datetime.now().date().isoformat()
    conn = get_db()
    conn.execute("INSERT INTO transactions(user_id,kind,amount,category,note,tx_date) VALUES(?,?,?,?,?,?)",
                 (user["id"],kind,amount,category,note,tx_date))
    conn.commit(); conn.close()
    return redirect(url_for("dashboard"))

@app.route("/delete/<int:tx_id>", methods=["POST"])
def delete_transaction(tx_id):
    user = current_user()
    if not user: return redirect(url_for("login"))
    conn = get_db()
    conn.execute("DELETE FROM transactions WHERE id=? AND user_id=?", (tx_id,user["id"]))
    conn.commit(); conn.close()
    return redirect(url_for("dashboard"))

@app.route("/budget", methods=["POST"])
def budget():
    user = current_user()
    if not user: return redirect(url_for("login"))
    value = max(0, float(request.form["monthly_budget"]))
    conn = get_db()
    conn.execute("""INSERT INTO budgets(user_id,monthly_budget,updated_at) VALUES(?,?,?)
                    ON CONFLICT(user_id) DO UPDATE SET monthly_budget=excluded.monthly_budget,
                    updated_at=excluded.updated_at""",
                 (user["id"],value,datetime.now().isoformat(timespec="seconds")))
    conn.commit(); conn.close()
    return redirect(url_for("dashboard"))

@app.route("/api/summary")
def api_summary():
    user = current_user()
    if not user: return jsonify({"error":"login required"}),401
    conn=get_db()
    rows=conn.execute("SELECT kind, amount, category FROM transactions WHERE user_id=?", (user["id"],)).fetchall()
    conn.close()
    income=sum(r["amount"] for r in rows if r["kind"]=="income")
    expense=sum(r["amount"] for r in rows if r["kind"]=="expense")
    cats={}
    for r in rows:
        if r["kind"]=="expense": cats[r["category"]]=cats.get(r["category"],0)+r["amount"]
    return jsonify({"income":income,"expense":expense,"savings":income-expense,"categories":cats})

init_db()

if __name__ == "__main__":
    app.run(debug=True)
