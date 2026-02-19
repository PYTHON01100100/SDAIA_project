import requests
import os
from dotenv import load_dotenv

load_dotenv()

url = "https://openrouter.ai/api/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
    "Content-Type": "application/json"
}

data = {
    "model": os.getenv("MODEL_NAME", "openrouter/openai/gpt-4o-mini"),
    "messages": [{"role": "user", "content": "Hi"}]
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
