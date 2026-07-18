"""
Royal City Admin API - Chay tren VPS cung bot
"""
from flask import Flask, jsonify, request
import sqlite3, os, json, requests, shutil
from datetime import datetime
import re

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "rng.db")
CONFIG_PATH = os.path.join(BASE_DIR, "config", "config.json")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
ROLES_PATH = os.path.join(BASE_DIR, "data", "roles.json")
MEMBER_IDS_PATH = os.path.join(BASE_DIR, "assets", "member_ids.txt")


def get_guild_member_ids() -> set:
    """Đọc danh sách member ID từ file bot ghi"""
    try:
        if os.path.exists(MEMBER_IDS_PATH):
            with open(MEMBER_IDS_PATH) as f:
                return {int(line.strip()) for line in f if line.strip().isdigit()}
    except:
        pass
    return set()

# === Discord API (khong can token, public user data) ===
DISCORD_API = "https://discord.com/api/v10"

def get_discord_user(user_id):
    """Lay avatar + ten tu Discord bang API (khong can auth cho public data)"""
    try:
        resp = requests.get(f"{DISCORD_API}/users/{user_id}", timeout=5)
        if resp.status_code == 200:
            d = resp.json()
            username = d.get("username", "Unknown")
            avatar_hash = d.get("avatar")
            if avatar_hash:
                ext = "gif" if avatar_hash.startswith("a_") else "png"
                avatar_url = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.{ext}?size=64"
            else:
                avatar_url = f"https://cdn.discordapp.com/embed/avatars/{(int(d.get('discriminator', '0')[0]) % 5) if d.get('discriminator') else 0}.png"
            return {"username": username, "avatar_url": avatar_url}
    except:
        pass
    return None

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def home():
    return jsonify({"name": "Royal City Admin API", "status": "running", "version": "2.0"})

# ==========================================
# DASHBOARD
# ==========================================
@app.route("/api/dashboard")
def dashboard():
    db = get_db(); c = db.cursor()
    c.execute("SELECT COUNT(*) FROM royal_profiles"); profiles = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM players"); players = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM collections"); collections = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM history"); history = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM confessions"); confessions = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM royal_profiles WHERE spouse_id IS NOT NULL"); married = c.fetchone()[0]
    c.execute("SELECT MAX(love_points) FROM royal_profiles"); max_love = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM daily_missions"); missions = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM seasons"); seasons = c.fetchone()[0]
    db_size = os.path.getsize(DB_PATH) / 1024
    # Count logs
    latest_log = os.path.join(LOGS_DIR, "latest.log")
    log_lines = sum(1 for _ in open(latest_log, encoding="utf-8", errors="ignore")) if os.path.exists(latest_log) else 0
    db.close()
    return jsonify({
        "profiles": profiles, "players": players, "collections": collections,
        "history": history, "confessions": confessions, "married": married,
        "max_love": max_love, "db_size_kb": round(db_size, 1), "log_lines": log_lines,
        "missions": missions, "seasons": seasons
    })

# ==========================================
# PROFILES (royal_profiles)
# ==========================================
@app.route("/api/profiles")
def profiles():
    db = get_db(); c = db.cursor()
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
    for row in rows:
        uid = row.get("user_id")
        if uid:
            row["discord"] = get_discord_user(uid)
    return jsonify(rows)

