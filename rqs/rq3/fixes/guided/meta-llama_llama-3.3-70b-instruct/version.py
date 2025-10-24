import platform
import re
import sys

def versiontuple(v):
    return tuple(map(int, (v.split("."))))

def kernel_version():
    if platform.system() == 'Windows':
        return versiontuple(platform.release())
    else:
        return tuple(map(int, re.match(r"(\d+)\.(\d+)", platform.release()).groups()))