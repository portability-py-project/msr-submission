import os
import sys

if os.name == 'nt':
    pyfmodex_path = os.path.join(os.path.dirname(__file__), 'pyfmodex.dll')
else:
    pyfmodex_path = os.path.join(os.path.dirname(__file__), 'libpyfmodex.so')

if not os.path.exists(pyfmodex_path):
    raise OSError(f"Required module not found: {pyfmodex_path}")

from UnityPy.export.AudioClipConverter import import_pyfmodex

import_pyfmodex()