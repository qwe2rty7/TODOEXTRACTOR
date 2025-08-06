import sqlite3
import os
import json
from datetime import datetime

class DatabaseSync:
    def __init__(self, db_path=None):
        if db_path:
            self.db_path = db_path
        else:
            self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'todos.db')
        
        self.init_database()
    
    def init_database(self):
        """Create tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                source TEXT NOT NULL,
                action TEXT NOT NULL,
                priority TEXT DEFAULT 'Medium',
                deadline TEXT,
                status TEXT DEFAULT 'Pending',
                completed_at TIMESTAMP,
                metadata TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_todos(self, todos, source):
        """Add todos to database"""
        if not todos:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for todo in todos:
            if isinstance(todo, dict):
                cursor.execute('''
                    INSERT INTO todos (source, action, priority, deadline, metadata)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    source,
                    todo.get('action', ''),
                    todo.get('priority', 'Medium'),
                    todo.get('deadline', ''),
                    json.dumps(todo)
                ))
            else:
                cursor.execute('''
                    INSERT INTO todos (source, action)
                    VALUES (?, ?)
                ''', (source, todo))
        
        conn.commit()
        conn.close()
        print(f"✅ Saved {len(todos)} todos to database")
    
    def get_pending_todos(self):
        """Get all pending todos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, created_at, source, action, priority, deadline
            FROM todos
            WHERE status = 'Pending'
            ORDER BY created_at DESC
        ''')
        
        todos = cursor.fetchall()
        conn.close()
        return todos
    
    def mark_completed(self, todo_id):
        """Mark a todo as completed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE todos
            SET status = 'Completed', completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (todo_id,))
        
        conn.commit()
        conn.close()