import sqlite3
import os
from pathlib import Path
import tempfile
import stat
import shutil
from contextlib import contextmanager


class DatabaseManager:
    def __init__(self, db_name="app.db"):
        self.db_name = db_name
        self.db_path = self._get_db_path()
        
    def _get_db_path(self):
        if os.name == 'nt':
            app_data = os.environ.get('APPDATA')
            if app_data:
                base_dir = Path(app_data) / "MyApp"
            else:
                base_dir = Path.home() / "AppData" / "Roaming" / "MyApp"
        else:
            base_dir = Path.home() / ".local" / "share" / "myapp"
        
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir / self.db_name
    
    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.execute("PRAGMA foreign_keys = ON")
            yield conn
        finally:
            if conn:
                conn.close()
    
    def initialize_schema(self):
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER,
                    expires_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            conn.commit()
    
    def backup_database(self, backup_dir=None):
        if backup_dir is None:
            backup_dir = tempfile.gettempdir()
        
        backup_dir = Path(backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        backup_name = f"{self.db_name}.backup"
        backup_path = backup_dir / backup_name
        
        try:
            shutil.copy2(self.db_path, backup_path)
            
            if os.name != 'nt':
                os.chmod(backup_path, stat.S_IRUSR | stat.S_IWUSR)
            
            return str(backup_path)
            
        except (IOError, OSError) as e:
            raise RuntimeError(f"Backup failed: {e}")
    
    def get_database_info(self):
        info = {
            "path": str(self.db_path),
            "exists": self.db_path.exists(),
            "size": 0,
            "readable": False,
            "writable": False
        }
        
        if info["exists"]:
            try:
                info["size"] = self.db_path.stat().st_size
                info["readable"] = os.access(self.db_path, os.R_OK)
                info["writable"] = os.access(self.db_path, os.W_OK)
            except OSError:
                pass
        
        return info


def migrate_old_database():
    old_paths = []
    
    if os.name == 'nt':
        old_paths = [
            Path.cwd() / "app.db",
            Path.home() / "Documents" / "app.db"
        ]
    else:
        old_paths = [
            Path.cwd() / "app.db",
            Path.home() / "app.db",
            Path("/tmp") / "app.db"
        ]
    
    db_manager = DatabaseManager()
    
    for old_path in old_paths:
        if old_path.exists() and not db_manager.db_path.exists():
            try:
                shutil.move(str(old_path), str(db_manager.db_path))
                print(f"Migrated database from {old_path} to {db_manager.db_path}")
                break
            except (IOError, OSError) as e:
                print(f"Failed to migrate from {old_path}: {e}")
                continue


if __name__ == "__main__":
    migrate_old_database()
    
    db = DatabaseManager()
    db.initialize_schema()
    
    with db.get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO users (username, email) VALUES (?, ?)", 
                    ("admin", "admin@example.com"))
        conn.commit()
        
        cursor = conn.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        print(f"Total users: {count}")
    
    backup_path = db.backup_database()
    print(f"Database backed up to: {backup_path}")
    
    info = db.get_database_info()
    print(f"Database info: {info}")