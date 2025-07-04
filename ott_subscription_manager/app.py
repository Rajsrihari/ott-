from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "mysecretkey"  # Required for session

# ===== DB Setup =====
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        name TEXT,
        price REAL,
        start_date TEXT,
        next_payment TEXT,
        payment_method TEXT,
        paid_by TEXT,
        category TEXT,
        notify INTEGER,
        enabled INTEGER,
        replacement TEXT,
        renewal_type TEXT
    )''')

    conn.commit()
    conn.close()

# ===== Home Route =====
@app.route("/")
def index():
    return render_template("index.html")

# ===== Signup =====
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
        except sqlite3.IntegrityError:
            return "Username already exists"
        conn.close()
        return redirect("/login")

    return render_template("signup.html")

# ===== Login =====
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session["username"] = username
            return redirect("/home")
        else:
            return "Invalid login"
    return render_template("login.html")

# ===== Logout =====
@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect("/")

# ===== Home Page after login =====
@app.route("/home")
def home():
    if "username" not in session:
        return redirect("/login")
    
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM subscriptions")
    subscriptions = c.fetchall()
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    conn.close()

    return render_template("home.html", username=session["username"], users=users, subscriptions=subscriptions)

# ===== Add Subscription =====
@app.route("/add_subscription", methods=["GET", "POST"])
def add_subscription():
    if "username" not in session:
        return redirect("/login")

    if request.method == "POST":
        data = (
            session["username"],
            request.form["name"],
            request.form["price"],
            request.form["start_date"],
            request.form["next_payment"],
            request.form["payment_method"],
            request.form["paid_by"],
            request.form["category"],
            1 if "notify" in request.form else 0,
            1 if request.form.get("status") == "enabled" else 0,
            request.form.get("replacement", ""),
            request.form.get("renewal_type")
        )

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute('''INSERT INTO subscriptions 
            (username, name, price, start_date, next_payment, payment_method, paid_by, category, notify, enabled, replacement, renewal_type) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', data)
        conn.commit()
        conn.close()

        return redirect("/home")

    return render_template("add_subscription.html")

# ===== Filter Route =====
@app.route("/filter/<filter_type>")
def filter_subscriptions(filter_type):
    if "username" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    if filter_type == "member":
        c.execute("SELECT * FROM subscriptions WHERE username=?", (session["username"],))
    elif filter_type == "category":
        c.execute("SELECT * FROM subscriptions WHERE category IN ('Music', 'Food', 'Gaming', 'Technology')")
    elif filter_type == "payment":
        c.execute("SELECT * FROM subscriptions WHERE payment_method IN ('Credit Card', 'Debit Card', 'Bank Transfer')")
    elif filter_type == "state":
        c.execute("SELECT * FROM subscriptions WHERE enabled IN (0, 1)")
    elif filter_type == "renewal":
        c.execute("SELECT * FROM subscriptions WHERE renewal_type IN ('Auto', 'Manual')")
    else:
        return redirect("/home")

    subscriptions = c.fetchall()
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    conn.close()

    return render_template("home.html", username=session["username"], users=users, subscriptions=subscriptions)

# ===== Search OTT =====
@app.route("/search", methods=["POST"])
def search():
    query = request.form["query"].lower()
    otts = ["netflix", "hotstar", "prime", "zeestudio", "sports7"]
    result = [o for o in otts if query in o]
    return render_template("home.html", search_results=result)
def get_filtered_subscriptions(query, args, title):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute(query, args)
    subscriptions = c.fetchall()
    conn.close()
    return render_template("home.html", username=session["username"], subscriptions=subscriptions, users=[], show_popup=True, popup_title=title)

@app.route("/filter/member")
def filter_member():
    if "username" not in session:
        return redirect("/login")
    query = "SELECT * FROM subscriptions WHERE username = ?"
    return get_filtered_subscriptions(query, (session["username"],), "Member Filter: Your Subscriptions")

@app.route("/filter/category")
def filter_category():
    query = "SELECT * FROM subscriptions WHERE category IN ('Music', 'Food', 'Gaming', 'Technology', 'Entertainment', 'Insurance', 'Cloud Services')"
    return get_filtered_subscriptions(query, (), "Category Filter")

@app.route("/filter/payment")
def filter_payment():
    query = "SELECT * FROM subscriptions WHERE payment_method IN ('Credit Card', 'Debit Card', 'Bank Transfer')"
    return get_filtered_subscriptions(query, (), "Payment Method Filter")

@app.route("/filter/state")
def filter_state():
    query = "SELECT * FROM subscriptions WHERE enabled IN (0, 1)"
    return get_filtered_subscriptions(query, (), "State Filter")

@app.route("/filter/renewal")
def filter_renewal():
    query = "SELECT * FROM subscriptions WHERE renewal_type IN ('Auto', 'Manual')"
    return get_filtered_subscriptions(query, (), "Renewal Type Filter")

# ===== Run App =====
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
