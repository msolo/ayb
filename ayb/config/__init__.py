# Encapsulate a config that is based on python syntax.
#
# Store things in un-importable files so you are forced to treat the config
# like an object, not a module.


import os
import time


class PyConfig(object):
  """A namespace for the config.

  All of our internal variables will be marked as such to prevent conflicts.
  """
  def __init__(self, path):
    self.__file__ = path
    self.__mtime__ = None
    self.__names__ = set()
    self._load()

  def _reload(self):
    if os.path.getmtime(self.__file__) > self.__mtime__:
      self._load()

  def _load(self):
    with open(self.__file__) as f:
      _globals = {}
      config_vars = {}
      exec f in _globals, config_vars
      self.__names__.update(config_vars.iterkeys())
      self.__dict__.update(config_vars)
      self.__mtime__ = os.path.getmtime(self.__file__)

  def _vars(self):
    return dict([(k,v) for k,v in self.__dict__.iteritems()
                 if k in self.__names__])
  
  def __repr__(self):
    return '<PyConfig %r @ %s>' % (self.__file__, self.__mtime__)


class _MissingValue:
  pass
MissingValue = _MissingValue()


class MetaConfig(object):
  # config_list: a list of config objects to be resolved agains
  def __init__(self, config_list):
    self.__config_list = config_list
    for config in self.__config_list:
      self.__dict__.update(config.__dict__)

  def _get_var(self, name):
    config_info = []
    for config in reversed(self.__config_list):
      value = getattr(config, name, MissingValue)
      config_info.append((config, value))
      if value is not MissingValue:
        break
    return config_info

  def __getattr__(self, name):
    config_info = self._get_var(name)
    if config_info:
      return config_info[-1][-1]
    else:
      raise AttributeError(name)

  def _vars(self):
    d = {}
    for config in self.__config_list:
      d.update(config._vars())
    return d


def load_configs(path_list, parse_args=False):
  config_list = [PyConfig(path) for path in path_list]

  if parse_args:
    # deferred import to break cycle
    from . import args
    _, _, cli_config = args.parse()
    config_list.append(cli_config)
    
  return MetaConfig(config_list)
