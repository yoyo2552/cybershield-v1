from flask import Flask, render_template_string, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import os
import re

app = Flask(__name__)

# 🔐 sécurité session
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
# 🧠 IA PHISHING ENGINE (PRO)
# -------------------
def phishing_ai(text):
    text = text.lower()

    score = 0
    reasons = []

    # 🔥 mots sensibles phishing
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
        "free": 10
    }

    # 🌐 liens suspects
    if re.search(r"http|https|bit\.ly|tinyurl", text):
        score += 40
        reasons.append("Lien suspect détecté")

    # 📊 mots
    for word, val in risky_words.items():
        if word in text:
            score += val
            reasons.append(f"Mot suspect: {word}")

    # 🚨 majuscules agressives
    if text.isupper():
        score += 15
        reasons.append("Message en MAJUSCULES")

    # ❗ spam ponctuation
    if text.count("!") > 2:
        score += 10
        reasons.append("Excès de '!'")

    # 🔢 chiffres suspects
    if re.search(r"\d{4,}", text):
        score += 10
        reasons.append("Séquence numérique suspecte")

    # clamp
    score = min(score, 100)

    return score, reasons

# -------------------
# HOME
# -------------------
@app.route("/")
def home():
    return render_template_string("""
    <html>
    <body style="margin:0;font-family:Arial;background:#0f172a;color:white;text-align:center;">
        <div style="margin-top:120px;">
            <h1>🛡️ CyberShield AI</h1>
            <p>IA de détection phishing nouvelle génération</p>

            <a href="/signup" style="padding:10px 20px;background:#6366f1;color:white;text-decoration:none;border-radius:10px;">Signup</a>
            <a href="/login" style="padding:10px 20px;background:#6366f1;color:white;text-decoration:none;border-radius:10px;">Login</a>
        </div>
    </body>
    </html>
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
    <body style="text-align:center;margin-top:100px;background:#0f172a;color:white;">
        <h1>Signup</h1>
        <form method="POST">
            <input name="email" placeholder="email"><br><br>
            <input name="password" type="password" placeholder="password"><br><br>
            <button>Créer compte</button>
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
    <body style="text-align:center;margin-top:100px;background:#0f172a;color:white;">
        <h1>Login</h1>
        <form method="POST">
            <input name="email"><br><br>
            <input name="password" type="password"><br><br>
            <button>Login</button>
        </form>
    </body>
    """)

# -------------------
# DASHBOARD (IA PRO)
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
            color = "red"
        elif score >= 40:
            verdict = "⚠️ SUSPECT"
            color = "orange"
        else:
            verdict = "✅ SAFE"
            color = "green"

        reasons_html = "<br>".join(reasons) if reasons else "Aucun signal suspect"

        result_html = f"""
        <div style="margin-top:20px;padding:20px;background:#111827;border-radius:12px;display:inline-block;">
            <h2 style="color:{color}">{verdict}</h2>
            <p>Score IA: <b>{score}/100</b></p>
            <hr>
            <p style="color:#cbd5e1">{reasons_html}</p>
        </div>
        """

    return render_template_string(f"""
    <body style="text-align:center;margin-top:80px;background:#0f172a;color:white;font-family:Arial;">

        <h1>CyberShield AI Dashboard</h1>
        <p>Bienvenue {session.get("user")}</p>

        <form method="POST">
            <textarea name="text" placeholder="Colle un message suspect..." style="width:300px;height:120px;"></textarea><br><br>
            <button>Analyser IA</button>
        </form>

        {result_html}

        <br><br>
        <a href="/logout" style="color:#6366f1;">Logout</a>

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