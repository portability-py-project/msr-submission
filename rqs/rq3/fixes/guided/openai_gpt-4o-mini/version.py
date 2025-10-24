import os
import re
import platform

def versiontuple(v):
    return tuple(map(int, (v.split("."))))

def kernel_version():
    if os.name == 'nt':
        return tuple(map(int, platform.version().split(".")[:2]))
    else:
        return tuple(map(int, re.match(r"(\d+)\.(\d+)", os.uname().release).groups()))