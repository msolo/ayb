#!/usr/bin/env python

# Link a python source tree into a single self-executing zip archive.
# The zip can also be extracted and run manually.
#
# Distributed under a BSD license.
# Copyright (c) 2012 Mike Solomon

import cStringIO
import compileall
import imp
import marshal
import optparse
import os
import string
import sys
import zipfile

bootstrap_src_tmpl = """
# ParImporter bootstrap
# 
# Insert a custom importer to allow compressed .so files to load transparently.
#
# ${tracer}

import cStringIO
import errno
import hashlib
import imp
import os
import sys
import tempfile
import zipfile
import zipimport

newname = '_par_bootstrap_'
sys.modules[newname] = sys.modules[__name__]
del sys.modules[__name__]

def log(fmt, *args):
  if os.environ.get('PLINK_DEBUG'):
    if args:
      fmt = fmt % args        
    print >> sys.stderr, 'plink:', fmt

class ParImporter(zipimport.zipimporter):
  def __init__(self, path):
    if not path.startswith(sys.path[0]):
      # Normally the first path item will be the our self-executing zip.
      # Otherwise, just skip it.
      log('ParImporter ignoring path:%s', path)
      raise ImportError
    self.data_cache = {}
    zipimport.zipimporter.__init__(self, path)
    log('ParImporter init path:%s archive:%s prefix:%s', path, self.archive, self.prefix)
  
  def find_module(self, fullname, path=None):
    log('find_module %s', fullname)
    data_path = fullname.replace('.', '/') + '.so'

    # Check for native .so modules first and track what needs to be extracted
    # before an import is run.
    try:
      self.data_cache[fullname] = self.get_data(data_path)
      log('found data_path:%s fullname:%s', data_path, fullname)
      return self
    except IOError:
      # This just means there was no data, which is expected sometimes.
      pass
    
    return zipimport.zipimporter.find_module(self, fullname, path)
  
  def load_module(self, fullname):
    if fullname in sys.modules:
      log('load_module %s (cached)', fullname)
      return sys.modules[fullname]

    if fullname in self.data_cache:
      # This resource must be extracted to a physical file.
      data = self.data_cache[fullname]
      del self.data_cache[fullname]
      bin_name = os.path.basename(sys.path[0])
      par_dir = '%s/%s-%s' % (tempfile.gettempdir(), bin_name, par_signature)
      try:
        os.mkdir(par_dir)
      except OSError as e:
        if e[0] != errno.EEXIST:
          raise e
      path = '%s/%s.so' % (par_dir, fullname)
      if not os.path.exists(path):
        log('load_module %s (extracting to %s)', fullname, path)
        tmp_path = path + '-' + os.urandom(8).encode('hex')
        with open(tmp_path, 'wb') as f:
          f.write(data)
        # Atomically rename so you don't get partially extracted files.
        os.rename(tmp_path, path)
      else:
        log('load_module %s (extracted to %s)', fullname, path)

      for suffix, file_mode, module_type in imp.get_suffixes():
        if path.endswith(suffix):
          s = (suffix, file_mode, module_type)
          f = open(path, file_mode)
          mod = imp.load_module(fullname, f, path, s)
          mod.__loader__ = self
          return mod
      raise ImportError('No module for %s (plink)' % fullname)

    log('load_module %s (default)', fullname)
    return zipimport.zipimporter.load_module(self, fullname)

log('initial sys.path: %s', sys.path)
sys.path_hooks.insert(0, ParImporter)

m = hashlib.md5()
m.update(open(sys.path[0]).read())
par_signature = m.hexdigest()

zf = zipfile.ZipFile(sys.path[0], 'r')
zf_data = zf.read('__run__.py')
zf.close()
exec zf_data
"""


tracer = 'plink-tracer-19830319'
zipmagic = '\x50\x4B\x03\x04'
pymagic = imp.get_magic() + '\000\000\000\000'

def mkbootstrap():
  return string.Template(bootstrap_src_tmpl).substitute(tracer=tracer)

# Takes a directory and makes a zip file containing any files therein
# that are (normally) loadable by Python.
def zipdir(path, options):
  compileall.compile_dir(path, ddir='', quiet=True)
  path = os.path.normpath(path)
  prefix = path + '/'
  b = cStringIO.StringIO()
  z = zipfile.ZipFile(b, 'w', zipfile.ZIP_DEFLATED)
  for root, dirs, files in os.walk(path):
    for f in sorted(files):
      if f.endswith(('.py', '.pyc', '.pyo', '.so')):
        if options.strip and f.endswith('.py'):
          continue
        realpath = os.path.join(root, f)
        arcpath = realpath.replace(prefix, '')
        log('deflate %s -> %s', realpath, arcpath)
        z.write(realpath, arcpath)
  z.close()
  return b.getvalue()

def log(fmt, *args):
  if options.verbose:
    if args:
      fmt = fmt % args        
    print >> sys.stderr, 'plink:', fmt

options = None
usage = """
%prog --main-file <main source file> <src directory>

PLINK_DEBUG=1 ./module.par
"""

if __name__ == '__main__':
  p = optparse.OptionParser(usage=usage)
  p.add_option('-v', '--verbose', action='store_true')
  p.add_option('-o', '--output')
  p.add_option('--strip', action='store_true', help='strip .py files')
  p.add_option('--format', default='par')
  p.add_option('--main-file',
               help='name of python to run after bootstrap')
  p.add_option('--python-binary', default='/usr/bin/python -ESs',
               help='adjust the shebang line of the output')
  (options, args) = p.parse_args()

  if not args:
    p.print_usage()
    sys.exit(2)

  if not options.main_file:
    sys.exit('--main-file must be specified')

  zipfn = args.pop(0)
  if not options.output:
    options.output = '%s.%s' % (os.path.basename(options.main_file).rsplit('.', 1)[0], options.format)

  if not os.path.isdir(zipfn):
    sys.exit('source must be a directory')
    
  bootstrap_src = mkbootstrap()
  log(bootstrap_src)

  with open(options.main_file) as f:
    main_src = f.read()        
  with open(os.path.join(zipfn, '__main__.py'), 'w') as f:
    f.write(bootstrap_src)
  with open(os.path.join(zipfn, '__run__.py'), 'w') as f:
    f.write(main_src)

  zipdata = zipdir(zipfn, options)

  if options.format == 'pyc':
    bootstrap_code = compile(bootstrap_src, '<plink bootstrap>', 'exec')
    code = pymagic + marshal.dumps(bootstrap_code) + zipdata
  elif options.format == 'par':
    code = '#!%s\n' % options.python_binary + zipdata

  with open(options.output, 'w') as f:
    f.write(code)

  os.chmod(options.output, 0755)
