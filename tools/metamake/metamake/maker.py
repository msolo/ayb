# Read a recipe file and turn it into a model.
#
# Write out a makefile and execute it with make.
#
# "target" ==  //<path>:<name>

import cStringIO
import glob
import new
import os
import pkgutil
import shutil
import subprocess

from metamake import error
from metamake import makefile
from metamake import target


MAKEFILE_SRC = 'BUILD'
MAKEFILE_GEN = 'Makefile.gen'

DEFAULT_OUT_DIR = 'out'
DEFAULT_BUILD_DIR = 'tmp'
DEFAULT_TOOLS_DIR = 'tools'

class Maker(object):
  def __init__(self, src_root, out_root=None, build_root=None, tool_root=None):
    self.src_root = os.path.abspath(src_root)
    if out_root:
      self.out_root = os.path.abspath(out_root)
    else:
      self.out_root = os.path.join(self.src_root, DEFAULT_OUT_DIR)
    if build_root:
      self.build_root = os.path.abspath(build_root)
    else:
      self.build_root = os.path.join(self.src_root, DEFAULT_BUILD_DIR)
    if tool_root:
      self.tool_root = os.path.abspath(tool_root)
    else:
      self.tool_root = os.path.join(self.src_root, DEFAULT_TOOLS_DIR)
    self._makefile_cache = {}
    self._target_cache = {}
    # detect cyclic dependencies
    self._resolving_targets = []
    
  def _add_target(self, target):
    self._target_cache[target.name] = target

  def _add_makefile(self, makefile):
    self._makefile_cache[makefile.makefile_path] = makefile

  def _resolve_src_path(self, name):
    if name.startswith('//'):
      return os.path.join(self.src_root, name[2:])
    if name.startswith('/'):
      raise error.MakeError('absolute paths not allowed', name)
    return os.path.join(self.src_root, name)

  def _resolve_out_path(self, name):
    if name.startswith('//'):
      return os.path.join(self.out_root, name[2:])
    if name.startswith('/'):
      raise error.MakeError('absolute paths not allowed', name)
    return os.path.join(self.out_root, name)

  def _normalize_target(self, target_name):
    path, name = target_name.split(':')
    path = os.path.join(path, MAKEFILE_SRC)
    path = self.target_path(os.path.abspath(path))
    return '%s:%s' % (path, name)

  def target_path(self, abspath):
    return '//' + os.path.relpath(abspath, self.src_root)

  def tool_path(self, tool):
    return os.path.join(self.tool_root, tool)
    
  def _out_root_for_target(self, target_name):
    makefile_path, name = target_name.split(':')
    relpath = os.path.dirname(makefile_path)
    return self._resolve_out_path(os.path.join(relpath, name + '.out'))

  @property
  def _makefile_gen_path(self):
    return os.path.join(self.build_root, MAKEFILE_GEN)

  # Resolve a target and its dependencies. Cache the resolved dependencies on
  # the target.
  def _resolve_target(self, target):
    for dep in target.deps:
      vprint('resolve dep: %s (%s)', dep, target.name)
      dep_target_name = self._normalize_target(dep)
      dep_target = self.resolve_target(dep_target_name)
      target.resolved_deps.append(dep_target)

  def resolve_target(self, target_name):
    vprint('resolve_target %s', target_name)
    if target_name in self._target_cache:
      return self._target_cache[target_name]
    if target_name in self._resolving_targets:
      raise error.MakeError('cycle detected resolving %s' % target_name,
                            self._resolving_targets)
    self._resolving_targets.append(target_name)
    makefile_path, name = target_name.split(':')
    if not makefile_path.endswith(MAKEFILE_SRC):
      makefile_path = os.path.join(makefile_path, MAKEFILE_SRC)
    makefile_path = self._resolve_src_path(makefile_path)
    makefile = self._read_makefile(makefile_path)
    vprint('resolve_target makefile: %s', makefile_path)
    vpprint(vars(makefile))
    target = makefile.get_target(target_name)
    vprint('resolve_target target: %s', target_name)
    vpprint(vars(target))
    self._resolve_target(target)
    last_target = self._resolving_targets.pop()
    if target_name != last_target:
      raise error.MakeError('last target does not match', target_name,
                            last_target)
    self._target_cache[target_name] = target
    return target

  def _read_makefile(self, path):
    path = os.path.abspath(path)
    if not path.startswith(self.src_root):
      raise error.MakeError('makefile not under src_root',
                            self.src_root, path)

    if path in self._makefile_cache:
      return self._makefile_cache[path]
    _makefile = makefile.Makefile(self, path)
    _makefile.read()
    self._makefile_cache[path] = _makefile
    return _makefile

  def run(self, mode, target_name, options):
    if mode not in ('build', 'clean', 'nuke'):
      raise error.MakeError('invalid mode', mode)

    if mode == 'nuke':
      vprint('nuking out_root: %s', self.out_root)
      shutil.rmtree(self.out_root)
      vprint('nuking build_root: %s', self.build_root)
      shutil.rmtree(self.build_root)
      return

    target_name = self._normalize_target(target_name)
    if not os.path.isdir(self.build_root):
      os.makedirs(self.build_root)

    # FIXME(msolomon) This is not a great way to do this, but works for now.
    old_out_root = self.out_root
    self.out_root = self._out_root_for_target(target_name)
    vprint('setting out_root %s -> %s', old_out_root, self.out_root)

    if not os.path.isdir(self.out_root):
      os.makedirs(self.out_root)
    
    target = self.resolve_target(target_name)
    vprint('run target %s %s', target_name, target.make_name)

    makefile_src = target.gen_makefile()
    #vprint(makefile_src)
    with open(self._makefile_gen_path, 'w') as f:
      f.write(makefile_src)

    args = ['make', '-r', '-f', self._makefile_gen_path]
    if options.dry_run:
      args.append('-n')
    if options.debug:
      args.append('-d')

    tname = target.make_name + '.' + mode
    args.append(tname)
    vprint(' '.join(args))
    proc = subprocess.Popen(args)
    proc.wait()
