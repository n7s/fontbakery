# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from fontbakery.testrunner import (
              DEBUG
            , INFO
            , WARN
            , ERROR
            , SKIP
            , PASS
            , FAIL
            , distribute_generator
            , Section
            , TestRunner
            , Spec
            )

from fontbakery.callable import condition, test
from fontbakery.testadapters.oldstyletest import oldStyleTest

import os
from fontTools.ttLib import TTFont

from fontbakery.constants import(
        # TODO: priority levels are not yet part of the new runner/reporters.
        # How did we ever use this information?
        # Check priority levels:
        TRIVIAL
      , LOW
      , NORMAL
      , IMPORTANT
      , CRITICAL

      , LICENSE_URL
      , NAMEID_DESCRIPTION
      , NAMEID_LICENSE_DESCRIPTION
      , NAMEID_LICENSE_INFO_URL
      , PLACEHOLDER_LICENSING_TEXT
      , STYLE_NAMES
)


conditions={}
def registerCondition(condition):
  conditions[condition.name] = condition
  return condition

tests=[]
def registerTest(test):
  tests.append(test)
  return test

@registerCondition
@condition
def ttFont(font):
  return TTFont(font)

@registerTest
@oldStyleTest(
    id='com.google.fonts/test/001'
  , priority=CRITICAL
)
def check_file_is_named_canonically(fb, font):
  """Checking file is named canonically

  A font's filename must be composed in the following manner:

  <familyname>-<stylename>.ttf

  e.g Nunito-Regular.ttf, Oswald-BoldItalic.ttf
  """
  file_path, filename = os.path.split(font)
  basename = os.path.splitext(filename)[0]
  # remove spaces in style names
  style_file_names = [name.replace(' ', '') for name in STYLE_NAMES]
  if '-' in basename and basename.split('-')[1] in style_file_names:
    fb.ok("{} is named canonically".format(font))
    return True
  else:
    fb.error(('Style name used in "{}" is not canonical.'
              ' You should rebuild the font using'
              ' any of the following'
              ' style names: "{}".').format(font,
                                            '", "'.join(STYLE_NAMES)))
    return False

@registerTest
@oldStyleTest(
    id='com.google.fonts/test/008'
)
def check_fonts_have_consistent_underline_thickness(fb, ttFonts):
  """Fonts have consistent underline thickness?"""
  fail = False
  uWeight = None
  for ttfont in ttFonts:
    if uWeight is None:
      uWeight = ttfont['post'].underlineThickness
    if uWeight != ttfont['post'].underlineThickness:
      fail = True

  if fail:
    # FIXME: more info would be great! Which fonts are the outliers
    fb.error("Thickness of the underline is not"
             " the same accross this family. In order to fix this,"
             " please make sure that the underlineThickness value"
             " is the same in the 'post' table of all of this family"
             " font files.")
  else:
    fb.ok("Fonts have consistent underline thickness.")

@registerTest
@oldStyleTest(
    id='com.google.fonts/test/015'
)
def check_font_has_post_table_version_2(fb, ttFont):
  """Font has post table version 2 ?"""
  if ttFont['post'].formatType != 2:
    fb.error(("Post table should be version 2 instead of {}."
              "More info at https://github.com/google/fonts/"
              "issues/215").format(ttFont['post'].formatType))
  else:
    fb.ok("Font has post table version 2.")

# DEPRECATED: 021 - "Checking fsSelection REGULAR bit"
#             025 - "Checking fsSelection ITALIC bit"
#             027 - "Checking fsSelection BOLD bit"
#
# Replaced by 129 - "Checking OS/2.fsSelection value"

# DEPRECATED: 022 - "Checking that italicAngle <= 0"
#             023 - "Checking that italicAngle is less than 20 degrees"
#             024 - "Checking if italicAngle matches font style"
#
# Replaced by 130 - "Checking post.italicAngle value"

# DEPRECATED: 026 - "Checking macStyle ITALIC bit"
#             ??? - "Checking macStyle BOLD bit"
#
# Replaced by 131 - "Checking head.macStyle value"

