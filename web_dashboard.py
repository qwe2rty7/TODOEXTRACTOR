"""
Simple Web Dashboard for Todo Monitoring
Run this locally or deploy to view your todos
"""

from flask import Flask, render_template_string, jsonify
import sqlite3
import json
import os
from datetime import datetime

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Todo Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        h1 { color: #333; }
        .stats { display: flex; gap: 20px; margin: 20px 0; }
        .stat-card { background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stat-number { font-size: 2em; font-weight: bold; color: #4CAF50; }
        table { width: 100%; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        th { background: #4CAF50; color: white; padding: 12px; text-align: left; }
        td { padding: 12px; border-bottom: 1px solid #ddd; }
        tr:hover { background: #f9f9f9; }
        .priority-high { color: #f44336; font-weight: bold; }
        .priority-medium { color: #ff9800; }
        .priority-low { color: #4CAF50; }
        .refresh-btn { background: #4CAF50; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }
        .refresh-btn:hover { background: #45a049; }
    </style>
</head>
<body>
    <h1>📝 Todo Monitor Dashboard</h1>
    
    <div class="stats">
        <div class="stat-card">
            <div>Total Todos</div>
            <div class="stat-number" id="total">-</div>
        </div>
        <div class="stat-card">
            <div>Pending</div>
            <div class="stat-number" id="pending">-</div>
        </div>
        <div class="stat-card">
            <div>Completed Today</div>
            <div class="stat-number" id="completed">-</div>
        </div>
    </div>
    
    <button class="refresh-btn" onclick="loadTodos()">🔄 Refresh</button>
    
    <h2>Recent Todos</h2>
    <table>
        <thead>
            <tr>
                <th>Time</th>
                <th>Source</th>
                <th>Action</th>
                <th>Priority</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody id="todos-table">
            <tr><td colspan="5">Loading...</td></tr>
        </tbody>
    </table>
    
    <script>
        function loadTodos() {
            fetch('/api/todos')
                .then(response => response.json())
                .then(data => {
                    // Update stats
                    document.getElementById('total').textContent = data.stats.total;
                    document.getElementById('pending').textContent = data.stats.pending;
                    document.getElementById('completed').textContent = data.stats.completed_today;
                    
                    // Update table
                    const tbody = document.getElementById('todos-table');
                    tbody.innerHTML = '';
                    
                    data.todos.forEach(todo => {
                        const row = tbody.insertRow();
                        row.innerHTML = `
                            <td>${new Date(todo.created_at).toLocaleString()}</td>
                            <td>${todo.source}</td>
                            <td>${todo.action}</td>
                            <td class="priority-${todo.priority.toLowerCase()}">${todo.priority}</td>
                            <td>${todo.status}</td>
                        `;
                    });
                });
        }
        
        // Load on page load
        loadTodos();
        
        // Auto-refresh every 30 seconds
        setInterval(loadTodos, 30000);
    </script>
</body>
</html>
'''

@app.route('/')
def dashboard():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/todos')
def get_todos():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'todos.db')
    
    if not os.path.exists(db_path):
        # Fallback to reading todos.txt if no database
        todos_txt = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'todos.txt')
        if os.path.exists(todos_txt):
            with open(todos_txt, 'r') as f:
                lines = f.readlines()
                todos = []
                for line in lines:
                    if line.strip() and line.startswith('- '):
                        todos.append({
                            'created_at': datetime.now().isoformat(),
                            'source': 'todos.txt',
                            'action': line[2:].strip(),
                            'priority': 'Medium',
                            'status': 'Pending'
                        })
                return jsonify({
                    'todos': todos[-20:],  # Last 20 todos
                    'stats': {
                        'total': len(todos),
                        'pending': len(todos),
                        'completed_today': 0
                    }
                })
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get recent todos
    cursor.execute('''
        SELECT * FROM todos
        ORDER BY created_at DESC
        LIMIT 50
    ''')
    todos = [dict(row) for row in cursor.fetchall()]
    
    # Get stats
    cursor.execute('SELECT COUNT(*) as total FROM todos')
    total = cursor.fetchone()['total']
    
    cursor.execute('SELECT COUNT(*) as pending FROM todos WHERE status = "Pending"')
    pending = cursor.fetchone()['pending']
    
    cursor.execute('''
        SELECT COUNT(*) as completed FROM todos 
        WHERE status = "Completed" 
        AND DATE(completed_at) = DATE('now')
    ''')
    completed_today = cursor.fetchone()['completed']
    
    conn.close()
    
    return jsonify({
        'todos': todos,
        'stats': {
            'total': total,
            'pending': pending,
            'completed_today': completed_today
        }
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)