import requests, sys
url = 'http://127.0.0.1:8000/chat'
payload = {"question": "What is my blood sugar level?", "history": None}
response = requests.post(url, json=payload)
# Write raw response to stdout buffer to avoid encoding issues
sys.stdout.buffer.write(response.content)
print('\nStatus:', response.status_code)
