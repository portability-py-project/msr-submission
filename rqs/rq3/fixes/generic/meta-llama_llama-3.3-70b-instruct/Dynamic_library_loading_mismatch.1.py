import sys
from UnityPy.export.AudioClipConverter import import_pyfmodex

if sys.platform.startswith('win'):
    import_pyfmodex()
elif sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
    try:
        import_pyfmodex()
    except Exception as e:
        print(f"Failed to import pyfmodex: {e}")