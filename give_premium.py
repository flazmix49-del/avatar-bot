import sqlite3

user_id = input("Введи свой ID из Telegram: ")

try:
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    
    if user:
        cursor.execute('UPDATE users SET premium = 1 WHERE user_id = ?', (user_id,))
        conn.commit()
        print(f"✅ Пользователь {user_id} теперь ПРЕМИУМ!")
    else:
        cursor.execute('INSERT INTO users (user_id, premium) VALUES (?, 1)', (user_id,))
        conn.commit()
        print(f"✅ Пользователь {user_id} создан и получил ПРЕМИУМ!")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Ошибка: {e}")