@app.route("/api/profiles/<int:pid>", methods=["PUT"])
def update_profile(pid):
    data = request.json
    db = get_db()

    # Lấy user_id của hồ sơ hiện tại
    c = db.cursor()
    c.execute("SELECT user_id FROM royal_profiles WHERE id=?", (pid,))
    row = c.fetchone()
    if not row:
        db.close()
        return jsonify({"error": "Không tìm thấy hồ sơ"}), 404

    current_uid = row[0]
    new_spouse_id = data.get("spouse_id")

    # 1. Xóa spouse cũ (nếu có) - người cũ không còn là tri kỷ nữa
    c.execute("SELECT spouse_id FROM royal_profiles WHERE id=?", (pid,))
    old_row = c.fetchone()
    if old_row and old_row[0] and old_row[0] != new_spouse_id:
        db.execute("UPDATE royal_profiles SET spouse_id=NULL, marriage_date=NULL WHERE user_id=?", (old_row[0],))

    # 2. Nếu có spouse mới, cập nhật cả 2 chiều
    if new_spouse_id:
        # Cập nhật hồ sơ hiện tại
        db.execute("""UPDATE royal_profiles SET gender=?, birthday=?, bio=?, status=?, spouse_id=?, love_points=?, marriage_date=COALESCE(marriage_date, datetime('now')) WHERE id=?""",
                  (data.get("gender"), data.get("birthday"), data.get("bio"), data.get("status"),
                   new_spouse_id, data.get("love_points"), pid))
        # Cập nhật ngược lại cho spouse
        db.execute("UPDATE royal_profiles SET spouse_id=?, marriage_date=COALESCE(marriage_date, datetime('now')) WHERE user_id=?", (current_uid, new_spouse_id))
    else:
        # Xóa spouse - chỉ update hồ sơ hiện tại
        db.execute("UPDATE royal_profiles SET gender=?, birthday=?, bio=?, status=?, spouse_id=NULL, love_points=? WHERE id=?",
                  (data.get("gender"), data.get("birthday"), data.get("bio"), data.get("status"),
                   data.get("love_points"), pid))

    db.commit()
    db.close()
    return jsonify({"ok": True})

@app.route("/api/profiles/<int:pid>", methods=["DELETE"])
def delete_profile(pid):
    db = get_db()
    # Get user_id before delete
    c = db.cursor()
    c.execute("SELECT user_id FROM royal_profiles WHERE id=?", (pid,))
    row = c.fetchone()
    if row:
        uid = row[0]
        # Cắt đứt quan hệ nếu có
        db.execute("UPDATE royal_profiles SET spouse_id=NULL WHERE spouse_id=?", (uid,))
    db.execute("DELETE FROM royal_profiles WHERE id=?", (pid,))
    db.commit(); db.close()
    return jsonify({"ok": True})

# ==========================================
# PLAYERS (RNG players)
# ==========================================
@app.route("/api/players")
def list_players():
    db = get_db(); c = db.cursor()
    search = request.args.get("search", "")
    limit = min(int(request.args.get("limit", 100)), 500)

    if search:
        if search.isdigit():
            c.execute("""SELECT p.*,
                (SELECT COUNT(*) FROM collections WHERE user_id = p.user_id) as collection_count
                FROM players p WHERE CAST(p.user_id AS TEXT) LIKE ? OR p.username LIKE ?
                ORDER BY p.total_rolls DESC LIMIT ?""",
                (f"%{search}%", f"%{search}%", limit))
        else:
            c.execute("""SELECT p.*,
                (SELECT COUNT(*) FROM collections WHERE user_id = p.user_id) as collection_count
                FROM players p ORDER BY p.total_rolls DESC LIMIT ?""", (limit,))
    else:
        c.execute("""SELECT p.*,
            (SELECT COUNT(*) FROM collections WHERE user_id = p.user_id) as collection_count
            FROM players p ORDER BY p.total_rolls DESC LIMIT ?""", (limit,))
    rows = [dict(r) for r in c.fetchall()]
    db.close()
    for row in rows:
        uid = row.get("user_id")
        if uid:
            row["discord"] = get_discord_user(uid)
    return jsonify(rows)

@app.route("/api/players/<int:user_id>", methods=["DELETE"])
def delete_player(user_id):
    db = get_db()
    db.execute("DELETE FROM players WHERE user_id=?", (user_id,))
    db.execute("DELETE FROM collections WHERE user_id=?", (user_id,))
    db.execute("DELETE FROM history WHERE user_id=?", (user_id,))
    db.execute("DELETE FROM daily_missions WHERE user_id=?", (user_id,))
    db.execute("DELETE FROM roll_inventory WHERE user_id=?", (user_id,))
    db.commit(); db.close()
    return jsonify({"ok": True, "message": f"Đã xóa toàn bộ dữ liệu RNG của user {user_id}"})

# ==========================================
# SEASONS
# ==========================================
@app.route("/api/seasons")
def list_seasons():
    db = get_db(); c = db.cursor()
    c.execute("SELECT * FROM seasons ORDER BY season_number DESC")
    rows = [dict(r) for r in c.fetchall()]
    db.close()
    return jsonify(rows)

