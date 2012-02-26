# Export command line args to standard builtin names OPTIONS, ARGS and CONFIG.
#
# Use module so that there is one singleton parser.

import __builtin__
import time

from optparse import *


default_option_parser = OptionParser()
add_option = default_option_parser.add_option
set_defaults = default_option_parser.set_defaults
all_options = default_option_parser._get_all_options

class CmdLineConfig(object):
  def __init__(self, default_values):
    self._file_ = '<command line>'
    self._mtime_ = time.time()
    self.__dict__.update(default_values.__dict__)
    self._names_ = set(default_values.__dict__)

  def _config_vars(self):
    return dict([(k,v) for k,v in self.__dict__.iteritems()
                 if k in self._names_])
  
  def __repr__(self):
    return '<CmdLineConfig %r @ %s>' % (self._file_, self._mtime_)
    
# options can be used to standin as a piece of the config and can overrride
# everything else in the chain.
def parse():
  config = CmdLineConfig(default_option_parser.get_default_values())
  options, args = default_option_parser.parse_args()
  __builtin__.OPTIONS = options
  __builtin__.ARGS = args
  __builtin__.CONFIG = config
  return options, args, config

