import os
import sys
import importlib.util
from pathlib import Path


def get_config_dir():
    """Get application config directory based on platform"""
    if os.name == 'nt':
        config_base = os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming')
    else:
        config_base = os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')
    
    config_dir = Path(config_base) / 'myapp'
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def load_config_module(config_path):
    """Dynamically load configuration module"""
    if not config_path.exists():
        return None
    
    try:
        spec = importlib.util.spec_from_file_location("config", config_path)
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)
        return config_module
    except Exception:
        return None


def get_default_config():
    """Default configuration with platform-specific paths"""
    return {
        'log_level': 'INFO',
        'max_workers': os.cpu_count() or 4,
        'temp_dir': str(Path(os.environ.get('TMPDIR', '/tmp' if os.name != 'nt' else 'C:\\temp'))),
        'line_ending': '\r\n' if os.name == 'nt' else '\n'
    }


def save_default_config():
    """Create default config file if it doesn't exist"""
    config_dir = get_config_dir()
    config_file = config_dir / 'config.py'
    
    if not config_file.exists():
        default_config = get_default_config()
        config_content = f"""# Auto-generated configuration
LOG_LEVEL = '{default_config['log_level']}'
MAX_WORKERS = {default_config['max_workers']}
TEMP_DIR = r'{default_config['temp_dir']}'
LINE_ENDING = {repr(default_config['line_ending'])}
"""
        config_file.write_text(config_content)
    
    return config_file


if __name__ == "__main__":
    config_file = save_default_config()
    config = load_config_module(config_file)
    
    if config:
        print(f"Config loaded from: {config_file}")
        print(f"Log level: {getattr(config, 'LOG_LEVEL', 'N/A')}")
        print(f"Max workers: {getattr(config, 'MAX_WORKERS', 'N/A')}")
    else:
        print("Using default configuration")