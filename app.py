from flask import Flask, render_template_string, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import os
import re
import stripe

app = Flask(__name__)

# 🔐 CONFIG
app.secret_key = os.environ.get("SECRET_KEY", "cybershield_secret")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# 💳 STRIPE
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

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
    is_pro = db.Column(db.Boolean, default=False)

with app.app_context():
    db.create_all()

# -------------------
# AI PHISHING
# -------------------
def phishing_ai(text):
    text = text.lower()
    score = 0
    reasons = []

    keywords = {
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

    for k, v in keywords.items():
        if k in text:
            score += v
            reasons.append(f"Mot suspect: {k}")

    if text.isupper():
        score += 10
        reasons.append("MAJUSCULES")

    if text.count("!") > 2:
        score += 10
        reasons.append("Spam !!!")

    return min(score, 100), reasons

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
    return render_template_string("""
    <body style="font-family:Arial;background:#0b1220;color:white;text-align:center;">

        <h1 style="margin-top:80px;">🛡️ CyberShield AI</h1>

        <div style="display:flex;justify-content:center;margin-top:50px;">

            <div style="background:#111827;padding:20px;margin:10px;border-radius:15px;width:200px;">
                <h2>Free</h2>
                <p>Basic AI scan</p>
                <a href="/signup" style="color:#4f46e5;">Start</a>
            </div>

            <div style="background:#111827;padding:20px;margin:10px;border-radius:15px;width:200px;">
                <h2>Pro</h2>
                <p>Full AI detection</p>
                <a href="/checkout" style="padding:10px;background:#4f46e5;color:white;text-decoration:none;border-radius:10px;">
                    Upgrade 9.99€
                </a>
            </div>

        </div>

    </body>
    """)

# -------------------
# STRIPE CHECKOUT
# -------------------
@app.route("/checkout")
def checkout():
    try:
        stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

        session_stripe = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": "CyberShield AI Pro"
                    },
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
        return f"<pre style='color:red'>{str(e)}</pre>"

# -------------------
# SUCCESS → ACTIVATE PRO
# -------------------
@app.route("/success")
def success():
    if "user" in session:
        user = User.query.filter_by(email=session["user"]).first()
        if user:
            user.is_pro = True
            db.session.commit()

    return """
    <h1 style="text-align:center;color:green;margin-top:100px;">
        🎉 Pro activé !
    </h1>
    <a href="/dashboard" style="display:block;text-align:center;">Go Dashboard</a>
    """

# -------------------
# SIGNUP
# -------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not email or not password:
            return "Champs requis"

        if User.query.filter_by(email=email).first():
            return "Email déjà utilisé"

        db.session.add(User(
            email=email,
            password=generate_password_hash(password)
        ))
        db.session.commit()

        return redirect("/login")

    return render_template_string("""
    <body style="text-align:center;margin-top:100px;background:#0b1220;color:white;">
        <h1>Signup</h1>
        <form method="POST">
            <input name="email"><br><br>
            <input name="password" type="password"><br><br>
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
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            return "Login failed"

        session["user"] = user.email
        return redirect("/dashboard")

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
# DASHBOARD (FREE / PRO)
# -------------------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect("/login")

    user = User.query.filter_by(email=session["user"]).first()

    result = ""

    if request.method == "POST":
        text = request.form.get("text", "")

        score, reasons = phishing_ai(text)

        # 🔥 LIMIT FREE
        if not user.is_pro:
            if len(text) > 100:
                return "<h2 style='color:red'>Free limit: 100 chars max. Upgrade Pro.</h2>"
            score = min(score, 60)

        if score >= 70:
            verdict = "🚨 PHISHING"
            color = "red"
        elif score >= 40:
            verdict = "⚠️ SUSPECT"
            color = "orange"
        else:
            verdict = "✅ SAFE"
            color = "green"

        result = f"""
        <div style="margin-top:20px;padding:20px;background:#111827;border-radius:15px;">
            <h2 style="color:{color}">{verdict}</h2>
            <p>Score: {score}/100</p>
            <p>{"<br>".join(reasons)}</p>
        </div>
        """

    plan = "PRO" if user.is_pro else "FREE"

    return render_template_string(f"""
    <body style="font-family:Arial;background:#0b1220;color:white;text-align:center;">

        <h1>CyberShield Dashboard</h1>
        <p>User: {session["user"]} | Plan: {plan}</p>

        <form method="POST">
            <textarea name="text" style="width:400px;height:120px;"></textarea><br><br>
            <button>Analyze</button>
        </form>

        {result}

        <br><br>
        <a href="/logout" style="color:#4f46e5;">Logout</a>

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