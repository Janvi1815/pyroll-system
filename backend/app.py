from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json
from passlib.hash import bcrypt
from jose import jwt
import datetime, os
import mysql.connector

# Flask app setup with custom templates/static path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")

app = Flask(
    __name__,
    template_folder=os.path.join(FRONTEND_DIR, "templates"),
    static_folder=os.path.join(FRONTEND_DIR, "static")
)
CORS(app)

SECRET_KEY = "mysecret"

# -------- MYSQL CONNECTION --------
def get_db():
    return mysql.connector.connect(
        host="sql.freedb.tech",
        user="freedb_prmusr",
        password="4875#SuP7dp!pxY",
        database="freedb_payroll_mgnt_db",
        port=3306
    )

# -------- AUTH --------
@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    username, password, role = data["username"], data["password"], data["role"]

    # ❌ Block admin signup
    if role == "admin":
        return jsonify({"error": "Admin signup not allowed. Contact system admin."}), 403

    conn = get_db()
    cur = conn.cursor(dictionary=True)

    # check if exists
    cur.execute("SELECT * FROM users WHERE username=%s", (username,))
    if cur.fetchone():
        cur.close()
        conn.close()
        return jsonify({"error": "User exists"}), 400

    hash_pw = bcrypt.hash(password)
    cur.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", (username, hash_pw, role))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"msg": "Signup success"})

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username, password = data["username"], data["password"]

    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM users WHERE username=%s", (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user:
        return jsonify({"error": "Invalid"}), 401
    if not bcrypt.verify(password, user["password"]):
        return jsonify({"error": "Invalid"}), 401

    token = jwt.encode({
        "username": username,
        "role": user["role"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    }, SECRET_KEY, algorithm="HS256")
    return jsonify({"token": token, "role": user["role"]})

def verify_token(request):
    auth = request.headers.get("Authorization")
    if not auth:
        return None
    token = auth.split(" ")[1]
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except:
        return None

# -------- EMPLOYEE EXPENSES --------
@app.route("/expenses", methods=["POST"])
def add_expense():
    user = verify_token(request)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    if user["role"] != "employee":
        return jsonify({"error": "Only employee"}), 403

    data = request.json
    title, amount = data["title"], data["amount"]

    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO expenses (username, title, amount) VALUES (%s, %s, %s)",
                (user["username"], title, amount))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"msg": "Expense added"})

@app.route("/expenses", methods=["GET"])
def list_expenses():
    user = verify_token(request)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, title, amount, created_at FROM expenses WHERE username=%s", (user["username"],))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify(rows)

# -------- SALARY SLIPS (ADMIN + EMPLOYEE VIEW) --------
@app.route("/slips", methods=["POST"])
def create_slip():
    user = verify_token(request)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    if user["role"] != "admin":
        return jsonify({"error": "Only admin"}), 403

    data = request.json
    emp, month, salary = data["employee"], data["month"], data["salary"]

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO salary_slips (employee, month, salary) 
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE salary=%s
    """, (emp, month, salary, salary))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"msg": "Slip created/updated"})

@app.route("/slips/<emp>", methods=["GET"])
def get_slips(emp):
    user = verify_token(request)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    if user["role"] == "employee" and user["username"] != emp:
        return jsonify({"error": "Forbidden"}), 403

    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT employee, month, salary, created_at FROM salary_slips WHERE employee=%s", (emp,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify(rows)

# -------- FRONTEND ROUTES --------
@app.route("/")
def home_page():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")

if __name__ == "__main__":
    app.run(debug=True)
