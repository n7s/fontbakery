#!/usr/bin/python3
# -*- coding: utf-8 -*-
'''sets of checks for SIL fonts, still a WIP, heavily inspired from existing checks'''
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
from fontbakery.constants import(PriorityLevel,
                                 NameID,
                                 PlatformID,
                                 WindowsEncodingID)
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
# checks are defined (or added/skipped) below


# declaring overall conditions
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

# We use `check` as a decorator to wrap an ordinary python
# function into an instance of FontBakeryCheck to prepare
# and mark it as a check.
# A check id is mandatory and must be globally and timely
# unique. Descriptive words are preferred to numerical ids.
# Checks have id, rationale, conditions and misc_metadata (priority)
# Then there is a corresponding function (named similarly) returning/yielding FAIL PASS.
# Conditions can be defined and added as dependencies. 


@check(
    id='org.sil.software/check/has-R',
    rationale=''' rationale ''',
    conditions=[],
    misc_metadata={
        'priority': PriorityLevel.IMPORTANT

    },
)
# This check will run once for each item in `fonts`.
# This is achieved via the iterag definition of font: fonts
def has_cap_r_in_name(font):
    """Filename contains an "R"."""
    # This test is not very useful again, but for each
    # input it can result in a PASS or a FAIL.
    if 'R' not in font:
      # This is our first check that can potentially fail.
      # To document this: return is also ok in a check.
      return FAIL, '"R" is not in font filename.'
    else:
      # since you can't return at one point in a function
      # and yield at another point, we always have to
      # use return within this check.
      return PASS, '"R" is in font filename.'


@check(
    id='org.sil.software/check/directories',
    rationale=''' check that the project directories are in good shape  ''',
    misc_metadata={
        'priority': PriorityLevel.CRITICAL
    }
)
def com_google_fonts_check_directories(fonts):
  """Checking all files are in the same directory.

  If the set of font files passed in the command line is not all in the
  same directory, then we warn the user since the tool will interpret
  the set of files as belonging to a single family (and it is unlikely
  that the user would store the files from a single family spread in
  several separate directories).
  """
  directories = ['source', 'build', 'results', 'buildlinux2']
  for target_file in fonts:
    directory = os.path.dirname(target_file)
    if directory not in directories:
      directories.append(directory)

  if len(directories) == 1:
    yield PASS, "All files are in the same directory."
  else:
    yield FAIL, ("Not all fonts passed in the command line"
                 " are in the same directory. This may lead to"
                 " bad results as the tool will interpret all"
                 " font files as belonging to a single"
                 " font family. The detected directories are:"
                 " {}".format(directories))


@check(
    id='org.sil.software/check/naming',
    rationale=''' foo ''',
    conditions=[],
    misc_metadata={
        'priority': PriorityLevel.CRITICAL
    }
)
def org_sil_software_check_naming(font):
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
    id='org.sil.software/check/project_structure',
    rationale=''' foo ''',
    conditions=[],
    misc_metadata={
        'priority': PriorityLevel.CRITICAL
    }
)
def org_sil_software_check_project_structure(font):
  """Checking the wscript is present. IOW is this font project CI-enabled? """
  if family_directory:
    descfilepath = os.path.join(family_directory, "wscript")
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
      for license in ['OFL.txt', 'LICENSE.txt']:
        license_path = os.path.join(family_directory, license)
        # FIXME: need a way to walk the directories to include parent root folder since our builds are in results/ and we run the checks there.
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
    id='org.sil.software/check/font_license',
    rationale=''' foo ''',
    conditions=['license'],
    misc_metadata={
        'priority': PriorityLevel.CRITICAL
    }
)
def org_sil_software_check_font_license(licenses):
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
                           " upstream repo, just make sure"
                           " there is a temporary license file in"
                           " the same folder."))
    else:
      yield PASS, "Found license at '{}'".format(licenses[0])


