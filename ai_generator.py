import requests
import random
import os
import time
from config import POLLINATIONS_API_KEY

BASE_URL = "https://gen.pollinations.ai"

# ========== АВАТАРКА ==========
def generate_avatar(prompt="", size=512):
    if not prompt:
        prompt = "beautiful avatar"

    url = f"{BASE_URL}/image/{prompt.replace(' ', '%20')}?width={size}&height={size}&model=flux&key={POLLINATIONS_API_KEY}"
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            os.makedirs('avatars', exist_ok=True)
            filename = f"avatars/ai_{random.randint(1000, 9999)}.png"
            with open(filename, 'wb') as f:
                f.write(response.content)
            return filename
        return None
    except Exception as e:
        print(f"Ошибка аватарки: {e}")
        return None

# ========== ВИДЕО ==========
def generate_video(prompt=""):
    if not prompt:
        prompt = "beautiful landscape"
    
    url = f"{BASE_URL}/video/{prompt.replace(' ', '%20')}?model=veo&duration=5&key={POLLINATIONS_API_KEY}"
    
    try:
        print(f"🎬 Генерирую видео по запросу: {prompt}")
        response = requests.get(url, timeout=120)
        
        if response.status_code == 200 and len(response.content) > 1000:
            os.makedirs('videos', exist_ok=True)
            filename = f"videos/video_{random.randint(1000, 9999)}.mp4"
            with open(filename, 'wb') as f:
                f.write(response.content)
            return filename
        return None
    except Exception as e:
        print(f"Ошибка видео: {e}")
        return None

# ========== ФАКТ ДНЯ ==========
def get_fact():
    facts = [
        "🧠 У осьминога 3 сердца и 9 мозгов!",
        "🐪 У верблюдов 3 века, чтобы защищать глаза от песка!",
        "🦒 Жирафы спят всего 30 минут в день!",
        "🐧 Пингвины предлагают камешки своим избранницам как кольца!",
        "🦈 Акулы существуют дольше, чем деревья!",
        "🐘 Слоны — единственные млекопитающие, которые не умеют прыгать!",
        "🦋 Бабочки пробуют еду ногами!",
        "🐙 У осьминогов прямоугольные зрачки!",
        "🦉 Совы не могут вращать глазами, они крутят головой на 270 градусов!",
        "🐱 Коты не чувствуют сладкий вкус!",
        "🦷 У улиток около 25 000 зубов!",
        "🐋 Самое громкое животное — синий кит (188 дБ)!",
        "🐝 Пчёлы танцуют, чтобы рассказать другим где еда!"
    ]
    return random.choice(facts)