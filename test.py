import requests
import json
import time

# Your WhatsApp Cloud API credentials
ACCESS_TOKEN = '12c6fbb9978aacfd5ad967537e269f1e'
PHONE_NUMBER_ID = 'YOUR_PHONE_NUMBER_ID'
API_URL = f'https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages'

# Headers for the request
HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

# List of recipients and their messages
clients = [
    {"name": "John", "phone": "9199XXXXXX01", "message": "Hi John! Your order has been shipped."},
    {"name": "Aisha", "phone": "9199XXXXXX02", "message": "Hi Aisha! Your subscription is expiring soon."},
    {"name": "Ravi", "phone": "9199XXXXXX03", "message": "Hey Ravi, don't miss our new offers!"}
]

def send_whatsapp_message(to_phone: str, message: str):
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {
            "body": message
        }
    }

    response = requests.post(API_URL, headers=HEADERS, json=payload)

    if response.status_code == 200:
        print(f"✅ Message sent to {to_phone}")
    else:
        print(f"❌ Failed to send message to {to_phone}: {response.text}")

# Send messages to all clients
for client in clients:
    send_whatsapp_message(client["phone"], client["message"])
    time.sleep(1)  # Optional: delay to avoid rate limiting
