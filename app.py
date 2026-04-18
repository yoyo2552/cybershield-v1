from flask import Flask, request, redirect
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "cybershield_secret"

# -------------------
# FAKE DATABASE (stable Render)
# -------------------
users = []

# -------------------
# HOME
# -------------------
@app.route("/")
def home():
    return """
    <html>
    <head>
    <style>
        body {
            margin: 0;
            font-family: Arial;
            background: linear-gradient(135deg, #0f172a, #1e293b);
            color: white;
            text-align: center;
        }
        .container { margin-top: 120px; }
        h1 { font-size: 50px; }
        p { color: #cbd5e1; }
        a {
            display: inline-block;
            margin: 10px;
            padding: 12px 20px;
            background: #6366f1;
            color: white;
            text-decoration: none;
            border-radius: 10px;
        }
    </style>
    </head>
    <body>
        <div class="container">
            <h1>🛡️ CyberShield AI</h1>
            <p>Détecte les messages suspects</p>
            <a href="/signup">Signup</a>
            <a href="/login">Login</a>
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
        email = request.form.get("email")
        password = generate_password_hash(request.form.get("password"))

        # éviter doublon
        for u in users:
            if u["email"] == email:
                return "Email déjà utilisé"

        users.append({
            "email": email,
            "password": password
        })

        return redirect("/login")

    return """
    <html>
    <body style="text-align:center;margin-top:100px;background:#0f172a;color:white;">
        <h1>Signup</h1>
        <form method="POST">
            <input name="email" placeholder="Email"><br><br>
            <input name="password" type="password" placeholder="Password"><br><br>
            <button>Signup</button>
        </form>
        <br>
        <a href="/">Home</a>
    </body>
    </html>
    """

# -------------------
# LOGIN (FIXÉ + SÉCURISÉ)
# -------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        for u in users:
            if u["email"] == email and check_password_hash(u["password"], password):
                return redirect("/dashboard")

        return "<h3 style='color:red;text-align:center'>Login failed</h3>"

    return """
    <html>
    <body style="text-align:center;margin-top:100px;background:#0f172a;color:white;">
        <h1>Login</h1>

        <form method="POST">
            <input name="email" placeholder="Email"><br><br>
            <input name="password" type="password" placeholder="Password"><br><br>
            <button>Login</button>
        </form>

        <br>
        <a href="/">Home</a>
    </body>
    </html>
    """

# -------------------
# DASHBOARD
# -------------------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    result = ""

    if request.method == "POST":
        text = request.form.get("text")

        score = 80 if "http" in text.lower() else 20

        if score > 60:
            verdict = "🚨 PHISHING"
        elif score > 30:
            verdict = "⚠️ SUSPECT"
        else:
            verdict = "✅ SAFE"

        result = f"<h2>{verdict} - Score {score}</h2>"

    return f"""
    <html>
    <body style="text-align:center;margin-top:80px;background:#0f172a;color:white;font-family:Arial;">

        <h1>Dashboard CyberShield</h1>

        <form method="POST">
            <textarea name="text" placeholder="message suspect" style="width:300px;height:100px;"></textarea><br><br>
            <button>Analyser</button>
        </form>

        {result}

        <br><br>
        <a href="/" style="color:#6366f1;">Home</a>

    </body>
    </html>
    """

# -------------------
# RUN
# -------------------
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)