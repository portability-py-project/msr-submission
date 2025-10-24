import sys
import re

def versiontuple(v):
    return tuple(map(int, (v.split("."))))

def kernel_version():
    return tuple(map(int, re.match(r"(\d+)\.(\d+)", sys.platform + ' ' + sys.version).groups()))