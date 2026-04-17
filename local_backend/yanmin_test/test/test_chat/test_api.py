import requests
import json

response = requests.post(
    "http://localhost:8002/agent/nanobot/chat",
    params={"message": "你好"}
)

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

with open("response.json", "w", encoding="utf-8") as f:
    f.write(response.text)

print("\nSaved to response.json")
