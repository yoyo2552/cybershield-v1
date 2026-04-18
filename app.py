import os
import re

from flask import Flask, request, render_template_string, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "change_this_secret"

# -------------------
# DATABASE
# -------------------
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///saas.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# -------------------
# LOGIN
# -------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# -------------------
# MODELS
# -------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(200))

class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    text = db.Column(db.String(300))
    score = db.Column(db.Integer)
    verdict = db.Column(db.String(50))

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -------------------
# AI DETECTION
# -------------------
def analyze(text):
    score = 0
    t = text.lower()

    high_risk = [
        "urgent", "immédiatement", "suspendu", "bloqué",
        "verify", "password", "mot de passe", "login",
        "paypal", "bank", "compte", "security"
    ]

    medium_risk = [
        "cliquez", "click", "ici", "connexion",
        "gagné", "winner", "free", "gift",
        "money", "1000", "€"
    ]

    for w in high_risk:
        if w in t:
            score += 20

    for w in medium_risk:
        if w in t:
            score += 10

    if re.search(r"http", t):
        score += 25

    if text.isupper() and len(text) > 10:
        score += 15

    if score >= 70:
        verdict = "🚨 PHISHING"
    elif score >= 40:
        verdict = "⚠️ SUSPECT"
    else:
        verdict = "✅ SAFE"

    return min(score, 100), verdict

# -------------------
# STYLE GLOBAL
# -------------------
STYLE = """
<style>
body{
    margin:0;
    font-family: Arial;
    background:#0b1220;
    color:white;
    text-align:center;
}

.container{
    max-width:900px;
    margin:auto;
    padding:80px 20px;
}

h1{
    font-size:50px;
}

p{
    color:#cbd5e1;
}

.btn{
    display:inline-block;
    margin-top:20px;
    padding:15px 25px;
    background:#6366f1;
    border-radius:10px;
    color:white;
    text-decoration:none;
    font-weight:bold;
}

.card{
    background:rgba(255,255,255,0.05);
    padding:20px;
    border-radius:15px;
    margin-top:30px;
}

textarea{
    width:100%;
    height:120px;
    border-radius:10px;
    padding:10px;
    background:#111827;
    color:white;
    border:none;
}

input{
    width:100%;
    padding:12px;
    margin-top:10px;
    border-radius:10px;
    border:none;
    background:#111827;
    color:white;
}

button{
    margin-top:15px;
    padding:12px 20px;
    background:#22c55e;
    border:none;
    border-radius:10px;
    color:white;
    font-weight:bold;
    cursor:pointer;
}
</style>
"""

# -------------------
# LANDING PAGE
# -------------------
@app.route("/")
def home():
    return f"""
    <html>
    <head>{STYLE}</head>
    <body>

    <div class="container">

        <h1>🛡️ Évite les arnaques en 2 secondes</h1>
        <p>Colle un message suspect → CyberShield te dit s’il est dangereux</p>

        <div class="card">
            <form method="POST" action="/dashboard">
                <textarea name="text" placeholder="Ex: URGENT votre compte est suspendu..."></textarea>
                <button>Analyser maintenant</button>
            </form>
        </div>

        <a href="/signup" class="btn">Créer un compte gratuitement</a>

        <div class="card">
            <h3>Pourquoi utiliser CyberShield ?</h3>
            <p>✔ Détection instantanée</p>
            <p>✔ Évite les arnaques</p>
            <p>✔ Simple et rapide</p>
        </div>

        <div class="card">
            <h3>Exemple</h3>
            <p>"Votre compte bancaire est suspendu, cliquez ici"</p>
            <p>→ 🚨 PHISHING détecté</p>
        </div>

    </div>

    </body>
    </html>
    """

# -------------------
# SIGNUP
# -------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        user = User(email=email, password=password)
        db.session.add(user)
        db.session.commit()

        return redirect("/login")

    return f"""
    <html><head>{STYLE}</head>
    <body>
    <div class="container">
    <h1>Créer un compte</h1>
    <div class="card">
        <form method="POST">
            <input name="email" placeholder="Email">
            <input name="password" type="password" placeholder="Password">
            <button>S'inscrire</button>
        </form>
    </div>
    </div>
    </body></html>
    """

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
            login_user(user)
            return redirect("/dashboard")

        return "❌ Login incorrect"

    return f"""
    <html><head>{STYLE}</head>
    <body>
    <div class="container">
    <h1>Login</h1>
    <div class="card">
        <form method="POST">
            <input name="email" placeholder="Email">
            <input name="password" type="password" placeholder="Password">
            <button>Se connecter</button>
        </form>
    </div>
    </div>
    </body></html>
    """

# -------------------
# LOGOUT
# -------------------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")

# -------------------
# DASHBOARD
# -------------------
@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    result = None

    if request.method == "POST":
        text = request.form["text"]
        score, verdict = analyze(text)

        analysis = Analysis(
            user_id=current_user.id,
            text=text[:200],
            score=score,
            verdict=verdict
        )

        db.session.add(analysis)
        db.session.commit()

        result = (score, verdict)

    history = Analysis.query.filter_by(user_id=current_user.id).all()

    return f"""
    <html><head>{STYLE}</head>
    <body>
    <div class="container">

    <h1>Dashboard</h1>

    <div class="card">
        <form method="POST">
            <textarea name="text" placeholder="Colle un message suspect..."></textarea>
            <button>Analyser</button>
        </form>
    </div>

    {f'<div class="card"><h2>Score: {result[0]} | {result[1]}</h2></div>' if result else ""}

    <div class="card">
        <h3>Historique</h3>
        {''.join([f"<p>{h.text} | {h.score} | {h.verdict}</p>" for h in history])}
    </div>

    <div class="card">
        <a href="/logout">Logout</a>
    </div>

    </div>
    </body></html>
    """

# -------------------
# RUN
# -------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)