try:
    from UnityPy.export.AudioClipConverter import import_pyfmodex

    import_pyfmodex()
except OSError as e:
    if e.winerror == 126:
        print("Error: The specified module could not be found.")