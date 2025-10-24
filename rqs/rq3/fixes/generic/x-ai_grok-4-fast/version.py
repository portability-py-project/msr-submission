import os
import re
import platform

def versiontuple(v):
    return tuple(map(int, (v.split("."))))

def kernel_version():
    return tuple(map(int, re.match(r"(\d+)\.(\d+)", platform.uname().release).groups()))