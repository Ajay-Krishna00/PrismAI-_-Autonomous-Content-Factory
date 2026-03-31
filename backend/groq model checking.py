import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("GROQ_API_KEY")
url = "https://api.groq.com/openai/v1/models"

if not api_key:
    raise SystemExit("GROQ_API_KEY is missing. Set it in your environment or dotenv file.")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers)

print(f"HTTP {response.status_code}")
print(response.json())