import config

test_constants = config.load_configs(['./tests/test_constants.py',
                                      './tests/test_constants2.py'])
assert test_constants.test == 1
assert test_constants.test2 == 2
#assert test_constants.test3 == 3
#print test_constants._vars()

from config import args
args.add_option('--file-arg', default='default-file.txt')
args.parse()

test_constants = config.load_configs(['./tests/test_constants.py',
                                      './tests/test_constants2.py'],
                                     True)
assert test_constants.test == 1
assert test_constants.file_arg == 'default-file.txt'
print test_constants._vars()
