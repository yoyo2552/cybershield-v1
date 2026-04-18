from flask import Flask, render_template_string, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = "cybershield_secret"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///saas.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# -------------------
# DATABASE
# -------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(200))

with app.app_context():
    db.create_all()

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
            <p>Détection de messages suspects</p>
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
            return "Email déjà utilisé"

        db.session.add(User(email=email, password=password))
        db.session.commit()

        return redirect("/login")

    return render_template_string("""
    <body style="text-align:center;margin-top:100px;background:#0f172a;color:white;">
        <h1>Signup</h1>
        <form method="POST">
            <input name="email" placeholder="email"><br><br>
            <input name="password" type="password" placeholder="password"><br><br>
            <button>Signup</button>
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
# DASHBOARD
# -------------------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect("/login")

    result = ""

    if request.method == "POST":
        text = request.form["text"]

        score = 80 if "http" in text.lower() else 20
        verdict = "🚨 PHISHING" if score > 60 else "✅ SAFE"

        result = f"<h2>{verdict} - {score}/100</h2>"

    return render_template_string(f"""
    <body style="text-align:center;margin-top:80px;background:#0f172a;color:white;font-family:Arial;">
        <h1>Dashboard CyberShield</h1>

        <form method="POST">
            <textarea name="text" placeholder="message suspect"></textarea><br><br>
            <button>Analyser</button>
        </form>

        {result}

        <br><br>
        <a href="/logout" style="color:#6366f1;">Logout</a>
    </body>
    """)

# -------------------
# LOGOUT
# -------------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

# -------------------
# RUN (RENDER SAFE)
# -------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)