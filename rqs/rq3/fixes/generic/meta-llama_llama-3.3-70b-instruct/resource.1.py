import os
import sys
import traceback
import psutil
import importlib


def show_layer_info(layer_name, layer_out):
    print('[layer]: %s\t[shape]: %s \n%s' % (layer_name,str(layer_out.get_shape().as_list()), show_memory_use()))


def show_memory_use():
    process = psutil.Process()
    total_memory = process.memory_info().rss / (1024.0 ** 2)
    strinfo = "\x1b[33m [Memory] Total Memory Use: %.4f MB \x1b[0m" % total_memory
    return strinfo


def import_class(import_str):
    mod_str, _sep, class_str = import_str.rpartition('.')
    module = importlib.import_module(mod_str)
    try:
        return getattr(module, class_str)
    except AttributeError:
        raise ImportError('Class %s cannot be found (%s)' %
                (class_str,
                    traceback.format_exception(*sys.exc_info())))


def import_object(import_str, *args, **kwargs):
    return import_class(import_str)(*args, **kwargs)


def import_module(import_str):
    return importlib.import_module(import_str)