import os
import requests

def send_telegram_message():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    user_id = os.getenv("TELEGRAM_USER_ID")
    message = "🚀 HyperBot está en línea, mi comandante!"

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": user_id,
        "text": message
    }

    res = requests.post(url, data=payload)
    print(res.json())

if __name__ == "__main__":
    send_telegram_message()
