from flask import Flask, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import os
import stripe

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cybershield_secret")

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
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(200))
    is_pro = db.Column(db.Boolean, default=False)

# -------------------
# 🔥 FIX DB (AJOUT COLONNE SI MANQUANTE)
# -------------------
with app.app_context():
    db.create_all()

    try:
        db.session.execute("ALTER TABLE user ADD COLUMN is_pro BOOLEAN DEFAULT 0")
        db.session.commit()
        print("Colonne is_pro ajoutée")
    except:
        pass  # déjà existante

# -------------------
# HOME
# -------------------
@app.route("/")
def home():
    return redirect("/signup")

# -------------------
# SIGNUP
# -------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        try:
            email = request.form["email"]
            password = request.form["password"]

            user = User(email=email, password=generate_password_hash(password))
            db.session.add(user)
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
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect("/login")

    user = User.query.filter_by(email=session["user"]).first()

    return f"""
    <h1>Dashboard</h1>
    <p>{user.email}</p>
    <p>Plan: {"PRO" if user.is_pro else "FREE"}</p>

    <a href="/checkout">Upgrade Pro</a><br><br>
    <a href="/logout">Logout</a>
    """

# -------------------
# STRIPE
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
            cancel_url=request.host_url,
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
        user.is_pro = True
        db.session.commit()

    return "<h1>Pro activé</h1><a href='/dashboard'>Dashboard</a>"

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