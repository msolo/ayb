import collections
import cPickle
import operator
import struct
import zlib

from itertools import izip


class PickleIO(object):
  record_header_format = '!Ii'
  record_header_size = struct.calcsize(record_header_format)
  
  def __init__(self, pfile, key_list=None, attr_list=None, record_type=tuple):
    self.pfile = pfile
    self.key_list = key_list
    self.record_type = record_type
    if key_list:
      self._getter = operator.itemgetter(*key_list)
    elif attr_list:
      self._getter = operator.attrgetter(*attr_list)
    
  def close(self):
    self.pfile.close()

  def fmt_item(self, item):
    if isinstance(item, tuple):
      data = cPickle.dumps(tuple(item), cPickle.HIGHEST_PROTOCOL)
    else:
      data = cPickle.dumps(self._getter(item), cPickle.HIGHEST_PROTOCOL)
    data_len, checksum = len(data), zlib.adler32(data)
    header = struct.pack(self.record_header_format, data_len, checksum)
    print "data_len", data_len, "checksum", checksum
    return header + data
    

class PickleRecordWriter(PickleIO):
  def write_record(self, item):
    self.pfile.write(self.fmt_item(item))


class PickleRecordReader(PickleIO):
  validate_checksum = True
  
  def seek(self, record_offset):
    self.pfile.seek(record_offset)

  def tell(self):
    return self.pfile.tell()

  def __iter__(self):
    return self

  def next(self):
    record = self.read_record()
    if record is None:
      raise StopIteration
    else:
      return record

  def read_record(self):
    raw_data = self.pfile.read(self.record_header_size)
    if not raw_data:
      return None
    data_len, checksum = struct.unpack(self.record_header_format, raw_data)
    data = self.pfile.read(data_len)
    new_checksum = zlib.adler32(data)
    if self.validate_checksum and checksum != new_checksum:
      # FIXME(msolomon) we could creep along byte-by-byte and see if we
      # can get back on track. This shouldn't happen very often at all.
      raise ValueError('checksum failed', checksum, new_checksum, data_len, repr(data))
    values = cPickle.loads(data)
    if self.record_type is dict:
      if self.key_list:
        return dict(izip(self.key_list, values))
      if self.attr_list:
        return dict(izip(self.attr_list, values))
    elif self.record_type is tuple:
      return values
    elif isinstance(self.record_type, tuple):
      # optimization for namedtuple
      return self.record_type._make(values)
    else:
      return self.record_type(*values)
