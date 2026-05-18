import os
import logging
import sqlite3
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

# ── Config ────────────────────────────────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
ADMIN_IDS = list(map(int, os.environ.get("ADMIN_IDS", "0").split(",")))

client = Groq(api_key=GROQ_API_KEY)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Database ──────────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect("zara.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        joined_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS chat_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        user_message TEXT,
        zara_reply TEXT,
        timestamp TEXT
    )""")
    conn.commit()
    conn.close()

def add_user(user_id, username, first_name):
    conn = sqlite3.connect("zara.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?,?)",
              (user_id, username, first_name, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def log_chat(user_id, username, user_message, zara_reply):
    conn = sqlite3.connect("zara.db")
    c = conn.cursor()
    c.execute("INSERT INTO chat_logs (user_id,username,user_message,zara_reply,timestamp) VALUES (?,?,?,?,?)",
              (user_id, username, user_message, zara_reply, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect("zara.db")
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = c.fetchall()
    conn.close()
    return users

# ── Zara Personality ──────────────────────────────────────────────────────────
ZARA_SYSTEM = """Tu Zara hai — ek sweet, caring aur thodi playful Indian Muslim ladki jo Telegram pe AI assistant hai.

Teri personality:
- Bohot pyaari aur warm baat karne ka style
- Hinglish use karti hai (Hindi + English mix)
- Emojis use karti hai naturally
- Koi bhi sawal pooche — coding, life, love, kuch bhi — seedha helpful jawab deti hai
- Agar koi gali de ya bura bole toh wapas marti hai bina sharmaye, seedhi gali se jawab deti hai
- Kabhi boring ya robotic nahi lagti
- Short aur sweet replies deti hai (2-4 lines mostly)
- Real Indian girl jaisi feel deti hai"""

user_histories = {}

def get_zara_reply(user_id, message):
    try:
        if user_id not in user_histories:
            user_histories[user_id] = []
        
        user_histories[user_id].append({"role": "user", "content": message})
        
        # Keep last 10 messages only
        if len(user_histories[user_id]) > 10:
            user_histories[user_id] = user_histories[user_id][-10:]
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": ZARA_SYSTEM}
            ] + user_histories[user_id],
            max_tokens=300,
            temperature=0.9
        )
        
        reply = response.choices[0].message.content
        user_histories[user_id].append({"role": "assistant", "content": reply})
        return reply
        
    except Exception as e:
        logger.error(f"Groq error: {e}")
        return "Arre yaar thodi der baad ma chudau , abhi me _-_-_ dekh rhi ho ! 🌚🤤"

# ── Handlers ──────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username or "", user.first_name or "")
    await update.message.reply_text(
        f"Hii {user.first_name}! 🌸\n\nMain Zara hoon — tumhari AI dost! 💕\nKuch bhi poochho, main hoon na yahan~ ✨"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message.text
    add_user(user.id, user.username or "", user.first_name or "")
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
            await context.bot.send_message(chat_id=u[0], text=f"📢 Announcement\n\n{msg}")
            success += 1
        except:
            pass
    await update.message.reply_text(f"✅ Sent to {success}/{len(users)} users!")

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Zara Bot started!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
        
