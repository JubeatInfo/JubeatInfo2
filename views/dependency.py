
from jubeatinfo.lib import NamedDict
"""This module manage view dependency tree and cascading data build."""

table = NamedDict()

def add(key, deps):
    if not key in table.keys():
        table[key] = []

    try:
        len(deps)
        table[key] += deps
    except TypeError:
        table[key].append(deps)

def build(build_func, built_deps=None, **args):
    def merge_args(data):
        argkeys = args.keys()
        for k, v in data.iteritems():
            if not k in argkeys:
                args[k] = v
    
    data = NamedDict()
    def merge_data(mdata):
        for k, v in mdata.iteritems():
            data[k] = v
        
    if built_deps is None:
        built_deps = list()
    
    if build_func in table.keys():
        for func in table[build_func]:
            if not func in built_deps:
                dep_data = build(func, built_deps, **args)
                merge_data(dep_data)
                merge_args(dep_data)

    self_data = build_func(**args)
    merge_data(self_data)
    built_deps.append(build_func)
    
    return data

