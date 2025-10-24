import os
import subprocess
import sys
from pathlib import Path


def get_system_shell():
    """Get the appropriate shell command for the current platform"""
    if os.name == 'nt':
        return ['cmd', '/c']
    else:
        shell = os.environ.get('SHELL', '/bin/sh')
        return [shell, '-c']


def run_command(command):
    """Execute a command using the platform-appropriate shell"""
    shell_cmd = get_system_shell()
    
    try:
        result = subprocess.run(
            shell_cmd + [command],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def get_current_user():
    """Get current username in a cross-platform way"""
    username = run_command('whoami' if os.name != 'nt' else 'echo %USERNAME%')
    
    if not username:
        username = os.environ.get('USER') or os.environ.get('USERNAME')
    
    return username or 'unknown'


def get_home_directory():
    """Get user home directory with fallback mechanisms"""
    home = Path.home()
    
    if not home.exists():
        home_env = os.environ.get('HOME') or os.environ.get('USERPROFILE')
        if home_env:
            home = Path(home_env)
    
    return home


if __name__ == "__main__":
    print(f"Current user: {get_current_user()}")
    print(f"Home directory: {get_home_directory()}")
    print(f"Shell: {' '.join(get_system_shell())}")