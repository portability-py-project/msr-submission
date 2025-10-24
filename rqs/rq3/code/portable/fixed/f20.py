import os
import sys
import shutil
import zipfile
import tarfile
import tempfile
import hashlib
import mimetypes
from pathlib import Path
import platform
import subprocess
from typing import List, Optional, Dict


class FileSystemUtils:
    def __init__(self):
        self.temp_dir = self._get_temp_directory()
        self.cache_dir = self._get_cache_directory()
        
    def _get_temp_directory(self):
        if os.name == 'nt':
            temp_base = os.environ.get('TEMP', tempfile.gettempdir())
        else:
            temp_base = os.environ.get('TMPDIR', '/tmp')
            if not os.path.exists(temp_base):
                temp_base = tempfile.gettempdir()
        
        app_temp = Path(temp_base) / "file_processor"
        app_temp.mkdir(exist_ok=True)
        return app_temp
    
    def _get_cache_directory(self):
        if os.name == 'nt':
            cache_base = os.environ.get('LOCALAPPDATA')
            if not cache_base:
                cache_base = Path.home() / "AppData" / "Local"
        else:
            cache_base = os.environ.get('XDG_CACHE_HOME')
            if not cache_base:
                cache_base = Path.home() / ".cache"
        
        app_cache = Path(cache_base) / "file_processor"
        app_cache.mkdir(parents=True, exist_ok=True)
        return app_cache
    
    def get_file_info(self, file_path: Path) -> Dict:
        try:
            stat = file_path.stat()
            
            info = {
                "path": str(file_path),
                "name": file_path.name,
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "is_file": file_path.is_file(),
                "is_dir": file_path.is_dir(),
                "executable": os.access(file_path, os.X_OK),
                "readable": os.access(file_path, os.R_OK),
                "writable": os.access(file_path, os.W_OK)
            }
            
            if file_path.is_file():
                mime_type, _ = mimetypes.guess_type(str(file_path))
                info["mime_type"] = mime_type
                info["extension"] = file_path.suffix
            
            return info
            
        except OSError as e:
            return {"error": str(e), "path": str(file_path)}
    
    def compute_file_hash(self, file_path: Path, algorithm='sha256') -> Optional[str]:
        try:
            hash_func = hashlib.new(algorithm)
            
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    hash_func.update(chunk)
            
            return hash_func.hexdigest()
            
        except Exception as e:
            print(f"Error computing hash for {file_path}: {e}")
            return None
    
    def create_archive(self, source_path: Path, archive_path: Path, 
                      compression: str = 'auto') -> bool:
        try:
            if compression == 'auto':
                if archive_path.suffix.lower() == '.zip':
                    compression = 'zip'
                elif archive_path.suffix.lower() in ['.tar', '.tgz', '.tar.gz']:
                    compression = 'tar'
                else:
                    compression = 'zip'
            
            if compression == 'zip':
                with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    if source_path.is_file():
                        zf.write(source_path, source_path.name)
                    else:
                        for file_path in source_path.rglob('*'):
                            if file_path.is_file():
                                relative_path = file_path.relative_to(source_path)
                                zf.write(file_path, relative_path)
            
            elif compression == 'tar':
                mode = 'w:gz' if archive_path.suffix in ['.tgz', '.tar.gz'] else 'w'
                with tarfile.open(archive_path, mode) as tf:
                    tf.add(source_path, arcname=source_path.name)
            
            return True
            
        except Exception as e:
            print(f"Error creating archive: {e}")
            return False
    
    def extract_archive(self, archive_path: Path, 
                       extract_to: Optional[Path] = None) -> Optional[Path]:
        if extract_to is None:
            extract_to = self.temp_dir / f"extract_{archive_path.stem}"
        
        extract_to.mkdir(parents=True, exist_ok=True)
        
        try:
            if archive_path.suffix.lower() == '.zip':
                with zipfile.ZipFile(archive_path, 'r') as zf:
                    # Security check for path traversal
                    for member in zf.namelist():
                        if os.path.isabs(member) or ".." in member:
                            raise ValueError(f"Unsafe path in archive: {member}")
                    zf.extractall(extract_to)
            
            elif archive_path.suffix.lower() in ['.tar', '.tgz', '.tar.gz']:
                with tarfile.open(archive_path, 'r:*') as tf:
                    # Security check for path traversal
                    for member in tf.getmembers():
                        if os.path.isabs(member.name) or ".." in member.name:
                            raise ValueError(f"Unsafe path in archive: {member.name}")
                    tf.extractall(extract_to)
            
            return extract_to
            
        except Exception as e:
            print(f"Error extracting archive: {e}")
            return None
    
    def find_executable(self, program: str) -> Optional[str]:
        """Cross-platform executable finder"""
        if os.name == 'nt':
            if not program.endswith('.exe'):
                program += '.exe'
        
        # Check if it's already a full path
        if os.path.isfile(program) and os.access(program, os.X_OK):
            return program
        
        # Search in PATH
        for path in os.environ.get('PATH', '').split(os.pathsep):
            full_path = os.path.join(path, program)
            if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                return full_path
        
        return None
    
    def safe_copy(self, src: Path, dst: Path, preserve_metadata: bool = True) -> bool:
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            if preserve_metadata:
                shutil.copy2(src, dst)
            else:
                shutil.copy(src, dst)
            
            return True
            
        except Exception as e:
            print(f"Error copying {src} to {dst}: {e}")
            return False
    
    def get_disk_usage(self, path: Path) -> Dict:
        try:
            if os.name == 'nt':
                import ctypes
                free_bytes = ctypes.c_ulonglong(0)
                total_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                    ctypes.c_wchar_p(str(path)),
                    ctypes.pointer(free_bytes),
                    ctypes.pointer(total_bytes),
                    None
                )
                
                return {
                    "total": total_bytes.value,
                    "free": free_bytes.value,
                    "used": total_bytes.value - free_bytes.value
                }
            else:
                stat = shutil.disk_usage(path)
                return {
                    "total": stat.total,
                    "free": stat.free,
                    "used": stat.used
                }
                
        except Exception as e:
            print(f"Error getting disk usage: {e}")
            return {"error": str(e)}


