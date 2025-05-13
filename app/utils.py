import requests
import os

API_URL = "https://api-inference.huggingface.co/models/j-hartmann/emotion-english-distilroberta-base"
HF_TOKEN = os.getenv("HF_TOKEN")

def detect_emotion(text: str) -> str:
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": text}
    response = requests.post(API_URL, headers=headers, json=payload)
    result = response.json()
    if isinstance(result, list) and result[0]:
        return result[0][0]["label"]
    return "Unknown"
