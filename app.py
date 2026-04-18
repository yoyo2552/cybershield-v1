from flask import Flask, request, redirect
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "cybershield_secret"

# -------------------
# SIMPLE STORAGE (sans DB compliquée pour éviter bugs Render)
# -------------------
users = []

# -------------------
# HOME (STYLE PRO)
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

        .container {
            margin-top: 120px;
        }

        h1 {
            font-size: 50px;
        }

        p {
            color: #cbd5e1;
            font-size: 18px;
        }

        a {
            display: inline-block;
            margin: 10px;
            padding: 12px 20px;
            background: #6366f1;
            color: white;
            text-decoration: none;
            border-radius: 10px;
        }

        a:hover {
            background: #4f46e5;
        }

        .card {
            margin-top: 40px;
            background: rgba(255,255,255,0.05);
            padding: 20px;
            border-radius: 15px;
            width: 60%;
            margin-left: auto;
            margin-right: auto;
        }
    </style>
    </head>

    <body>

    <div class="container">
        <h1>🛡️ CyberShield AI</h1>
        <p>Détecte les messages suspects en 2 secondes</p>

        <a href="/signup">Signup</a>
        <a href="/login">Login</a>

        <div class="card">
            <p>✔ Analyse rapide</p>
            <p>✔ Détection phishing</p>
            <p>✔ Interface moderne</p>
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

        users.append({"email": email, "password": password})

        return redirect("/login")

    return """
    <form method="POST" style="text-align:center;margin-top:100px;">
        <input name="email" placeholder="email"><br><br>
        <input name="password" type="password" placeholder="password"><br><br>
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

        for u in users:
            if u["email"] == email and check_password_hash(u["password"], password):
                return redirect("/dashboard")

        return "Login failed"

    return """
    <form method="POST" style="text-align:center;margin-top:100px;">
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
    result = ""

    if request.method == "POST":
        text = request.form["text"]

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
    <body style="font-family:Arial;text-align:center;margin-top:80px;background:#0f172a;color:white;">

    <h1>Dashboard CyberShield</h1>

    <form method="POST">
        <textarea name="text" style="width:300px;height:100px;"></textarea><br><br>
        <button>Analyser</button>
    </form>

    {result}

    <br><br>
    <a href="/" style="color:#6366f1;">Home</a>

    </body>
    </html>
    """

# -------------------
# RUN (RENDER SAFE)
# -------------------
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)