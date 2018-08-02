#!/usr/bin/python3
# -*- coding: utf-8 -*-
# sets of checks for SIL fonts 
__author__ = 'Nicolas Spalinger'


from fontbakery.checkrunner import (
              INFO
            , WARN
            , ERROR
            , SKIP
            , PASS
            , FAIL
            , Section
            )
import os
from .shared_conditions import is_variable_font
from fontbakery.callable import condition, check, disable
from fontbakery.message import Message
from fontbakery.constants import(
        # TODO: priority levels are not yet part of the new runner/reporters.
        # How did we ever use this information?
        # Check priority levels:
        CRITICAL
      , IMPORTANT
#     , NORMAL
#     , LOW
#     , TRIVIAL
)

from fontbakery.fonts_spec import spec_factory

# don't import other specs for now
# spec_imports = (
#    ('.', ('general', 'cmap', 'head', 'os2', 'post', 'name',
#       'hhea', 'dsig', 'hmtx', 'gpos', 'gdef', 'kern', 'glyf',
#       'fvar', 'shared_conditions', 'loca')
#    ),
#    ('fontbakery.specifications.googlefonts', (
# "License URL matches License text on name table?"
#      'com_google_fonts_check_030',
#        # This condition is a dependency of the check above:
#        'familyname',
# )

specification = spec_factory(default_section=Section("SIL Fonts"))

# -------------------------------------------------------------------

@condition
def style(font):
  """Determine font style from canonical filename."""
  from fontbakery.constants import STYLE_NAMES
  filename = os.path.basename(font)
  if '-' in filename:
    stylename = os.path.splitext(filename)[0].split('-')[1]
    if stylename in [name.replace(' ', '') for name in STYLE_NAMES]:
      return stylename
  return None

@condition(force=True)
def expected_os2_weight(style):
  """The weight name and the expected OS/2 usWeightClass value inferred from
  the style part of the font name

  The Google Font's API which serves the fonts can only serve
  the following weights values with the corresponding subfamily styles:

  250, Thin
  275, ExtraLight
  300, Light
  400, Regular
  500, Medium
  600, SemiBold
  700, Bold
  800, ExtraBold
  900, Black

  Thin is not set to 100 because of legacy Windows GDI issues:
  https://www.adobe.com/devnet/opentype/afdko/topic_font_wt_win.html
  """
  if not style:
    return None
  # Weight name to value mapping:
  GF_API_WEIGHTS = {
      "Thin": 250,
      "ExtraLight": 275,
      "Light": 300,
      "Regular": 400,
      "Medium": 500,
      "SemiBold": 600,
      "Bold": 700,
      "ExtraBold": 800,
      "Black": 900
  }
  if style == "Italic":
    weight_name = "Regular"
  elif style.endswith("Italic"):
    weight_name = style.replace("Italic", "")
  else:
    weight_name = style

  expected = GF_API_WEIGHTS[weight_name]
  return weight_name, expected


@condition(force=True)
def os2_weight_warn():
  return {"style": "ExtraLight",
          "value": 250,
          "message": ("A value of 250 for OS/2 usWeightClass is acceptable for TTFs"
                      " (but not for OTFs), because it won't auto-bold (and blur)"
                      " in Windows GDI apps. However, since OTFs will, and because"
                      " we'd like to have OTFs and TTFs be as consistent as possible,"
                      " we'd prefer ExtraLight to be 275 in both cases.")}


@check(
  id = 'org.sil.scripts/check/001',
  misc_metadata = {
    'priority': CRITICAL
  }
)
def org_sil_scripts_check_001(font):
  """Checking file is named canonically.

  A font's filename must be composed in the following manner:
  <familyname>-<stylename>.ttf

  e.g Nunito-Regular.ttf, Oswald-BoldItalic.ttf
  """
  from fontbakery.constants import STYLE_NAMES

  filename = os.path.basename(font)
  basename = os.path.splitext(filename)[0]
  # remove spaces in style names
  style_file_names = [name.replace(' ', '') for name in STYLE_NAMES]
  if '-' in basename and basename.split('-')[1] in style_file_names:
    yield PASS, "{} is named canonically.".format(font)
  else:
    yield FAIL, ('Style name used in "{}" is not canonical.'
                 ' You should rebuild the font using'
                 ' any of the following'
                 ' style names: "{}".').format(font,
                                               '", "'.join(STYLE_NAMES))

@condition
def family_directory(fonts):
  """Get the path of font project directory."""
  if fonts:
    return os.path.dirname(fonts[0])

@check(
  id = 'org.sil.scripts/check/002',
  misc_metadata = {
    'priority': CRITICAL
  }
)
def org_sil_scripts_check_002(font):
  """Checking the OFL FAQ is present."""
  if family_directory:
    descfilepath = os.path.join(family_directory, "OFL-FAQ.txt")
    if os.path.exists(descfilepath):
      yield FAIL, ("Fail")
    else:
      yield PASS, ("Good")

@condition
def licenses(family_directory):
  """Get a list of paths for every license
     file found in a font project."""
  licenses = []
  if family_directory:
    for license in ['OFL.txt', 'ofl.txt', 'LICENSE.txt']:
      license_path = os.path.join(family_directory, license)
      if os.path.exists(license_path):
        licenses.append(license_path)
  return licenses


@condition
def license_path(licenses):
  """Get license path."""
  # return license if there is exactly one license
  return licenses[0] if len(licenses) == 1 else None


