from UnityPy.export.AudioClipConverter import import_pyfmodex

try:
    import_pyfmodex()
except OSError:
    pass