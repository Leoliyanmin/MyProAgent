import requests
import json

response = requests.post('http://localhost:8001/auth/verification/send', json={'email': 'test@mail.sustech.edu.cn', 'purpose': 'register'})
print(f'Status: {response.status_code}')
print(f'Response: {response.text}')
data = response.json()
print(f'test_code: {data.get("test_code", "Not found")}')