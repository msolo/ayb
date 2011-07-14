from lang import rimport

m = rimport.restricted_import('test_import', path='./tests')
print m

# not clear to me that this should be made to work - too ambiguous
#m = rimport.restricted_import('test_import.module_value', path='./tests')
#print m

m = rimport.restricted_import('test_import', fromlist=('module_value',),
                              path='./tests')
print m

print rimport.restricted_import('test_import_package.package_module', fromlist=(),
                              path='./tests')
print rimport.restricted_import('test_import_package', fromlist=(),
                              path='./tests')
print rimport.restricted_import('test_import_package', fromlist=('package_module',),
                              path='./tests')


try:
  m = rimport.restricted_import('os', path='./tests')
  print m
except ImportError:
  # expected
  pass

print rimport._module_cache
