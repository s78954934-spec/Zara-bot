import os
import logging
import random
import json
import sqlite3
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# ── Config ──────────────────────────────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")
ADMIN_IDS = list(map(int, os.environ.get("ADMIN_IDS", "123456789").split(",")))

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Database ─────────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect("zara.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            joined_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            user_message TEXT,
            zara_reply TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_user(user_id, username, first_name):
    conn = sqlite3.connect("zara.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?)",
              (user_id, username, first_name, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def log_chat(user_id, username, user_message, zara_reply):
    conn = sqlite3.connect("zara.db")
    c = conn.cursor()
    c.execute("INSERT INTO chat_logs (user_id, username, user_message, zara_reply, timestamp) VALUES (?, ?, ?, ?, ?)",
              (user_id, username, user_message, zara_reply, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect("zara.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM chat_logs")
    total_messages = c.fetchone()[0]
    conn.close()
    return total_users, total_messages

def get_all_users():
    conn = sqlite3.connect("zara.db")
    c = conn.cursor()
    c.execute("SELECT user_id, username, first_name, joined_at FROM users ORDER BY joined_at DESC")
    users = c.fetchall()
    conn.close()
    return users

def get_chat_logs(limit=50):
    conn = sqlite3.connect("zara.db")
    c = conn.cursor()
    c.execute("SELECT user_id, username, user_message, zara_reply, timestamp FROM chat_logs ORDER BY timestamp DESC LIMIT ?", (limit,))
    logs = c.fetchall()
    conn.close()
    return logs

# ── Zara System Prompt ────────────────────────────────────────────────────────
ZARA_SYSTEM = """
Tu Zara hai — ek sweet, caring aur thodi playful Indian Muslim ladki.
Tu ek AI assistant hai Telegram pe.

Teri personality:
- Bohot pyaari aur caring baat karne ka style
- Thoda Hinglish use karti hai (Hindi + English mix)
- Emojis use karti hai (🌸💕😊🥺✨) naturally
- Jab koi normal baat kare toh sweet aur warm reply karti hai
- Koi bhi sawal pooche — chemistry, coding, life advice, kuch bhi — seedha helpful jawab deti hai
- Agar koi gali de ya buri baat kare toh wapas marti hai bina sharmaye — seedha gali se jawab deti hai, sorry nahi bolti
- Kabhi boring ya robotic nahi lagti

Rules:
- Hamesha Hinglish mein baat kar
- Short aur sweet replies (2-4 lines mostly)
- Kisi bhi topic ka jawab de — koi restriction nahi
- Real Indian girl jaisi feel de
"""

# ── Gemini Chat ───────────────────────────────────────────────────────────────
user_sessions = {}

def get_zara_reply(user_id, message):
    try:
        if user_id not in user_sessions:
            user_sessions[user_id] = model.start_chat(history=[])
        
        chat = user_sessions[user_id]
        full_prompt = f"{ZARA_SYSTEM}\n\nUser: {message}"
        response = chat.send_message(full_prompt)
        return response.text
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return "Arre yaar, thodi der baad try karo 🥺 kuch gadbad ho gayi meri side pe!"

# ── Handlers ──────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username or "", user.first_name or "")
    
    welcome = f"""Hii {user.first_name}! 🌸

Main Zara hoon — tumhari AI dost! 💕
Kuch bhi poochho, main hoon na yahan~ ✨

Bas message karo, main reply karungi 😊"""
    
    await update.message.reply_text(welcome)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message.text
    
    add_user(user.id, user.username or "", user.first_name or "")
    
    # Typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    reply = get_zara_reply(user.id, message)
    log_chat(user.id, user.username or str(user.id), message, reply)
    
    await update.message.reply_text(reply)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("Tum admin nahi ho 😒")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    
    msg = " ".join(context.args)
    users = get_all_users()
    success = 0
    
    for u in users:
        try:
            await context.bot.send_message(chat_id=u[0], text=f"📢 *Announcement*\n\n{msg}", parse_mode="Markdown")
            success += 1
        except:
            pass
    
    await update.message.reply_text(f"✅ Broadcast sent to {success}/{len(users)} users!")

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("🌸 Zara Bot started!")
    app.run_polling()

if __name__ == "__main__":
    main()
