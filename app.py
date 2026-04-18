from flask import Flask, render_template_string, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import os
import re
import stripe

app = Flask(__name__)

# 🔐 CONFIG
app.secret_key = os.environ.get("SECRET_KEY", "cybershield_secret")

# 💳 STRIPE
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

# 🗄️ DB CONFIG
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
    is_pro = db.Column(db.Boolean, default=False)

# 🔥 FIX AUTO DB (évite crash)
with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        print("DB ERROR → RESET")
        if os.path.exists("saas.db"):
            os.remove("saas.db")
        db.create_all()

# -------------------
# AI PHISHING
# -------------------
def phishing_ai(text):
    text = text.lower()
    score = 0

    if "http" in text:
        score += 40
    if "password" in text:
        score += 20
    if "urgent" in text:
        score += 20
    if "bank" in text:
        score += 20

    return min(score, 100)

# -------------------
# HOME
# -------------------
@app.route("/")
def home():
    return redirect("/pricing")

# -------------------
# PRICING
# -------------------
@app.route("/pricing")
def pricing():
    return """
    <body style="background:#0b1220;color:white;text-align:center;">
        <h1>CyberShield AI</h1>
        <a href="/signup">Free</a><br><br>
        <a href="/checkout">Pro 9.99€</a>
    </body>
    """

# -------------------
# CHECKOUT
# -------------------
@app.route("/checkout")
def checkout():
    try:
        session_stripe = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "eur",
                    "product_data": {"name": "CyberShield Pro"},
                    "unit_amount": 999,
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=request.host_url + "success",
            cancel_url=request.host_url + "pricing",
        )
        return redirect(session_stripe.url)
    except Exception as e:
        return str(e)

# -------------------
# SUCCESS
# -------------------
@app.route("/success")
def success():
    if "user" in session:
        user = User.query.filter_by(email=session["user"]).first()
        if user:
            user.is_pro = True
            db.session.commit()

    return "<h1>Pro activé</h1><a href='/dashboard'>Dashboard</a>"

# -------------------
# SIGNUP
# -------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        try:
            email = request.form["email"]
            password = request.form["password"]

            db.session.add(User(
                email=email,
                password=generate_password_hash(password)
            ))
            db.session.commit()

            return redirect("/login")

        except Exception as e:
            return f"Erreur signup: {str(e)}"

    return """
    <h1>Signup</h1>
    <form method="POST">
        <input name="email"><br><br>
        <input name="password" type="password"><br><br>
        <button>Create</button>
    </form>
    """

# -------------------
# LOGIN
# -------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            user = User.query.filter_by(email=request.form["email"]).first()

            if user and check_password_hash(user.password, request.form["password"]):
                session["user"] = user.email
                return redirect("/dashboard")

            return "Login failed"

        except Exception as e:
            return str(e)

    return """
    <h1>Login</h1>
    <form method="POST">
        <input name="email"><br><br>
        <input name="password" type="password"><br><br>
        <button>Login</button>
    </form>
    """

# -------------------
# DASHBOARD
# -------------------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect("/login")

    user = User.query.filter_by(email=session["user"]).first()

    result = ""

    if request.method == "POST":
        text = request.form["text"]
        score = phishing_ai(text)

        if not user.is_pro:
            score = min(score, 50)

        result = f"<h2>Score: {score}/100</h2>"

    plan = "PRO" if user.is_pro else "FREE"

    return f"""
    <h1>Dashboard</h1>
    <p>{session["user"]} | {plan}</p>

    <form method="POST">
        <textarea name="text"></textarea><br><br>
        <button>Analyze</button>
    </form>

    {result}
    """

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