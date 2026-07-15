import requests
import random
import os

def generate_avatar(prompt="", size=512):
    if not prompt:
        prompt = "beautiful avatar"

    url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?width=1024&height=1024&seed={random.randint(1, 999999)}&nologo=true"
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            filename = f"avatars/ai_{random.randint(1000, 9999)}.png"
            with open(filename, 'wb') as f:
                f.write(response.content)
            return filename
        return None
    except Exception as e:
        print(f"Ошибка: {e}")
        return None