@condition
def license(license_path):
  """Get license filename."""
  if license_path:
    return os.path.basename(license_path)



@check(
  id = 'org.sil.scripts/check/003'
)
def org_sil_scripts_check_003(licenses):
  """Check font has a license."""
  if len(licenses) > 1:
    yield FAIL, Message("multiple",
                        ("More than a single license file found."
                         " Please review."))
  elif not licenses:
    yield FAIL, Message("none",
                        ("No license file was found."
                         " Please add an OFL.txt or a LICENSE.txt file."
                         " If you are running fontbakery on an"
                         " upstream repo, which is fine, just make sure"
                         " there is a temporary license file in"
                         " the same folder."))
  else:
    yield PASS, "Found license at '{}'".format(licenses[0])


@check(
  id = 'org.sil.scripts/check/004',
  conditions = ['license'],
  misc_metadata = {
    'priority': CRITICAL
  })
def org_sil_scripts_check_004(ttFont, license):
  """Check copyright namerecords match license file."""
  from fontbakery.constants import (NAMEID_LICENSE_DESCRIPTION,
                                    NAMEID_LICENSE_INFO_URL,
                                    PLACEHOLDER_LICENSING_TEXT,
                                    NAMEID_STR,
                                    PLATID_STR)
  from unidecode import unidecode
  failed = False
  placeholder = PLACEHOLDER_LICENSING_TEXT[license]
  entry_found = False
  for i, nameRecord in enumerate(ttFont["name"].names):
    if nameRecord.nameID == NAMEID_LICENSE_DESCRIPTION:
      entry_found = True
      value = nameRecord.toUnicode()
      if value != placeholder:
        failed = True
        yield FAIL, Message("wrong", \
                            ("License file {} exists but"
                             " NameID {} (LICENSE DESCRIPTION) value"
                             " on platform {} ({})"
                             " is not specified for that."
                             " Value was: \"{}\""
                             " Must be changed to \"{}\""
                             "").format(license,
                                        NAMEID_LICENSE_DESCRIPTION,
                                        nameRecord.platformID,
                                        PLATID_STR[nameRecord.platformID],
                                        unidecode(value),
                                        unidecode(placeholder)))
  if not entry_found:
    yield FAIL, Message("missing", \
                        ("Font lacks NameID {} "
                         "(LICENSE DESCRIPTION). A proper licensing entry"
                         " must be set.").format(NAMEID_LICENSE_DESCRIPTION))
  elif not failed:
    yield PASS, "Licensing entry on name table is correctly set."

@condition
def familyname(font):
  filename = os.path.basename(font)
  filename_base = os.path.splitext(filename)[0]
  return filename_base.split('-')[0]

@check(
  id = 'org.sil.scripts/check/005',
  conditions = ['familyname'],
  misc_metadata = {
    'priority': CRITICAL
  }
)
def org_sil_scripts_check_005(ttFont, familyname):
  """"License URL matches License text on name table?"""
  from fontbakery.constants import (NAMEID_LICENSE_DESCRIPTION,
                                    NAMEID_LICENSE_INFO_URL,
                                    PLACEHOLDER_LICENSING_TEXT)
  LICENSE_URL = {
    'OFL.txt': 'http://scripts.sil.org/OFL',
    'LICENSE.txt': 'http://www.apache.org/licenses/LICENSE-2.0',
  }
  LICENSE_NAME = {
    'OFL.txt': 'Open Font',
    'LICENSE.txt': 'Apache',
  }
  detected_license = False
  for license in ['OFL.txt', 'LICENSE.txt']:
    placeholder = PLACEHOLDER_LICENSING_TEXT[license]
    for nameRecord in ttFont['name'].names:
      string = nameRecord.string.decode(nameRecord.getEncoding())
      if nameRecord.nameID == NAMEID_LICENSE_DESCRIPTION and\
         string == placeholder:
        detected_license = license
        break

  else:
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
            yield FAIL, Message("licensing-inconsistency",
                                ("Licensing inconsistency in name table"
                                 " entries! NameID={} (LICENSE DESCRIPTION)"
                                 " indicates {} licensing, but NameID={}"
                                 " (LICENSE URL) has '{}'. Expected: '{}'"
                                 "").format(NAMEID_LICENSE_DESCRIPTION,
                                            LICENSE_NAME[detected_license],
                                            NAMEID_LICENSE_INFO_URL,
                                            string, expected))
    if not found_good_entry:
      yield FAIL, Message("no-license-found",
                          ("A known license URL must be provided in the"
                           " NameID {} (LICENSE INFO URL) entry."
                           " Currently accepted licenses are Apache or"
                           " Open Font License."
                           "").format(NAMEID_LICENSE_INFO_URL))
    else:
      if failed:
        yield FAIL, Message("bad-entries",
                            ("Even though a valid license URL was seen in"
                             " NAME table, there were also bad entries."
                             " Please review NameIDs {} (LICENSE DESCRIPTION)"
                             " and {} (LICENSE INFO URL)."
                             "").format(NAMEID_LICENSE_DESCRIPTION,
                                        NAMEID_LICENSE_INFO_URL))
      else:
        yield PASS, "Font has a valid license URL in NAME table."


specification.auto_register(globals())


# FIXME: use logging.info or remove?
for section_name, section in specification._sections.items():
  print ("{} checks on {}".format(len(section._checks), section_name))

