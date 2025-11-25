import os
import sqlite3
from functools import wraps
from flask import (
    Flask, render_template, request, jsonify,
    session, redirect, url_for, g
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Secret key for sessions (set SECRET_KEY env var on Render for production)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")

# SQLite database path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "app.db")


def get_db():
    """Open a new database connection per request."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error=None):
    """Close the database at the end of the request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create tables if they don't exist."""
    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """
    )
    db.commit()


def login_required_json(f):
    """Decorator for JSON routes that require login."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return wrapper


@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("index"))
    return render_template("dashboard.html", username=session.get("username"))


# ---------- AUTH API ----------

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip().lower()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    if len(username) < 3 or len(password) < 4:
        return jsonify({"error": "Username or password too short"}), 400

    db = get_db()
    try:
        db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, generate_password_hash(password)),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already taken"}), 400

    return jsonify({"message": "Registered successfully"})


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip().lower()
    password = data.get("password") or ""

    db = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()

    if user is None or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid username or password"}), 401

    session["user_id"] = user["id"]
    session["username"] = username

    return jsonify({"message": "Logged in successfully"})


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})


# ---------- NOTES API ----------

@app.route("/api/notes", methods=["GET", "POST"])
@login_required_json
def notes():
    db = get_db()
    user_id = session["user_id"]

    if request.method == "POST":
        data = request.get_json() or {}
        content = (data.get("content") or "").strip()
        if not content:
            return jsonify({"error": "Note cannot be empty"}), 400

        cur = db.execute(
            "INSERT INTO notes (user_id, content) VALUES (?, ?)",
            (user_id, content),
        )
        db.commit()
        note_id = cur.lastrowid

        note = db.execute(
            "SELECT id, content, created_at FROM notes WHERE id = ?", (note_id,)
        ).fetchone()
        return jsonify({"note": dict(note)}), 201

    # GET
    cur = db.execute(
        "SELECT id, content, created_at FROM notes WHERE user_id = ? "
        "ORDER BY created_at DESC",
        (user_id,),
    )
    notes_list = [dict(row) for row in cur.fetchall()]
    return jsonify({"notes": notes_list})


@app.route("/api/notes/<int:note_id>", methods=["DELETE"])
@login_required_json
def delete_note(note_id):
    db = get_db()
    user_id = session["user_id"]

    cur = db.execute(
        "SELECT id FROM notes WHERE id = ? AND user_id = ?", (note_id, user_id)
    ).fetchone()
    if cur is None:
        return jsonify({"error": "Note not found"}), 404

    db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    db.commit()
    return jsonify({"message": "Deleted"})


# ---------- INITIALIZE DB FOR FLASK 3+ ----------

# This replaces @app.before_first_request (removed in Flask 3)
with app.app_context():
    init_db()


# Only used if you run it directly (Render uses gunicorn)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
