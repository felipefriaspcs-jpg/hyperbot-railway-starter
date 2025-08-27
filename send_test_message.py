import requests

def send_telegram_message():
    # 🚨 Hardcoded for testing only — delete after confirming it's working
    token = "8282101491:AAGgnEF-ML2Jv0dnBF76No1kzCyIdo6A9vU"
    user_id = "1404344692"
    message = "🚀 HyperBot está en línea, mi comandante!"

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": @Flip42022,
        "text": message
    }

    res = requests.post(url, data=payload)
    print(res.json())

if __name__ == "__main__":
    send_telegram_message()

