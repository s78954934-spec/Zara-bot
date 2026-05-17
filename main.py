import subprocess
import sys
import threading
import time

def run_bot():
    while True:
        subprocess.run([sys.executable, "bot.py"])
        time.sleep(5)  # restart after 5 sec if crashes

def run_server():
    subprocess.run([sys.executable, "server.py"])

if __name__ == "__main__":
    print("Starting Zara Bot + Dashboard...")
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    run_server()
    
