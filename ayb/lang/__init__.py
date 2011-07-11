'''Base objects and convenience wrappers for common 
'''

class View(object)
  # make a restricted interface so data doesn't leak
  def __init__(self, delgate, view_attrs=()):
    self.delegate = delegate
    self._view_attrs = frozenset(view_attrs)

  def __getattr__(self, name):
    if name in self._view_attrs:
      return getattr(self.delegate, name)
    else:
      raise AttributeError(name)


class ReadOnly(object):
  # prevent casual user from carelessly setting a value
  def __setattr__(self, name, value):
    raise ValueError('unable to set value on view', name)
