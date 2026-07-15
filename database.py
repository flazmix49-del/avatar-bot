import sqlite3
import time
from datetime import date

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            avatar_count INTEGER DEFAULT 0,
            premium INTEGER DEFAULT 0,
            premium_until INTEGER DEFAULT 0,
            last_reset TEXT DEFAULT CURRENT_DATE
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            avatar_path TEXT,
            paid INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT avatar_count, premium, premium_until FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result

def add_user(user_id, username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', (user_id, username))
    conn.commit()
    conn.close()

def update_user_count(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('UPDATE users SET avatar_count = avatar_count + 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def set_premium(user_id, days=15):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    premium_until = int(time.time()) + days * 86400
    c.execute('UPDATE users SET premium = 1, premium_until = ? WHERE user_id = ?', (premium_until, user_id))
    conn.commit()
    conn.close()

def reset_daily(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('UPDATE users SET avatar_count = 0, last_reset = ? WHERE user_id = ?', (date.today().isoformat(), user_id))
    conn.commit()
    conn.close()

def check_premium(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT premium, premium_until FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    if result and result[0] == 1 and result[1] > int(time.time()):
        return True
    return False

def get_premium_days_left(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT premium_until FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    if result:
        return max(0, (result[0] - int(time.time())) // 86400)
    return 0

def save_order(user_id, avatar_path):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('INSERT INTO orders (user_id, avatar_path) VALUES (?, ?)', (user_id, avatar_path))
    conn.commit()
    conn.close()