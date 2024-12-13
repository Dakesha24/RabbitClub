import sqlite3
from datetime import datetime
import os

class ChatDatabase:
    def __init__(self, db_path='chat_history.db'):
        self.db_path = db_path
        self.init_db()
        
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS messages
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      role TEXT NOT NULL,
                      content TEXT NOT NULL,
                      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()
        conn.close()
    
    def save_message(self, role, content):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('INSERT INTO messages (role, content) VALUES (?, ?)',
                  (role, content))
        conn.commit()
        
        # Check database size
        c.execute("SELECT COUNT(*) FROM messages")
        count = c.fetchone()[0]
        
        # If more than 100 messages, keep only the latest 50
        if count > 100:
            c.execute("""DELETE FROM messages 
                        WHERE id NOT IN (
                            SELECT id FROM messages 
                            ORDER BY timestamp DESC 
                            LIMIT 50
                        )""")
            conn.commit()
            
        conn.close()
    
    def get_chat_history(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''SELECT role, content, timestamp 
                     FROM messages 
                     ORDER BY timestamp''')
        messages = c.fetchall()
        conn.close()
        return messages
    
    def clear_chat_history(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('DELETE FROM messages')
        conn.commit()
        conn.close()
    
    def get_db_size(self):
        try:
            return os.path.getsize(self.db_path)
        except:
            return 0