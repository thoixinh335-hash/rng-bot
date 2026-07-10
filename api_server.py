"""
Royal City Admin API - Chạy trên VPS cùng bot
pm2 start api_server.py --name rng-api --interpreter python3
Truy cập: http://VPS_IP:5555
"""
from flask import Flask, jsonify, request
import sqlite3
import os
import json
from datetime import datetime

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "rng.db")
CONFIG_PATH = os.path.join(BASE_DIR, "config", "config.json")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def home():
    return jsonify({"name": "Royal City Admin API", "status": "running"})

@app.route("/api/dashboard")
def dashboard():
    db = get_db()
    c = db.cursor()
    c.execute("SELECT COUNT(*) FROM royal_profiles"); profiles = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM players"); players = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM collections"); collections = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM history"); history = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM confessions"); confessions = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM royal_profiles WHERE spouse_id IS NOT NULL"); married = c.fetchone()[0]
    c.execute("SELECT MAX(love_points) FROM royal_profiles"); max_love = c.fetchone()[0] or 0
    db_size = os.path.getsize(DB_PATH) / 1024
    db.close()
    return jsonify({
        "profiles": profiles, "players": players, "collections": collections,
        "history": history, "confessions": confessions, "married": married,
        "max_love": max_love, "db_size_kb": round(db_size, 1)
    })

@app.route("/api/profiles")
def profiles():
    db = get_db()
    c = db.cursor()
    search = request.args.get("search", "")
    if search:
        if search.isdigit():
            c.execute("SELECT * FROM royal_profiles WHERE id = ? OR CAST(user_id AS TEXT) LIKE ? ORDER BY id", (int(search), f"%{search}%"))
        else:
            c.execute("SELECT * FROM royal_profiles ORDER BY id")
    else:
        c.execute("SELECT * FROM royal_profiles ORDER BY id")
    rows = [dict(r) for r in c.fetchall()]
    db.close()
    return jsonify(rows)

@app.route("/api/profiles/<int:pid>", methods=["PUT"])
def update_profile(pid):
    data = request.json
    db = get_db()
    db.execute("UPDATE royal_profiles SET gender=?, birthday=?, status=?, spouse_id=?, love_points=? WHERE id=?",
              (data.get("gender"), data.get("birthday"), data.get("status"),
               data.get("spouse_id"), data.get("love_points"), pid))
    db.commit(); db.close()
    return jsonify({"ok": True})

@app.route("/api/profiles/<int:pid>", methods=["DELETE"])
def delete_profile(pid):
    db = get_db()
    db.execute("DELETE FROM royal_profiles WHERE id=?", (pid,))
    db.commit(); db.close()
    return jsonify({"ok": True})

@app.route("/api/logs")
def logs():
    latest_log = os.path.join(LOGS_DIR, "latest.log")
    if os.path.exists(latest_log):
        with open(latest_log, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()[-500:]
        return jsonify({"lines": lines})
    return jsonify({"lines": ["Chưa có log."]})

@app.route("/api/config", methods=["GET", "PUT"])
def config():
    if request.method == "GET":
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return jsonify(json.load(f))
        return jsonify({})
    else:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(request.json, f, indent=2, ensure_ascii=False)
        return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5555, debug=False)
