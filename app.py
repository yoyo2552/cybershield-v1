import os
import re

from flask import Flask, request, render_template_string, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "change_this_secret_key"

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
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    text = db.Column(db.String(300))
    score = db.Column(db.Integer)
    verdict = db.Column(db.String(50))

# ✅ FIX IMPORTANT SQLALCHEMY (Render)
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -------------------
# AI SIMPLE
# -------------------
def analyze(text):
    score = 0
    t = text.lower()

    risky_words = [
        "urgent", "suspendu", "bloqué", "password",
        "login", "compte", "paypal", "bank",
        "cliquez", "click", "gagné", "winner"
    ]

    for w in risky_words:
        if w in t:
            score += 15

    if re.search(r"http", t):
        score += 25

    if text.isupper() and len(text) > 10:
        score += 10

    score = min(score, 100)

    if score >= 70:
        verdict = "🚨 PHISHING"
    elif score >= 40:
        verdict = "⚠️ SUSPECT"
    else:
        verdict = "✅ SAFE"

    return score, verdict

# -------------------
# HOME
# -------------------
@app.route("/")
def home():
    return """
    <h1>CyberShield AI</h1>
    <a href='/signup'>Signup</a> | <a href='/login'>Login</a>
    """

# -------------------
# SIGNUP FIX
# -------------------
@app.route("/")
def home():
    return "CYBERSHIELD OK - DEPLOY FONCTIONNE"