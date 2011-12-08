import sys
from lang import rimport

m = rimport.rimport('test_import', path='./tests')
#print m

# not clear to me that this should be made to work - too ambiguous
#m = rimport.rimport('test_import.module_value', path='./tests')
#print m

m = rimport.rimport('test_import', fromlist=('module_value',),
                    path='./tests')
#print m

m = rimport.rimport('test_import_package.package_module', fromlist=(),
                    path='./tests')
#print rimport.rimport('test_import_package', fromlist=(),
#                      path='./tests')
#print rimport.rimport('test_import_package', fromlist=('package_module',),
#                      path='./tests')


try:
  m = rimport.rimport('os', path='./tests')
#  print m
except ImportError:
  # expected
  pass

def dump_cache(module_cache):
  module_count = 0
  for k,v in module_cache.iteritems():
    if isinstance(v, dict):
      module_count += dump_cache(v)
    else:
      module_count += 1
  return module_count

if dump_cache(rimport._module_cache) != 2:
  sys.exit(1)
