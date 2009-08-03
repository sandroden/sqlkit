# -*- mode: python -*-
# spec file for pyinstaller. Read README.pyinstaller for more info 

import os
import sys

ROOT = os.path.dirname(sys.argv[1]) + '/'

#sqlkit = Tree(ROOT + 'sqlkit', prefix='sqlkit')
locale = Tree(ROOT + 'sqlkit/locale', prefix='sqlkit/locale')
demo = Tree(ROOT + 'demo', prefix='demo',
            excludes= ROOT + 'demo/layout')

import babel
babel = Tree(babel.__path__[0], prefix='babel')


a = Analysis([os.path.join(HOMEPATH,'support/_mountzlib.py'),
              os.path.join(HOMEPATH,'support/useUnicode.py'),
              ROOT + '/bin/sqledit'],
             pathex=[os.path.abspath(os.path.dirname(sys.argv[0]))]
             )

pyz = PYZ(a.pure - babel)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=1,
          name=os.path.join('build/pyi.linux2/sqledit', 'sqledit'),
          debug=False,
          strip=True,
          upx=True,
          console=1 )

coll = COLLECT( exe,
                a.binaries,
                a.zipfiles,
                a.datas,
                babel,
                demo,
                locale,
                #sqlkit,
                strip=False,
                upx=True,
#                name=os.path.join('dist', 'sqledit')
                name=os.path.join('pyinstaller', 'sqlkit')
                )
