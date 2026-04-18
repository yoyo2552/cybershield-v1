from flask import Flask, render_template_string, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import os
import re

app = Flask(__name__)

# 🔐 CONFIG
app.secret_key = "cybershield_secret"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# 🗄️ DB
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///saas.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# -------------------
# USER MODEL
# -------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

with app.app_context():
    db.create_all()

# -------------------
# 🧠 AI ENGINE
# -------------------
def phishing_ai(text):
    text = text.lower()

    score = 0
    reasons = []

    risky_words = {
        "urgent": 15,
        "password": 20,
        "bank": 20,
        "verify": 15,
        "login": 15,
        "suspend": 25,
        "click": 10,
        "confirm": 15,
        "winner": 20,
        "free": 10,
        "account": 15
    }

    if re.search(r"http|https|bit\.ly|tinyurl", text):
        score += 40
        reasons.append("Lien suspect")

    for word, val in risky_words.items():
        if word in text:
            score += val
            reasons.append(f"Mot suspect: {word}")

    if text.isupper():
        score += 15
        reasons.append("MAJUSCULES")

    if text.count("!") > 2:
        score += 10
        reasons.append("Spam !!!")

    if re.search(r"\d{4,}", text):
        score += 10
        reasons.append("Chiffres suspects")

    return min(score, 100), reasons

# -------------------
# 🏠 LANDING PAGE
# -------------------
@app.route("/")
def home():
    return render_template_string("""
    <body style="margin:0;font-family:Arial;background:#0b1220;color:white;">

    <div style="display:flex;justify-content:space-between;padding:20px;background:#0f172a;">
        <h2>🛡️ CyberShield AI</h2>
        <div>
            <a href="/login" style="color:white;margin-right:10px;">Login</a>
            <a href="/signup" style="color:white;">Signup</a>
        </div>
    </div>

    <div style="text-align:center;margin-top:120px;">
        <h1 style="font-size:50px;">AI Phishing Protection</h1>
        <p style="color:#94a3b8;">Detect scams & malicious messages instantly</p>
        <a href="/signup" style="padding:12px 25px;background:#4f46e5;color:white;text-decoration:none;border-radius:10px;">Get Started</a>
    </div>

    <div style="display:flex;justify-content:center;margin-top:60px;">

        <div style="background:#111827;padding:20px;margin:10px;border-radius:15px;width:220px;">
            ⚡ AI Detection
        </div>

        <div style="background:#111827;padding:20px;margin:10px;border-radius:15px;width:220px;">
            🔐 Secure Login
        </div>

        <div style="background:#111827;padding:20px;margin:10px;border-radius:15px;width:220px;">
            📊 Risk Score
        </div>

    </div>

    </body>
    """)

# -------------------
# SIGNUP
# -------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        if User.query.filter_by(email=email).first():
            return "Email déjà utilisé"

        db.session.add(User(email=email, password=password))
        db.session.commit()

        return redirect("/login")

    return render_template_string("""
    <body style="text-align:center;margin-top:100px;background:#0b1220;color:white;">
        <h1>Signup</h1>
        <form method="POST">
            <input name="email" placeholder="email"><br><br>
            <input name="password" type="password" placeholder="password"><br><br>
            <button>Create</button>
        </form>
    </body>
    """)

# -------------------
# LOGIN
# -------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session["user"] = user.email
            return redirect("/dashboard")

        return "Login failed"

    return render_template_string("""
    <body style="text-align:center;margin-top:100px;background:#0b1220;color:white;">
        <h1>Login</h1>
        <form method="POST">
            <input name="email"><br><br>
            <input name="password" type="password"><br><br>
            <button>Login</button>
        </form>
    </body>
    """)

# -------------------
# DASHBOARD IA
# -------------------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect("/login")

    result = ""

    if request.method == "POST":
        text = request.form["text"]

        score, reasons = phishing_ai(text)

        if score >= 70:
            verdict = "🚨 PHISHING"
            color = "red"
        elif score >= 40:
            verdict = "⚠️ SUSPECT"
            color = "orange"
        else:
            verdict = "✅ SAFE"
            color = "green"

        reasons_html = "<br>".join(reasons) if reasons else "Clean"

        result = f"""
        <div style="margin-top:20px;padding:20px;background:#111827;border-radius:15px;">
            <h2 style="color:{color}">{verdict}</h2>
            <p>Score IA: <b>{score}/100</b></p>
            <p>{reasons_html}</p>
        </div>
        """

    return render_template_string(f"""
    <body style="margin:0;font-family:Arial;background:#0b1220;color:white;text-align:center;">

        <div style="padding:15px;background:#0f172a;">
            🛡️ CyberShield AI | {session.get("user")}
            <a href="/logout" style="color:#6366f1;margin-left:20px;">Logout</a>
        </div>

        <h1>Dashboard IA</h1>

        <form method="POST">
            <textarea name="text" style="width:400px;height:120px;"></textarea><br><br>
            <button style="padding:10px 20px;background:#4f46e5;color:white;">Analyze</button>
        </form>

        {result}

    </body>
    """)

# -------------------
# LOGOUT
# -------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# -------------------
# RUN
# -------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)