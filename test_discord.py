import requests
from dotenv import load_dotenv
import os

load_dotenv()

webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

if not webhook_url:
    print("ERROR: DISCORD_WEBHOOK_URL not found in .env file")
    exit(1)

print(f"Testing webhook: {webhook_url[:50]}...")

test_message = {
    "embeds": [{
        "title": "Test Alert - Discord Webhook Working!",
        "description": "Your Polymarket monitor Discord integration is configured correctly.",
        "color": 5763719,
        "fields": [
            {"name": "Status", "value": "Connection Successful", "inline": True}
        ]
    }]
}

try:
    response = requests.post(webhook_url, json=test_message, timeout=10)
    response.raise_for_status()
    print("SUCCESS: Test message sent to Discord!")
    print(f"Response status: {response.status_code}")
except Exception as e:
    print(f"FAILED: {e}")
