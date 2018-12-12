#!/usr/bin/python2

import pkgutil

from fontbakery import specifications
from fontbakery.callable import FontBakeryCheck

checks = []

for importer, modname, ispkg in pkgutil.iter_modules(specifications.__path__):
    exec('from fontbakery.specifications import ' + modname)
    exec('module = ' + modname)
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if isinstance(attr, FontBakeryCheck):
            checks.append((attr.__name__, attr.__doc__))

checks.sort()

for name, doc in checks:
    print('# ' + name)
    print()
    print(doc.strip())
    print()


