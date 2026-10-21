import os
import time
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, jsonify, request

app = Flask(__name__)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "postgres"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "dbname": os.getenv("DB_NAME", "usermgmt"),
    "user": os.getenv("DB_USER", "appuser"),
    "password": os.getenv("DB_PASSWORD", ""),
}

@contextmanager
def db():
    conn = psycopg2.connect(**DB_CONFIG, connect_timeout=3)
    try:
        yield conn
    finally:
        conn.close()

def ensure_table(retries=10):
    for i in range(retries):
        try:
            with db() as conn, conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        name TEXT NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                """)
                conn.commit()
            print("ensure_table: OK", flush=True)
            return
        except Exception as e:
            print("ensure_table attempt %d/%d failed: %s" % (i+1, retries, e), flush=True)
            time.sleep(2)
    print("ensure_table: giving up", flush=True)

@app.get("/healthz")
def healthz():
    return jsonify(status="ok"), 200

@app.get("/ready")
def ready():
    try:
        with db() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
        return jsonify(status="ready"), 200
    except Exception as e:
        return jsonify(status="not ready", error=str(e)), 503

@app.get("/users")
def list_users():
    with db() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT id, name, email, created_at FROM users ORDER BY id")
        rows = cur.fetchall()
    return jsonify(rows), 200

@app.post("/users")
def create_user():
    data = request.get_json(silent=True) or {}
    name, email = data.get("name"), data.get("email")
    if not name or not email:
        return jsonify(error="name and email are required"), 400
    try:
        with db() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO users (name, email) VALUES (%s, %s) "
                "RETURNING id, name, email, created_at",
                (name, email),
            )
            row = cur.fetchone()
            conn.commit()
        return jsonify(row), 201
    except psycopg2.errors.UniqueViolation:
        return jsonify(error="email already exists"), 409

@app.get("/users/<int:user_id>")
def get_user(user_id):
    with db() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "SELECT id, name, email, created_at FROM users WHERE id = %s",
            (user_id,),
        )
        row = cur.fetchone()
    if not row:
        return jsonify(error="user not found"), 404
    return jsonify(row), 200

@app.put("/users/<int:user_id>")
def update_user(user_id):
    data = request.get_json(silent=True) or {}
    with db() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "UPDATE users SET name = COALESCE(%s, name), "
            "email = COALESCE(%s, email) WHERE id = %s "
            "RETURNING id, name, email, created_at",
            (data.get("name"), data.get("email"), user_id),
        )
        row = cur.fetchone()
        conn.commit()
    if not row:
        return jsonify(error="user not found"), 404
    return jsonify(row), 200

@app.delete("/users/<int:user_id>")
def delete_user(user_id):
    with db() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM users WHERE id = %s RETURNING id", (user_id,))
        row = cur.fetchone()
        conn.commit()
    if not row:
        return jsonify(error="user not found"), 404
    return jsonify(deleted=user_id), 200

ensure_table()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)