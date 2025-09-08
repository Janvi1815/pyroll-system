from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os, datetime, hashlib
import pymysql
from jose import jwt

# ----------------- CONFIG -----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")

app = Flask(
    __name__,
    template_folder=os.path.join(FRONTEND_DIR, "templates"),
    static_folder=os.path.join(FRONTEND_DIR, "static")
)
CORS(app)

SECRET_KEY = "mysecret"

# ----------------- DB CONNECTION -----------------
def get_db():
    return pymysql.connect(
        host="sql12.freesqldatabase.com",
        user="sql12797590",
        password="FLlGlPEFib",
        database="sql12797590",
        port=3306,
        cursorclass=pymysql.cursors.DictCursor
    )

# ----------------- SIMPLE HASH UTILS -----------------
def hash_password(password: str) -> str:
    """Hash a password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Check SHA256 password hash."""
    return hash_password(password) == hashed

# ----------------- TOKEN VERIFY -----------------
def verify_token(request):
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        return None
    token = auth.split(" ")[1]
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except Exception:
        return None

# ----------------- AUTH -----------------
@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    username, password, role = data.get("username"), data.get("password"), data.get("role")

    if not username or not password or not role:
        return jsonify({"error": "Missing fields"}), 400

    if role.lower() == "admin":
        return jsonify({"error": "Admin signup not allowed. Contact system admin."}), 403

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username=%s", (username,))
            if cur.fetchone():
                return jsonify({"error": "User already exists"}), 400

            hash_pw = hash_password(password)
            cur.execute(
                "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                (username, hash_pw, role)
            )
        conn.commit()
        return jsonify({"msg": "Signup successful"})
    finally:
        conn.close()

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username, password = data.get("username"), data.get("password")

    if not username or not password:
        return jsonify({"error": "Missing credentials"}), 400

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username=%s", (username,))
            user = cur.fetchone()

        if not user or not verify_password(password, user["password"]):
            return jsonify({"error": "Invalid username or password"}), 401

        token = jwt.encode({
            "username": username,
            "role": user["role"],
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
        }, SECRET_KEY, algorithm="HS256")

        return jsonify({"token": token, "role": user["role"]})
    finally:
        conn.close()

# ----------------- EMPLOYEE EXPENSES -----------------
@app.route("/expenses", methods=["POST"])
def add_expense():
    user = verify_token(request)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    if user["role"] != "employee":
        return jsonify({"error": "Only employees can add expenses"}), 403

    data = request.json
    title, amount = data.get("title"), data.get("amount")

    if not title or not amount:
        return jsonify({"error": "Missing fields"}), 400

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO expenses (username, title, amount) VALUES (%s, %s, %s)",
                (user["username"], title, amount)
            )
        conn.commit()
        return jsonify({"msg": "Expense added"})
    finally:
        conn.close()

@app.route("/expenses", methods=["GET"])
def list_expenses():
    user = verify_token(request)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, title, amount, created_at FROM expenses WHERE username=%s",
                (user["username"],)
            )
            rows = cur.fetchall()
        return jsonify(rows)
    finally:
        conn.close()

# ----------------- SALARY SLIPS -----------------
@app.route("/slips", methods=["POST"])
def create_slip():
    user = verify_token(request)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    if user["role"] != "admin":
        return jsonify({"error": "Only admin can create salary slips"}), 403

    data = request.json
    emp, month, salary = data.get("employee"), data.get("month"), data.get("salary")

    if not emp or not month or not salary:
        return jsonify({"error": "Missing fields"}), 400

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO salary_slips (employee, month, salary)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE salary=%s
            """, (emp, month, salary, salary))
        conn.commit()
        return jsonify({"msg": "Salary slip created/updated"})
    finally:
        conn.close()

@app.route("/slips/<emp>", methods=["GET"])
def get_slips(emp):
    user = verify_token(request)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    if user["role"] == "employee" and user["username"] != emp:
        return jsonify({"error": "Forbidden"}), 403

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT employee, month, salary, created_at FROM salary_slips WHERE employee=%s",
                (emp,)
            )
            rows = cur.fetchall()
        return jsonify(rows)
    finally:
        conn.close()

# ----------------- FRONTEND ROUTES -----------------
@app.route("/")
def home_page():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")

# ----------------- MAIN -----------------
if __name__ == "__main__":
    app.run(debug=True)
