from UnityPy.export.AudioClipConverter import import_pyfmodex
import os

if os.name == 'nt':
    import_pyfmodex()  # Windows
else:
    import_pyfmodex()  # Non-Windows