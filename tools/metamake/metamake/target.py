import os


# srcs: always files, relative to the makefile location
# deps: 'path:target_name', paths beginning with '//' are relative to the "make
# root", paths beginning with ':' are relative to the current makefile.
# outs: always files, relative to the makefile location - these will
#       be interpreted relative to the maker.out_root.
class Target(object):
  def __init__(self, makefile, name='', srcs=(), data=(), deps=(), outs=(), **kargs):
    self.makefile = makefile
    self._name = name
    self.srcs = flatten_iterables(srcs)
    self.data = flatten_iterables(data)
    self.deps = deps
    self.outs = flatten_iterables(outs)
    self.clean_outs = []
    self.resolved_deps = []
    self.__dict__.update(kargs)

  # A fully qualified target: //path:name
  @property
  def name(self):
    p = self.makefile.maker.target_path(self.makefile.makefile_path)
    return '%s:%s' % (p, self._name) 

  # An escaped target that can be used in a Makefile
  @property
  def make_name(self):
    return escape_make_name(self.name)

  def make_context(self):
    return {
      'name': self.name,
      'make_name': self.make_name,
      'srcs_list': ' '.join(self.srcs),
      'data_list': ' '.join(self.data),
      'build_deps_list': ' '.join([dep.make_name + '.build'
                                   for dep in self.resolved_deps]),
      'outs_list': ' '.join([self.makefile.resolve_out_path(x)
                             for x in self.outs]),
      'clean_outs_list': ' '.join([self.makefile.resolve_out_path(x)
                                   for x in self.clean_outs]),
      'clean_deps_list': ' '.join([dep.make_name + '.clean'
                                   for dep in self.resolved_deps]),
      'out_root': self.makefile.maker.out_root,
      'build_root': self.makefile.maker.build_root,
      }

  def gen_targets(self):
    ctx = self.make_context()
    # rm -df $(sort $(dir %(outs_list)s))
    return '''# %(name)s
%(make_name)s.build: %(build_deps_list)s %(outs_list)s %(data_list)s;

%(make_name)s.clean: %(clean_deps_list)s
\trm -df %(outs_list)s %(clean_outs_list)s
''' % ctx

  def gen_productions(self):
    return ''

  def gen_makefile(self):
    b = [self.gen_targets(),
         self.gen_productions(),
         ]
    for dep in self.resolved_deps:
      b.append(dep.gen_makefile())
    return '\n'.join(b)

  # A list of all data files.
  def all_data_files(self):
    data = self.data[:]
    for dep in self.resolved_deps:
      data.extend(dep.all_data_files())
    return data


def flatten_iterables(xi):
  results = []
  for x in xi:
    if isinstance(x, (set, list, tuple)):
      results.extend(x)
    else:
      results.append(x)
  return results

# Makefile targets need to be escaped.
def escape_make_name(fqname):
  return fqname.replace('/', '_').replace(':', '_')
