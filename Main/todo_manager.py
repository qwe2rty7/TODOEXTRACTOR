import os
from datetime import datetime

class TodoManager:
    def __init__(self, todo_file_path=None, notes_file_path=None):
        if todo_file_path:
            self.todo_file = todo_file_path
        else:
            self.todo_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'todos.txt')
        
        if notes_file_path:
            self.notes_file = notes_file_path
        else:
            self.notes_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'notes.txt')
    
    def save_todos_to_file(self, todos, source_info):
        """Append todos to the todos.txt file with source information"""
        if not todos:
            return
        
        try:
            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(self.todo_file), exist_ok=True)
            
            # Read existing todos to avoid duplicates
            existing_todos = set()
            if os.path.exists(self.todo_file):
                with open(self.todo_file, 'r', encoding='utf-8') as f:
                    existing_todos = set(line.strip().lower() for line in f if line.strip())
            
            # Append new todos
            with open(self.todo_file, 'a', encoding='utf-8') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
                
                f.write(f"\n--- {source_info} [{timestamp}] ---\n")
                
                new_count = 0
                for todo in todos:
                    # Simple duplicate check
                    if todo.lower() not in existing_todos:
                        f.write(f"- {todo}\n")
                        existing_todos.add(todo.lower())
                        new_count += 1
                
                f.write("\n")
                
                if new_count > 0:
                    print(f"Saved {new_count} new todo(s) to {self.todo_file}")
                else:
                    print("No new todos to save (duplicates filtered)")
                    
        except Exception as e:
            print(f"ERROR saving todos: {e}")
    
    def save_notes_to_file(self, notes, source_info):
        """Append notes to the notes.txt file with source information"""
        if not notes:
            return
        
        try:
            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(self.notes_file), exist_ok=True)
            
            # Append notes
            with open(self.notes_file, 'a', encoding='utf-8') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
                
                f.write(f"\n--- {source_info} [{timestamp}] ---\n")
                
                for note in notes:
                    f.write(f"• {note}\n")
                
                f.write("\n")
                
                print(f"Saved {len(notes)} note(s) to {self.notes_file}")
                    
        except Exception as e:
            print(f"ERROR saving notes: {e}")