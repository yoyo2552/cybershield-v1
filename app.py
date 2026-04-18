from flask import Flask, render_template_string, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import os
import re

app = Flask(__name__)

# 🔐 SECURITY
app.secret_key = os.environ.get("SECRET_KEY", "cybershield_secret")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# 🗄️ DATABASE
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
# 🧠 AI ENGINE (PHISHING SCORE)
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
        reasons.append("Lien suspect détecté")

    for word, val in risky_words.items():
        if word in text:
            score += val
            reasons.append(f"Mot suspect: {word}")

    if text.isupper():
        score += 15
        reasons.append("Message en majuscules")

    if text.count("!") > 2:
        score += 10
        reasons.append("Excès de ponctuation")

    if re.search(r"\d{4,}", text):
        score += 10
        reasons.append("Suite numérique suspecte")

    return min(score, 100), reasons

# -------------------
# HOME
# -------------------
@app.route("/")
def home():
    return render_template_string("""
    <body style="margin:0;font-family:Arial;background:#0b1220;color:white;text-align:center;">
        <div style="margin-top:120px;">
            <h1>🛡️ CyberShield AI</h1>
            <p>Détection phishing IA nouvelle génération</p>

            <a href="/signup" style="padding:10px 20px;background:#6366f1;color:white;text-decoration:none;border-radius:10px;">Signup</a>
            <a href="/login" style="padding:10px 20px;background:#6366f1;color:white;text-decoration:none;border-radius:10px;">Login</a>
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
            return "<h3 style='color:red;text-align:center'>Email déjà utilisé</h3>"

        db.session.add(User(email=email, password=password))
        db.session.commit()

        return redirect("/login")

    return render_template_string("""
    <body style="text-align:center;margin-top:100px;background:#0b1220;color:white;">
        <h1>Signup</h1>
        <form method="POST">
            <input name="email" placeholder="email"><br><br>
            <input name="password" type="password" placeholder="password"><br><br>
            <button>Create account</button>
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

        return "<h3 style='color:red;text-align:center'>Login failed</h3>"

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
# DASHBOARD PRO (IA)
# -------------------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect("/login")

    result_html = ""

    if request.method == "POST":
        text = request.form["text"]

        score, reasons = phishing_ai(text)

        if score >= 70:
            verdict = "🚨 PHISHING ÉLEVÉ"
            color = "#ef4444"
        elif score >= 40:
            verdict = "⚠️ SUSPECT"
            color = "#f59e0b"
        else:
            verdict = "✅ SAFE"
            color = "#22c55e"

        reasons_html = "<br>".join(reasons) if reasons else "Aucun signal détecté"

        result_html = f"""
        <div style="margin-top:25px;padding:20px;background:#111827;border-radius:16px;max-width:500px;margin:auto;">
            <h2 style="color:{color}">{verdict}</h2>
            <p>Score IA : <b>{score}/100</b></p>
            <hr style="border:1px solid #1f2937;">
            <p style="color:#cbd5e1;text-align:left">{reasons_html}</p>
        </div>
        """

    return render_template_string(f"""
    <body style="margin:0;font-family:Arial;background:#0b1220;color:white;">

        <div style="padding:15px 30px;background:#0f172a;display:flex;justify-content:space-between;">
            <h2>🛡️ CyberShield AI</h2>
            <div>
                {session.get("user")}
                <a href="/logout" style="margin-left:15px;color:#6366f1;">Logout</a>
            </div>
        </div>

        <div style="text-align:center;margin-top:60px;">
            <h1>Dashboard IA</h1>

            <form method="POST">
                <textarea name="text" placeholder="Analyse un message suspect..."
                    style="width:400px;height:140px;padding:10px;border-radius:10px;"></textarea><br><br>

                <button style="padding:12px 25px;background:#4f46e5;color:white;border:none;border-radius:10px;">
                    Analyser IA
                </button>
            </form>

            {result_html}
        </div>

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