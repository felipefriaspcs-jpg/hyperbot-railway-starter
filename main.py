import time
from rsi_scalping_bot import run_once   # <-- point to your real bot file

if __name__ == "__main__":
    while True:
        try:
            run_once()
            print("✅ Cycle complete. Sleeping 20s...\n")
            time.sleep(20)
        except Exception as e:
            print(f"❌ Error in main loop: {e}")
            time.sleep(10)
