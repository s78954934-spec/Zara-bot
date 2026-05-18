import os
import json
import sqlite3
import subprocess
import threading
import sys
from flask import Flask, jsonify, request, send_from_directory
from datetime import datetime
import requests

app = Flask(__name__, static_folder="dashboard")

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "zara@admin2025")

# Error log storage
error_logs = []

def get_db():
    conn = sqlite3.connect("zara.db")
    conn.row_factory = sqlite3.Row
    return conn

# ── Serve Dashboard ───────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory("dashboard", "index.html")

# ── Stats ─────────────────────────────────────────────────────────────────────
@app.route("/api/stats")
def stats():
    try:
        conn = get_db()
        total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        total_messages = conn.execute("SELECT COUNT(*) FROM chat_logs").fetchone()[0]
        conn.close()
        return jsonify({"total_users": total_users, "total_messages": total_messages})
    except:
        return jsonify({"total_users": 0, "total_messages": 0})

# ── Users ─────────────────────────────────────────────────────────────────────
@app.route("/api/users")
def users():
    try:
        conn = get_db()
        rows = conn.execute("SELECT user_id, username, first_name, joined_at FROM users ORDER BY joined_at DESC").fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])
    except:
        return jsonify([])

# ── Chat Logs ─────────────────────────────────────────────────────────────────
@app.route("/api/logs")
def logs():
    try:
        conn = get_db()
        rows = conn.execute("SELECT user_id, username, user_message, zara_reply, timestamp FROM chat_logs ORDER BY timestamp DESC LIMIT 100").fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])
    except:
        return jsonify([])

# ── Error Logs ────────────────────────────────────────────────────────────────
@app.route("/api/errors")
def get_errors():
    return jsonify(error_logs[-50:])

@app.route("/api/errors", methods=["POST"])
def add_error():
    data = request.json
    error_logs.append({
        "message": data.get("message", ""),
        "timestamp": datetime.now().isoformat()
    })
    return jsonify({"ok": True})

# ── Broadcast ─────────────────────────────────────────────────────────────────
@app.route("/api/broadcast", methods=["POST"])
def broadcast():
    data = request.json
    msg = data.get("message", "")
    if not msg:
        return jsonify({"error": "No message"}), 400
    try:
        conn = get_db()
        users = conn.execute("SELECT user_id FROM users").fetchall()
        conn.close()
        success = 0
        for u in users:
            try:
                res = requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    json={"chat_id": u["user_id"], "text": f"Announcement\n\n{msg}"},
                    timeout=5
                )
                if res.status_code == 200:
                    success += 1
            except:
                pass
        return jsonify({"message": f"Sent to {success}/{len(users)} users"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── Code Editor ───────────────────────────────────────────────────────────────
@app.route("/api/code", methods=["GET", "POST"])
def code():
    file_map = {
        "bot": "bot.py",
        "dashboard": "dashboard/index.html"
    }
    if request.method == "GET":
        file_key = request.args.get("file", "bot")
        filepath = file_map.get(file_key, "bot.py")
        try:
            with open(filepath, "r") as f:
                return jsonify({"code": f.read()})
        except:
            return jsonify({"code": "# File not found"})
    elif request.method == "POST":
        data = request.json
        file_key = data.get("file", "bot")
        code_content = data.get("code", "")
        filepath = file_map.get(file_key, "bot.py")
        try:
            with open(filepath, "w") as f:
                f.write(code_content)
            return jsonify({"message": "Saved! Bot will restart automatically."})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

# ── Restart ───────────────────────────────────────────────────────────────────
@app.route("/api/restart", methods=["POST"])
def restart():
    def do_restart():
        import time
        time.sleep(1)
        os.execv(sys.executable, [sys.executable] + sys.argv)
    threading.Thread(target=do_restart).start()
    return jsonify({"message": "Restarting..."})

# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    import threading
bot_thread = threading.Thread(target=lambda: os.system("python bot.py"), daemon=True)
bot_thread.start()
app.run(host="0.0.0.0", port=port, debug=False)
    
