'''Restricted importer.

Only pull modules from a particular location on disk.
'''

from collections import defaultdict

import imp
import os


# a separate cache of modules keyed by path
_module_cache = defaultdict(dict)

def rimport(name, globals=None, locals=None, fromlist=(),
            level=-1, path=''):
  # check if the module is already loaded
  try:
    module = _module_cache[path][name]
    if module is None: # cached import miss
      raise ImportError(name)
  except KeyError:
    # we do the importing by hand here to make sure it is done securely.
    # the regular import tries to load from anywhere in sys.path
    for suffix, mode, imp_type in imp.get_suffixes():
      # FIXME(msolomon) how does this work with zipimport?p
      src_path = os.path.join(path, *name.split('.')) + suffix
      if not os.path.isfile(src_path):
        continue

      with open(src_path, mode) as f:
        module = imp.load_module(name, f, src_path, (suffix, mode, imp_type))
        _module_cache[path][name] = module
        break
    else:
      raise ImportError(name, 'module not found in path', path)
  if len(fromlist) > 1:
    raise ImportError(name, 'module has odd fromlist', fromlist)
  elif len(fromlist) == 1:
    return getattr(module, fromlist[0])
  else:
    return module  

# # FIXME(msolomon) handle package imports
# def _pkg_import():
#     search_path = path
#     for mname in name.split('.'):
#       f, src_path, description = imp.find_module(mname, search_path)
#       module_data = imp.find_module(mname, search_path)
#       if module:
#       with f:
#         module = imp.load_module(mname, f, src_path, description)
#         _module_cache[path][mname] = module
#         if description[-1] == imp.PKG_DIRECTORY:
#           search_path = module.__path__
    
