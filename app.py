from flask import Flask, request, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "cybershield_key"

# -------------------
# DATABASE (simple & stable)
# -------------------
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# -------------------
# MODELS
# -------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(200))

# -------------------
# CREATE DB
# -------------------
with app.app_context():
    db.create_all()

# -------------------
# HOME
# -------------------
@app.route("/")
def home():
    return """
    <html>
    <body style="font-family:Arial;text-align:center;margin-top:100px;">
        <h1>🛡️ CyberShield AI</h1>
        <p>Détection de messages suspects</p>

        <a href="/signup">Signup</a> |
        <a href="/login">Login</a>
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

        if User.query.filter_by(email=email).first():
            return "Email déjà utilisé"

        user = User(email=email, password=password)
        db.session.add(user)
        db.session.commit()

        return redirect("/login")

    return """
    <form method="POST">
        <input name="email" placeholder="email"><br>
        <input name="password" type="password" placeholder="password"><br>
        <button>Signup</button>
    </form>
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
            return redirect("/dashboard")

        return "Login failed"

    return """
    <form method="POST">
        <input name="email"><br>
        <input name="password" type="password"><br>
        <button>Login</button>
    </form>
    """

# -------------------
# DASHBOARD
# -------------------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    result = ""

    if request.method == "POST":
        text = request.form["text"]

        score = 50 if "http" in text else 10

        if score > 40:
            verdict = "⚠️ SUSPECT"
        else:
            verdict = "✅ SAFE"

        result = f"<h2>{verdict} - Score {score}</h2>"

    return f"""
    <h1>Dashboard CyberShield</h1>

    <form method="POST">
        <textarea name="text" placeholder="message"></textarea><br>
        <button>Analyser</button>
    </form>

    {result}

    <br><a href="/">Home</a>
    """

# -------------------
# RUN (IMPORTANT RENDER)
# -------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)