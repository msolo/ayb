import cStringIO
import glob
import new
import os
import pkgutil
import subprocess

from metamake import error
from metamake import defs


# When exec is run, it pollutes the namespace. However, you still want
# certain keys to resolve from the base namespace.
class HierarchicalDict(dict):
  def __init__(self, base_dict):
    self._base_dict = base_dict

  def __missing__(self, k):
    return self._base_dict[k]

class Makefile(object):
  def __init__(self, maker, makefile_path):
    self.maker = maker
    self.makefile_path = os.path.abspath(makefile_path)

    self._includes = set()
    self.target_map = {}
    # namespaces as makefiles are evaluated
    self.pym_globals = {
      'build_def': self.build_def,
      'include': self.include,
      'glob': self.glob,
      }
    # This seems needlessly complex, but this makes all import / include
    # mechanisms go through the same flow.
    for name in defs.default_defs:
      filename = name + '.pym'
      data = pkgutil.get_data('metamake.defs', filename)
      path = os.path.join(os.path.dirname(defs.__file__), filename) 
      self._include_data(data, path)
          
  def add_target(self, target):
    if target.name in self.target_map:
      raise error.MakeError('duplicate target %s in %s' % (target.name, self.makefile_path))
    self.target_map[target.name] = target

  def get_target(self, name):
    try:
      return self.target_map[name]
    except KeyError:
      raise error.MakeError('no target %s in %s' % (name, self.makefile_path),
                            self.target_map.keys())
    
  def resolve_src_path(self, name):
    if name.startswith('//'):
      return os.path.join(self.maker.src_root, name[2:])
    if name.startswith('/'):
      raise error.MakeError('absolute paths not allowed', name)
    return os.path.join(os.path.dirname(self.makefile_path), name)

  def resolve_out_path(self, name):
    if name.startswith('/'):
      raise error.MakeError('absolute paths not allowed', name)
    relpath = os.path.relpath(os.path.dirname(self.makefile_path),
                              self.maker.src_root)
    return os.path.abspath(os.path.join(self.maker.out_root, relpath, name))

  # use '**' as the indicator to recurse
  def glob(self, pathname):
    pathname = self.resolve_src_path(pathname)
    if '**' in pathname:
      paths = []
      root, pathname = pathname.split('**/')
      gpath = os.path.join(root, pathname)
      paths.extend(glob.glob(gpath))
      for root, dirs, files in os.walk(root):
        for i, dir in enumerate(dirs[:]):
          if dir.startswith('.'):
            del dirs[i]
            continue
          gpath = os.path.join(root, dir, pathname)
          paths.extend(glob.glob(gpath))
    else:
      paths = glob.glob(pathname)

    paths = [os.path.relpath(x, os.path.dirname(self.makefile_path))
             for x in paths]
    paths.sort()
    return paths

  def include(self, name):
    path = self.resolve_src_path(name)
    if path in self._includes:
      return
    vprint('include %s %s', name, path)
    with open(path) as f:
      data = f.read()
    self._include_data(data, path)

  def _include_data(self, data, path):
    if path in self._includes:
      return
    vprint('_include_data %s', path)
    include_globals = self.pym_globals.copy()
    run_code = compile(data, path, 'exec')
    exec run_code in include_globals
    self._includes.add(path)
    
  def build_def(self, method):
    vprint('build_def %s', method.__name__)
    m = new.instancemethod(method, self, self.__class__)
    self.pym_globals[method.__name__] = m
    return m

  def read(self):
    try:
      with open(self.makefile_path) as f:
        exec f in HierarchicalDict(self.pym_globals)
    except IOError as e:
      raise IOError(str(e), self.makefile_path)

