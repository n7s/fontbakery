#!/usr/bin/python3
# -*- coding: utf-8 -*-
# sets of checks for SIL fonts 
__author__ = 'Nicolas Spalinger'

import sys
from functools import partial

from fontbakery.commands.check_specification import (
    runner_factory as super_runner_factory, main as super_main)
from fontbakery.specifications.silfonts import specification

SILFONTS_SPECIFICS = {}

# runner_factory is used by the fontbakery dashboard.
# It is here in order to have a single place from which
# the spec is configured for the CLI and the worker.
def runner_factory(fonts):
    values = {}
    values.update(SILFONTS_SPECIFICS)
    values['fonts'] = fonts
    return super_runner_factory(specification, values=values)

main = partial(super_main, specification, values=SILFONTS_SPECIFICS)


if __name__ == '__main__':
    sys.exit(main())

