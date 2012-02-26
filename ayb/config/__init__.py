# Encapsulate a config that is based on python syntax.
#
# Store things in un-importable files so you are forced to treat the config
# like an object, not a module.


import os
import time


class PyConfig(object):
  # A namespace for the config.
  #
  # All of our internal variables will be marked as such to prevent conflicts.
  def __init__(self, path):
    self._file_ = os.path.abspath(path)
    self._names_ = set()
    self._mtime_ = None
    self._load()

  # FIXME(msolomon) hook up reloader to inotify or something
  def _reload(self):
    if os.path.getmtime(self._file_) > self._mtime_:
      self._load()

  def _load(self):
    with open(self._file_) as f:
      _globals = {}
      config_vars = {}
      exec f in _globals, config_vars
      self._names_.update(config_vars.iterkeys())
      self._mtime_ = os.path.getmtime(self._file_)
      self.__dict__.update(config_vars)

  def _config_vars(self):
    return dict([(k,v) for k,v in self.__dict__.iteritems()
                 if k in self._names_])
  
  def __repr__(self):
    return '<PyConfig %r @ %s>' % (self._file_, self._mtime_)


class __MissingValue:
  pass
MissingValue = __MissingValue()


class MetaConfig(object):
  # config_list: a list of config objects to be resolved against
  def __init__(self, config_list):
    self._config_list_ = config_list
    self._names_ = set()
    for config in self._config_list_:
      config_vars = config._config_vars()
      self._names_.update(config_vars.iterkeys())
      self.__dict__.update(_vars)

  def _get_var(self, name):
    config_info = []
    for config in reversed(self._config_list_):
      value = getattr(config, name, MissingValue)
      config_info.append((config, value))
      if value is not MissingValue:
        break
    return config_info

  def _config_vars(self):
    return dict([(name, getattr(self, name)) for name in self._names_])

  def debug_vars(self):
    d = {}
    for config in self._config_list_:
      for k, v in config._config_vars().iteritems():
        d[k] = (v, config._file_)
    return d

    
# As a demo, you can see how data can be built up using programmatic
# transforms on config data.
class DeferredConfig(object):
  def __init__(self, config):
    self._config = config

  def set_config(self, config):
    self._config = config

  @property
  def log_path(self):
    return os.path.join(self._config.file_root, 'log')


def load_configs(path_list, parse_args=False):
  config_list = [PyConfig(path) for path in path_list]

  if parse_args:
    # deferred import to break cycle
    from . import args
    _, _, cli_config = args.parse()
    config_list.append(cli_config)
    
  return MetaConfig(config_list)
