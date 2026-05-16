import subprocess
import sys
import os
import threading

def run_bot():
    subprocess.run([sys.executable, "bot.py"])

def run_server():
    subprocess.run([sys.executable, "server.py"])

if __name__ == "__main__":
    print("🌸 Starting Zara Bot + Dashboard...")
    
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Run Flask server (main thread)
    run_server()