@check(
    id='org.sil.software/check/matching-metadata',
    rationale=''' foo ''',
    conditions=['license'],
    misc_metadata={
         'priority': PriorityLevel.CRITICAL
    }
)
def org_sil_software_check_matching_metadata(ttFont, license):
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
          yield FAIL, Message("wrong",
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
      yield FAIL, Message("missing",
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


@condition
def font_familynames(ttFont):
    from fontbakery.utils import get_name_entry_strings
    from fontbakery.constants import NAMEID_FONT_FAMILY_NAME
    return get_name_entry_strings(ttFont, NAMEID_FONT_FAMILY_NAME)


@condition
def typographic_familynames(ttFont):
    from fontbakery.utils import get_name_entry_strings
    from fontbakery.constants import NAMEID_TYPOGRAPHIC_FAMILY_NAME
    return get_name_entry_strings(ttFont, NAMEID_TYPOGRAPHIC_FAMILY_NAME)


@check(
    id='org.sil.software/check/license_URLs',
    rationale=''' foo ''',
    conditions=['familyname'],
    misc_metadata={
        'priority': PriorityLevel.CRITICAL
    }
)
def org_sil_software_check_license_URLs(ttFont, familyname):
    """"License URL matches License text on name table?"""
    from fontbakery.constants import (NAMEID_LICENSE_DESCRIPTION,
                                      NAMEID_LICENSE_INFO_URL,
                                      PLACEHOLDER_LICENSING_TEXT)
    LICENSE_URL = {
        'OFL.txt': 'http://scripts.sil.org/OFL',
    }
    LICENSE_NAME = {
        'OFL.txt': 'SIL Open Font License',
    }
    detected_license = False
    for license in ['OFL.txt', 'COPYING', 'LICENSE.txt']:
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


@check(
    id='org.sil.software/check/versions',
    rationale=''' foo ''',
    conditions=[],
    misc_metadata={
        'priority': PriorityLevel.CRITICAL
    }
)
def org_sil_software_check_versions(ttFonts):
    """Make sure all font files have the same version value."""
    all_detected_versions = []
    fontfile_versions = {}
    for ttFont in ttFonts:
      v = ttFont['head'].fontRevision
      fontfile_versions[ttFont] = v

      if v not in all_detected_versions:
        all_detected_versions.append(v)
    if len(all_detected_versions) != 1:
      versions_list = ""
      for v in fontfile_versions.keys():
        versions_list += "* {}: {}\n".format(v.reader.file.name,
                                             fontfile_versions[v])
      yield WARN, ("version info differs among font"
                   " files of the same font project.\n"
                   "These were the version values found:\n"
                   "{}").format(versions_list)
    else:
      yield PASS, "All font files have the same version."


check(
    id='org.sil.software/check/os2',
    rationale=''' foo ''',
    conditions=['style'],
    misc_metadata={
        'priority': PriorityLevel.CRITICAL
    }
)


def org_sil_software_check_check_os2(ttFont, style):
    """Checking OS/2 fsSelection value."""
    from fontbakery.utils import check_bit_entry
    from fontbakery.constants import (STYLE_NAMES,
                                      RIBBI_STYLE_NAMES,
                                      FSSEL_REGULAR,
                                      FSSEL_ITALIC,
                                      FSSEL_BOLD)

    # Checking fsSelection REGULAR bit:
    expected = "Regular" in style or \
               (style in STYLE_NAMES and
                style not in RIBBI_STYLE_NAMES and
                "Italic" not in style)
    yield check_bit_entry(ttFont, "OS/2", "fsSelection",
                          expected,
                          bitmask=FSSEL_REGULAR,
                          bitname="REGULAR")

    # Checking fsSelection ITALIC bit:
    expected = "Italic" in style
    yield check_bit_entry(ttFont, "OS/2", "fsSelection",
                          expected,
                          bitmask=FSSEL_ITALIC,
                          bitname="ITALIC")

    # Checking fsSelection BOLD bit:
    expected = style in ["Bold", "BoldItalic"]
    yield check_bit_entry(ttFont, "OS/2", "fsSelection",
                          expected,
                          bitmask=FSSEL_BOLD,
                          bitname="BOLD")


@check(
    id='org.sil.software/check/name_table',
    rationale=''' foo ''',
    conditions=['style'],
    misc_metadata={
        'priority': PriorityLevel.IMPORTANT

    }
)
def org_sil_software_check_name_table(ttFont, style):
    """Font has all mandatory 'name' table entries?"""
    from fontbakery.utils import get_name_entry_strings
    from fontbakery.constants import (RIBBI_STYLE_NAMES,
                                      NAMEID_STR,
                                      NAMEID_FONT_FAMILY_NAME,
                                      NAMEID_FONT_SUBFAMILY_NAME,
                                      NAMEID_FULL_FONT_NAME,
                                      NAMEID_POSTSCRIPT_NAME,
                                      NAMEID_TYPOGRAPHIC_FAMILY_NAME,
                                      NAMEID_TYPOGRAPHIC_SUBFAMILY_NAME)
    required_nameIDs = [NAMEID_FONT_FAMILY_NAME,
                        NAMEID_FONT_SUBFAMILY_NAME,
                        NAMEID_FULL_FONT_NAME,
                        NAMEID_POSTSCRIPT_NAME]
    if style not in RIBBI_STYLE_NAMES:
      required_nameIDs += [NAMEID_TYPOGRAPHIC_FAMILY_NAME,
                           NAMEID_TYPOGRAPHIC_SUBFAMILY_NAME]
    failed = False
    # The font must have at least these name IDs:
    for nameId in required_nameIDs:
      if len(get_name_entry_strings(ttFont, nameId)) == 0:
        failed = True
        yield FAIL, ("Font lacks entry with"
                     " nameId={} ({})").format(nameId,
                                               NAMEID_STR[nameId])
    if not failed:
      yield PASS, "Font contains values for all mandatory name table entries."


def check_skip_filter(checkid, font=None, **iterargs):
    if font and checkid in (
        'com.google.fonts/check/035'  # Checking correctness of monospaced metadata.
        ,'com.google.fonts/check/036'  # Does GPOS table have kerning information?
        ,'com.google.fonts/check/037'  # Font has all expected currency sign characters?
    ):
     return False, ('skip')

    return True, None


specification.check_skip_filter = check_skip_filter

specification.auto_register(globals())


# FIXME: use logging.info or remove?
for section_name, section in specification._sections.items():
  print ("{} checks on {}".format(len(section._checks), section_name))
