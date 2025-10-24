import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional


class TaskQueue:
    def __init__(self, db_path="tasks.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the task database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    processed_at TEXT,
                    retry_count INTEGER DEFAULT 0
                )
            """)
            conn.commit()
    
    def add_task(self, task_type: str, payload: Dict) -> int:
        """Add a new task to the queue"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO tasks (task_type, payload) VALUES (?, ?)",
                (task_type, json.dumps(payload))
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_pending_tasks(self, limit: int = 10) -> List[Dict]:
        """Get pending tasks from the queue"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM tasks WHERE status = 'pending' ORDER BY created_at LIMIT ?",
                (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def mark_task_completed(self, task_id: int):
        """Mark a task as completed"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE tasks SET status = 'completed', processed_at = ? WHERE id = ?",
                (datetime.now().isoformat(), task_id)
            )
            conn.commit()
    
    def mark_task_failed(self, task_id: int):
        """Mark a task as failed and increment retry count"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE tasks SET status = 'failed', retry_count = retry_count + 1 WHERE id = ?",
                (task_id,)
            )
            conn.commit()


def process_email_task(payload):
    """Process email sending task"""
    recipient = payload.get('recipient')
    subject = payload.get('subject')
    print(f"Sending email to {recipient} with subject: {subject}")
    return True


if __name__ == "__main__":
    queue = TaskQueue()
    
    task_id = queue.add_task("send_email", {
        "recipient": "user@example.com",
        "subject": "Welcome!",
        "body": "Welcome to our service"
    })
    
    tasks = queue.get_pending_tasks()
    for task in tasks:
        if task['task_type'] == 'send_email':
            payload = json.loads(task['payload'])
            if process_email_task(payload):
                queue.mark_task_completed(task['id'])
            else:
                queue.mark_task_failed(task['id'])