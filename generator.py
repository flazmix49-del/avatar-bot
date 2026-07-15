from PIL import Image, ImageDraw, ImageFont
import random
import os

def generate_avatar(name="", size=512, style="random"):
    """Генерирует красивую аватарку"""
    
    styles = ['cosmic', 'sunset', 'ocean', 'neon', 'nature', 'minimal', 'gradient', 'galaxy']
    if style == "random" or style not in styles:
        style = random.choice(styles)
    
    img = Image.new('RGB', (size, size))
    draw = ImageDraw.Draw(img)
    
    if style == 'cosmic':
        draw_cosmic(draw, size)
    elif style == 'sunset':
        draw_sunset(draw, size)
    elif style == 'ocean':
        draw_ocean(draw, size)
    elif style == 'neon':
        draw_neon(draw, size)
    elif style == 'nature':
        draw_nature(draw, size)
    elif style == 'minimal':
        draw_minimal(draw, size)
    elif style == 'gradient':
        draw_gradient(draw, size)
    elif style == 'galaxy':
        draw_galaxy(draw, size)
    
    if name and name.strip():
        add_text(draw, name, size)
    
    return img

def draw_cosmic(draw, size):
    for i in range(size):
        draw.line([(0, i), (size, i)], fill=(20, 10, 40 + 30 * i // size))
    for _ in range(120):
        x, y = random.randint(0, size), random.randint(0, size)
        r = random.randint(1, 3)
        draw.ellipse([x-r, y-r, x+r, y+r], fill=(255, 255, 255))

def draw_sunset(draw, size):
    for i in range(size):
        r = 255
        g = 150 - 100 * i // size
        b = 50 + 150 * i // size
        draw.line([(0, i), (size, i)], fill=(r, max(0, g), b))
    for r in range(size//5, 0, -5):
        draw.ellipse([size//2-r, size//3-r, size//2+r, size//3+r], fill=(255, 200, 50))

def draw_ocean(draw, size):
    for i in range(size):
        draw.line([(0, i), (size, i)], fill=(20 + 50*i//size, 80 + 100*i//size, 150 + 80*i//size))
    for w in range(3):
        y = size//3 + w * size//5
        for x in range(0, size, 3):
            draw.point((x, y + int(15 * ((x * 0.02 + w * 2) % 6.28))), fill=(255, 255, 255))

def draw_neon(draw, size):
    draw.rectangle([0, 0, size, size], fill=(5, 5, 20))
    colors = [(255,0,255), (0,255,255), (255,255,0), (0,255,0), (255,0,0), (0,0,255)]
    for _ in range(6):
        color = random.choice(colors)
        x1, y1 = random.randint(0, size), random.randint(0, size)
        x2, y2 = random.randint(0, size), random.randint(0, size)
        draw.line([x1, y1, x2, y2], fill=color, width=random.randint(2, 6))

def draw_nature(draw, size):
    for i in range(size//2):
        draw.line([(0, i), (size, i)], fill=(135, 206, 235))
    for i in range(size//2, size):
        draw.line([(0, i), (size, i)], fill=(34, 139 - 50*(i-size//2)//size, 34))
    for _ in range(5):
        x = random.randint(20, size-20)
        h = random.randint(40, 120)
        draw.rectangle([x-3, size-h, x+3, size], fill=(101, 67, 33))
        r = random.randint(20, 45)
        draw.ellipse([x-r, size-h-r, x+r, size-h+r], fill=(34, 139, 34))

def draw_minimal(draw, size):
    bg = (random.randint(230, 255), random.randint(230, 255), random.randint(230, 255))
    draw.rectangle([0, 0, size, size], fill=bg)
    for _ in range(4):
        x, y = random.randint(0, size), random.randint(0, size)
        w, h = random.randint(50, 150), random.randint(50, 150)
        color = (random.randint(100, 200), random.randint(100, 200), random.randint(100, 200))
        if random.choice([True, False]):
            draw.rectangle([x, y, x+w, y+h], fill=color)
        else:
            draw.ellipse([x, y, x+w, y+h], fill=color)

def draw_gradient(draw, size):
    colors = [(255, 100, 150), (200, 50, 200), (100, 50, 200), (50, 200, 255), (100, 255, 200), (255, 200, 50)]
    c1 = random.choice(colors)
    c2 = random.choice(colors)
    for i in range(size):
        r = c1[0] + (c2[0] - c1[0]) * i // size
        g = c1[1] + (c2[1] - c1[1]) * i // size
        b = c1[2] + (c2[2] - c1[2]) * i // size
        draw.line([(0, i), (size, i)], fill=(r, g, b))

def draw_galaxy(draw, size):
    for i in range(size):
        draw.line([(0, i), (size, i)], fill=(10 + 20*i//size, 5 + 30*i//size, 30 + 80*i//size))
    for _ in range(50):
        x = size//2 + int(random.gauss(0, size//3))
        y = size//2 + int(random.gauss(0, size//3))
        r = random.randint(2, 8)
        draw.ellipse([x-r, y-r, x+r, y+r], fill=(random.randint(150,255), random.randint(100,200), random.randint(200,255)))
    for _ in range(80):
        x, y = random.randint(0, size), random.randint(0, size)
        r = random.randint(1, 3)
        draw.ellipse([x-r, y-r, x+r, y+r], fill=(255, 255, 255))

def add_text(draw, name, size):
    try:
        font = ImageFont.truetype("arial.ttf", size//5)
    except:
        font = ImageFont.load_default()
    
    if len(name) > 12:
        name = name[:12] + "."
    
    draw.text((size//2 - len(name)*size//10, size//2 - size//10), 
             name.upper(), fill=(255, 255, 255), font=font)

def save_avatar(img, user_id):
    os.makedirs('avatars', exist_ok=True)
    filename = f"avatars/{user_id}_{random.randint(1000, 9999)}.png"
    img.save(filename)
    return filename