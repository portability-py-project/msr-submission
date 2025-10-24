import signal

# Check for the presence of SIGHUP and SIGKILL signals
if hasattr(signal, 'SIGHUP'):
    SIGHUP = signal.SIGHUP
else:
    SIGHUP = None

if hasattr(signal, 'SIGKILL'):
    SIGKILL = signal.SIGKILL
else:
    SIGKILL = None