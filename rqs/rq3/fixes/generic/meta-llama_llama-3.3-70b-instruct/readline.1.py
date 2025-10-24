import os

# ...

def _init_readline():
    try:
        readline.parse_and_bind(r'"\C-?": backward-kill-word') 
        readline.parse_and_bind(r'"\e[3~": delete-char')        
        readline.parse_and_bind('set editing-mode emacs') 
        readline.parse_and_bind('set horizontal-scroll-mode on')
        readline.parse_and_bind('set bell-style none')
        
        history_dir = os.path.dirname(HISTORY_FILE)
        if not os.path.exists(history_dir):
            os.makedirs(history_dir, exist_ok=True)
        
        if not os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                pass
        
        try:
            readline.read_history_file(HISTORY_FILE)
        except:
            pass
        
        readline.set_history_length(1000)
        atexit.register(_save_history)
        
    except Exception as e:
        console.print(f"[warning]Failed to initialize command history: {str(e)}[/warning]")

# ...

if __name__ == "__main__":
    try:
        cli()
    except KeyboardInterrupt:
        stream_print("\n[warning]Operation cancelled[/warning]")
        flush_pending()
    except Exception as e:
        stream_print(f"\n[danger]An error occurred: {str(e)}[/danger]")
        flush_pending()
    finally:
        flush_pending()
        if os.name == 'nt':  # Windows
            os.system('cls')
        else:  # Unix/Linux/MacOS/BSDOS
            os.system('clear')