@registerCondition
@condition
def licenses(font):
  """Get license path"""
  licenses = []
  file_path = os.path.dirname(font)
  for license in ['OFL.txt', 'LICENSE.txt']:
    license_path = os.path.join(file_path, license)
    if os.path.exists(license_path):
      licenses.append(license_path)
  return licenses

@registerCondition
@condition
def license(licenses):
  """Get license path"""
  # return license if there is exactly one license
  return licenses[0] if len(licenses) == 1 else None

@registerTest
@oldStyleTest(
    id='com.google.fonts/test/028'
)
def check_font_has_a_license(fb, licenses):
  """Check font has a license"""
  if len(licenses) > 1:
    fb.error("More than a single license file found."
                 " Please review.")
  elif not licenses:
    fb.error("No license file was found."
               " Please add an OFL.txt or a LICENSE.txt file."
               " If you are running fontbakery on a Google Fonts"
               " upstream repo, which is fine, just make sure"
               " there is a temporary license file in the same folder.")
  else:
    fb.ok("Found license at '{}'".format(licenses[0]))

@registerTest
@oldStyleTest(
    id='com.google.fonts/test/030'
  , conditions=['license']
  , priority=CRITICAL
)
def check_font_has_a_valid_license_url(fb, ttFont):
  """"License URL matches License text on name table ?"""
  detected_license = False
  for license in ['OFL.txt', 'LICENSE.txt']:
    placeholder = PLACEHOLDER_LICENSING_TEXT[license]
    for nameRecord in ttFont['name'].names:
      string = nameRecord.string.decode(nameRecord.getEncoding())
      if nameRecord.nameID == NAMEID_LICENSE_DESCRIPTION and\
         string == placeholder:
        detected_license = license
        break

  found_good_entry = False
  if detected_license:
    failed = False
    expected = LICENSE_URL[detected_license]
    for nameRecord in ttFont['name'].names:
      if nameRecord.nameID == NAMEID_LICENSE_INFO_URL:
        string = nameRecord.string.decode(nameRecord.getEncoding())
        if string == expected:
          found_good_entry = True
        else:
          failed = True
          fb.error(("Licensing inconsistency in name table entries!"
                    " NameID={} (LICENSE DESCRIPTION) indicates"
                    " {} licensing, but NameID={} (LICENSE URL) has"
                    " '{}'. Expected:"
                    " '{}'").format(NAMEID_LICENSE_DESCRIPTION,
                                    LICENSE_NAME[detected_license],
                                    NAMEID_LICENSE_INFO_URL,
                                    string, expected))
  if not found_good_entry:
    fb.error(("A License URL must be provided in the "
              "NameID {} (LICENSE INFO URL) entry."
              "").format(NAMEID_LICENSE_INFO_URL))
  else:
    if failed:
      fb.error(("Even though a valid license URL was seen in NAME table,"
                " there were also bad entries. Please review"
                " NameIDs {} (LICENSE DESCRIPTION) and {}"
                " (LICENSE INFO URL).").format(NAMEID_LICENSE_DESCRIPTION,
                                               NAMEID_LICENSE_INFO_URL))
    else:
      fb.ok("Font has a valid license URL in NAME table.")


@registerTest
@oldStyleTest(
    id='com.google.fonts/test/031'
  , priority=CRITICAL
)
def check_description_strings_in_name_table(fb, ttFont):
  """Description strings in the name table
  must not contain copyright info."""

  failed = False
  for name in ttFont['name'].names:
    if 'opyright' in name.string.decode(name.getEncoding())\
       and name.nameID == NAMEID_DESCRIPTION:
      failed = True

  if failed:
    fb.error(("Namerecords with ID={} (NAMEID_DESCRIPTION)"
              " should be removed (perhaps these were added by"
              " a longstanding FontLab Studio 5.x bug that"
              " copied copyright notices to them.)"
              "").format(NAMEID_DESCRIPTION))
  else:
    fb.ok("Description strings in the name table"
          " do not contain any copyright string.")


specificiation = Spec(
    conditions=conditions
  , testsections=[Section('Default', tests)]
  , iterargs={'font': 'fonts'}
  , derived_iterables={'ttFonts': ('ttFont', True)}
)
