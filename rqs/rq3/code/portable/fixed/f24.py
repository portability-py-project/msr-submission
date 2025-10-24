import os
import stat
import shutil
from pathlib import Path


def set_executable_permissions(file_path):
    """Set executable permissions in a cross-platform way"""
    file_path = Path(file_path)
    
    if os.name == 'nt':
        # On Windows, just ensure the file exists and is readable
        if file_path.suffix.lower() not in ['.exe', '.bat', '.cmd']:
            new_path = file_path.with_suffix(file_path.suffix + '.bat')
            if not new_path.exists():
                shutil.copy2(file_path, new_path)
            return new_path
    else:
        # On Unix-like systems, set proper execute permissions
        current_permissions = file_path.stat().st_mode
        new_permissions = current_permissions | stat.S_IEXEC | stat.S_IXUSR | stat.S_IXGRP
        file_path.chmod(new_permissions)
    
    return file_path


def create_script_wrapper(script_content, script_name):
    """Create a cross-platform script wrapper"""
    if os.name == 'nt':
        script_file = Path(f"{script_name}.bat")
        wrapper_content = f"@echo off\n{script_content}\n"
    else:
        script_file = Path(script_name)
        wrapper_content = f"#!/bin/bash\n{script_content}\n"
    
    script_file.write_text(wrapper_content)
    return set_executable_permissions(script_file)


def is_executable(file_path):
    """Check if file is executable in a cross-platform way"""
    file_path = Path(file_path)
    
    if not file_path.exists():
        return False
    
    if os.name == 'nt':
        return file_path.suffix.lower() in ['.exe', '.bat', '.cmd', '.com']
    else:
        return os.access(file_path, os.X_OK)


def find_executables_in_path(program_name):
    """Find all executable versions of a program in PATH"""
    executables = []
    path_dirs = os.environ.get('PATH', '').split(os.pathsep)
    
    for path_dir in path_dirs:
        if not path_dir:
            continue
        
        path_obj = Path(path_dir)
        if not path_obj.exists():
            continue
        
        if os.name == 'nt':
            extensions = ['.exe', '.bat', '.cmd', '.com']
            for ext in extensions:
                candidate = path_obj / f"{program_name}{ext}"
                if candidate.exists() and is_executable(candidate):
                    executables.append(str(candidate))
        else:
            candidate = path_obj / program_name
            if candidate.exists() and is_executable(candidate):
                executables.append(str(candidate))
    
    return executables


if __name__ == "__main__":
    script_path = create_script_wrapper("echo 'Hello World'", "hello")
    print(f"Created script: {script_path}")
    print(f"Is executable: {is_executable(script_path)}")
    
    python_executables = find_executables_in_path("python")
    print(f"Found Python executables: {python_executables}")
    
    if script_path.exists():
        script_path.unlink()