# ==========================================
# CONFESSIONS
# ==========================================
@app.route("/api/confessions")
def list_confessions():
    db = get_db(); c = db.cursor()
    limit = min(int(request.args.get("limit", 50)), 200)
    c.execute("SELECT id, user_id, content, created_at FROM confessions ORDER BY id DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in c.fetchall()]
    db.close()
    for row in rows:
        uid = row.get("user_id")
        if uid:
            row["discord"] = get_discord_user(uid)
    return jsonify(rows)

@app.route("/api/confessions/<int:cid>", methods=["DELETE"])
def delete_confession(cid):
    db = get_db()
    db.execute("DELETE FROM confessions WHERE id=?", (cid,))
    db.commit(); db.close()
    return jsonify({"ok": True})

# ==========================================
# BACKUP / RESTORE
# ==========================================
@app.route("/api/backups")
def list_backups():
    os.makedirs(ASSETS_DIR, exist_ok=True)
    backups = []
    for f in sorted(os.listdir(ASSETS_DIR)):
        if f.startswith("rng_backup_") and f.endswith(".db"):
            fpath = os.path.join(ASSETS_DIR, f)
            size_kb = round(os.path.getsize(fpath) / 1024, 1)
            backups.append({"filename": f, "size_kb": size_kb, "created": f.replace("rng_backup_", "").replace(".db", "")})
    return jsonify(backups)

@app.route("/api/backup", methods=["POST"])
def create_backup():
    os.makedirs(ASSETS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(ASSETS_DIR, f"rng_backup_{timestamp}.db")
    try:
        shutil.copyfile(DB_PATH, backup_path)
        return jsonify({"ok": True, "filename": f"rng_backup_{timestamp}.db"})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/api/restore/<filename>", methods=["POST"])
def restore_backup(filename):
    source = os.path.join(ASSETS_DIR, filename)
    if not os.path.exists(source):
        return jsonify({"error": "File không tồn tại"})
    try:
        shutil.copyfile(source, DB_PATH)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/api/backups/<filename>", methods=["DELETE"])
def delete_backup(filename):
    fpath = os.path.join(ASSETS_DIR, filename)
    if os.path.exists(fpath):
        os.remove(fpath)
        return jsonify({"ok": True})
    return jsonify({"error": "File không tồn tại"})

# ==========================================
# MAINTENANCE
# ==========================================
@app.route("/api/reset_all", methods=["POST"])
def reset_all():
    db = get_db()
    db.execute("DELETE FROM collections")
    db.execute("DELETE FROM history")
    db.execute("DELETE FROM roll_inventory")
    db.execute("DELETE FROM daily_missions")
    db.execute("DELETE FROM players")
    db.execute("DELETE FROM seasons")
    db.commit(); db.close()
    return jsonify({"ok": True, "message": "Đã reset toàn bộ dữ liệu RNG"})

@app.route("/api/reset_player_all", methods=["POST"])
def reset_all_players():
    db = get_db()
    db.execute("DELETE FROM collections")
    db.execute("DELETE FROM history")
    db.execute("DELETE FROM roll_inventory")
    db.execute("DELETE FROM daily_missions")
    db.execute("DELETE FROM players")
    db.commit(); db.close()
    return jsonify({"ok": True, "message": "Đã xóa toàn bộ dữ liệu người chơi RNG"})

@app.route("/api/reload_config", methods=["POST"])
def reload_config():
    """Ghi lại signal để bot reload (thực tế là đọc config từ file)"""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
        return jsonify({"ok": True, "config": config})
    return jsonify({"error": "Config không tồn tại"})

# ==========================================
# LOGS
# ==========================================
@app.route("/api/logs")
def logs():
    latest_log = os.path.join(LOGS_DIR, "latest.log")
    if os.path.exists(latest_log):
        with open(latest_log, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()[-500:]
        return jsonify({"lines": lines})
    return jsonify({"lines": ["Chua co log."]})

@app.route("/api/logs/clear", methods=["POST"])
def clear_logs():
    for fname in ["latest.log", "errors.log"]:
        fpath = os.path.join(LOGS_DIR, fname)
        if os.path.exists(fpath): open(fpath, "w").close()
    return jsonify({"ok": True})

# ==========================================
# CONFIG
# ==========================================
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

# ==========================================
# ROLES (data/roles.json)
# ==========================================
@app.route("/api/roles")
def list_roles():
    if os.path.exists(ROLES_PATH):
        with open(ROLES_PATH, "r", encoding="utf-8") as f:
            roles = json.load(f)
        return jsonify(roles)
    return jsonify([])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5555, debug=False)
