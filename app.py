from flask import Flask, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import os
import stripe

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")

# Stripe
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

# DB
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///saas.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# -------------------
# MODEL
# -------------------
class User(db.Model):
    __tablename__ = "users_v3"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(200))
    is_pro = db.Column(db.Boolean, default=False)
    stripe_customer_id = db.Column(db.String(200))
    subscription_id = db.Column(db.String(200))

with app.app_context():
    db.create_all()

# -------------------
# HOME
# -------------------
@app.route("/")
def home():
    return """
    <h1>🛡️ CyberShield AI</h1>
    <p>Protection phishing intelligente</p>
    <a href="/signup">Start Free</a><br><br>
    <a href="/pricing">Pricing</a>
    """

# -------------------
# PRICING
# -------------------
@app.route("/pricing")
def pricing():
    return """
    <h1>Pricing</h1>
    <p>Free: limité</p>
    <p>Pro: 9€/mois</p>
    <a href="/checkout">Upgrade Pro</a>
    """

# -------------------
# SIGNUP
# -------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        if len(password) < 6:
            return "Mot de passe trop court"

        user = User(email=email, password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()

        return redirect("/login")

    return """
    <h1>Signup</h1>
    <form method="POST">
        <input name="email" required><br><br>
        <input name="password" type="password" required><br><br>
        <button>Create</button>
    </form>
    """

# -------------------
# LOGIN
# -------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form["email"]).first()

        if user and check_password_hash(user.password, request.form["password"]):
            session["user"] = user.email
            return redirect("/dashboard")

        return "Login failed"

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
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    user = User.query.filter_by(email=session["user"]).first()

    plan = "PRO" if user.is_pro else "FREE"

    return f"""
    <h1>Dashboard</h1>
    <p>{user.email}</p>
    <p>Plan: {plan}</p>

    <a href="/checkout">Upgrade</a><br><br>
    <a href="/logout">Logout</a>
    """

# -------------------
# CHECKOUT (SUBSCRIPTION)
# -------------------
@app.route("/checkout")
def checkout():
    try:
        session_stripe = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{
                "price": "price_xxx",  # ⚠️ remplace par ton ID Stripe
                "quantity": 1,
            }],
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
    return "<h1>Paiement réussi</h1><a href='/dashboard'>Dashboard</a>"

# -------------------
# WEBHOOK (SECURE)
# -------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")
    endpoint_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except:
        return "Error", 400

    if event["type"] == "checkout.session.completed":
        session_data = event["data"]["object"]

        email = session_data["customer_details"]["email"]

        user = User.query.filter_by(email=email).first()

        if user:
            user.is_pro = True
            db.session.commit()

    return "OK"

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