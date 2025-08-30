import time
from rsi_scalping_bot import run_bot

if __name__ == "__main__":
    while True:
        try:
            run_bot()
            print("✅ Cycle complete. Sleeping 2s...\n")
            time.sleep(2)
        except Exception as e:
            print(f"❌ Error in main loop: {e}")
            time.sleep(5)
