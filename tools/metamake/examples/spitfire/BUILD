# A demo set of targets for the spitfire compiler.
# http://code.google.com/p/spitfire/source/browse/#svn%2Ftrunk
# Copy this BUILD file into the root of the source tree and try:
# metamake.par build :runtime

py_exe(name='spitfire_compile',
       srcs=[glob('spitfire/**/*.py'),
             'yappsrt.py',
             ],
       main='scripts/spitfire-compile',
       deps=[':_udn',
             ],
       )

py_lib(name='runtime',
       srcs=[glob('spitfire/runtime/**/*.py'),
             ],
       deps=[':_udn',
             ],
       )

py_ext(name='_udn',
       srcs=['spitfire/runtime/_udn.c',],
       )

file_group(name='test_files',
       data=[glob('tests/**/*'),],
       )

tgzfile(name='testtgz',
        deps=[':spitfire_compile',
              ':test_files',
              ]
        )

tbzfile(name='testtbz',
        deps=[':spitfire_compile',
              ':test_files',
              ]
        )
