'''Export command line args to standard builtin names OPTIONS and ARGS.

Use module so that there is one singleton parser.
'''

from optparse import *
import time

default_option_parser = OptionParser()
add_option = default_option_parser.add_option
set_defaults = default_option_parser.set_defaults
all_options = default_option_parser._get_all_options

class CmdLineConfig(object):
  def __init__(self, default_values):
    self.__file__ = '<command line>'
    self.__mtime__ = time.time()
    self.__dict__.update(default_values.__dict__)

  def __repr__(self):
    return '<CmdLineConfig %r @ %s>' % (self.__file__, self.__mtime__)
    
# options can be used to standin as a piece of the config and can overrride
# everything else in the chain.
def parse():
  import __builtin__
  values = CmdLineConfig(default_option_parser.get_default_values())
  options, args = default_option_parser.parse_args(values=values)
  __builtin__.OPTIONS = options
  __builtin__.ARGS = args
  return options, args

