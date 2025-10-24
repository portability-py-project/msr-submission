import os
import re
import platform

def versiontuple(v):
    return tuple(map(int, (v.split("."))))

def kernel_version():
    if os.name == 'nt':
        ver = platform.version()
    else:
        ver = platform.release()
    return tuple(map(int, re.match(r"(\d+)\.(\d+)", ver).groups()))