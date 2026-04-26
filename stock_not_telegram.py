import os
import requests

print("BOT_TOKEN exists:", "BOT_TOKEN" in os.environ)
print("CHAT_ID exists:", "CHAT_ID" in os.environ)

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

def send_msg(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    res = requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    print(res.json())

send_msg("Test from GitHub 🚀")
