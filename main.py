import time
from breakout_bot import run_once   # 👈 rename this to match the file where you put the new bot

if __name__ == "__main__":
    while True:
        try:
            run_once()   # run one full signal+trade cycle
            print("✅ Cycle complete. Sleeping 20s...\n")
            time.sleep(20)   # give API some breathing room
        except Exception as e:
            print(f"❌ Error in main loop: {e}")
            time.sleep(10)   # wait a bit longer if it crashes
