import os
import tempfile
import time
from pathlib import Path


class CrossPlatformLock:
    def __init__(self, name):
        self.name = name
        self.lock_file = self._get_lock_path()
        self.acquired = False
    
    def _get_lock_path(self):
        if os.name == 'nt':
            lock_dir = Path(tempfile.gettempdir()) / "locks"
        else:
            lock_dir = Path("/var/lock") if os.path.exists("/var/lock") else Path(tempfile.gettempdir()) / "locks"
        
        lock_dir.mkdir(exist_ok=True)
        return lock_dir / f"{self.name}.lock"
    
    def acquire(self, timeout=5):
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                if not self.lock_file.exists():
                    self.lock_file.write_text(str(os.getpid()))
                    self.acquired = True
                    return True
                
                time.sleep(0.1)
            except OSError:
                time.sleep(0.1)
        
        return False
    
    def release(self):
        if self.acquired and self.lock_file.exists():
            try:
                self.lock_file.unlink()
                self.acquired = False
                return True
            except OSError:
                pass
        return False


if __name__ == "__main__":
    lock = CrossPlatformLock("test_app")
    
    if lock.acquire():
        print("Lock acquired successfully")
        time.sleep(1)
        lock.release()
        print("Lock released")
    else:
        print("Failed to acquire lock")