Railway pe ye Environment Variables add karna:

BOT_TOKEN = 8805223659:AAEYu0HAXw1nu49XgFQyk7b_OR_dIboHgS0
GEMINI_API_KEY = AIzaSyAvnwG_tdm4Hu0FLpFC-9m9HfYwIOyHvDo
ADMIN_IDS = YOUR_TELEGRAM_USER_ID
ADMIN_PASSWORD = zara@admin2025

---
ADMIN_IDS kaise pata kare:
@userinfobot pe /start bhejo, woh tumhara ID batayega

---
Dashboard URL:
https://YOUR-APP.railway.app/

---
FILES STRUCTURE:
zara_bot/
├── main.py          ← Entry point
├── bot.py           ← Zara Telegram bot
├── server.py        ← Flask dashboard server
├── requirements.txt ← Dependencies
├── Procfile         ← Railway config
└── dashboard/
    └── index.html   ← Admin panel
