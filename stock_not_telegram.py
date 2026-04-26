import requests

BOT_TOKEN = "PASTE_YOUR_TOKEN"
CHAT_ID = "PASTE_YOUR_CHAT_ID"

def send_msg(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    response = requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg
    })
    print(response.json())

send_msg("Test message from Python 🚀")