def get_system_info():
    info = {
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
        "encoding": sys.getdefaultencoding(),
        "file_encoding": sys.getfilesystemencoding()
    }
    
    if os.name == 'nt':
        info["windows_version"] = platform.win32_ver()
    else:
        try:
            info["uname"] = platform.uname()
        except AttributeError:
            pass
    
    return info


def run_cross_platform_command(command: List[str], cwd: Optional[Path] = None) -> Dict:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
        
    except subprocess.TimeoutExpired:
        return {"error": "Command timed out", "success": False}
    except Exception as e:
        return {"error": str(e), "success": False}


if __name__ == "__main__":
    fs_utils = FileSystemUtils()
    
    print("System Information:")
    sys_info = get_system_info()
    for key, value in sys_info.items():
        print(f"  {key}: {value}")
    
    print(f"\nTemp directory: {fs_utils.temp_dir}")
    print(f"Cache directory: {fs_utils.cache_dir}")
    
    # Test file operations
    test_file = fs_utils.temp_dir / "test.txt"
    test_file.write_text("Hello, cross-platform world!")
    
    file_info = fs_utils.get_file_info(test_file)
    print(f"\nTest file info: {file_info}")
    
    file_hash = fs_utils.compute_file_hash(test_file)
    print(f"File hash: {file_hash}")
    
    # Test archive creation
    archive_path = fs_utils.temp_dir / "test_archive.zip"
    if fs_utils.create_archive(test_file, archive_path):
        print(f"Archive created: {archive_path}")
        
        # Test extraction
        extract_path = fs_utils.extract_archive(archive_path)
        if extract_path:
            print(f"Archive extracted to: {extract_path}")
    
    # Test disk usage
    disk_usage = fs_utils.get_disk_usage(Path.cwd())
    print(f"\nDisk usage: {disk_usage}")
    
    # Test executable finding
    python_exe = fs_utils.find_executable("python")
    print(f"Python executable: {python_exe}")
    
    # Cleanup
    if test_file.exists():
        test_file.unlink()
    if archive_path.exists():
        archive_path.unlink()