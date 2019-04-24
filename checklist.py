#!/usr/bin/python3
# script to export fontbakery checks for review
# adapted from https://github.com/googlefonts/fontbakery/issues/2039

import pkgutil

from fontbakery import profiles
from fontbakery.callable import FontBakeryCheck

checks = []

for importer, modname, ispkg in pkgutil.iter_modules(profiles.__path__):
  exec('from fontbakery.profiles import ' + modname)
  exec('module = ' + modname)
  for attr_name in dir(module):
    attr = getattr(module, attr_name)
    if isinstance(attr, FontBakeryCheck):
      try:
        rationale = f"\n## rationale:\n\t{attr.rationale}\n"
      except:
        rationale = ""
      checks.append((attr.id, attr.__doc__, rationale))

checks.sort()

for check_id, doc, rationale in checks:
  print(f'# {check_id}\n{doc.strip()}{rationale}\n')


