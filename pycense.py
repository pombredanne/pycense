#! /usr/bin/python
###############################################################################
# Copyright (c) 2013 Charlie Pashayan                                         #
#                                                                             #
# Permission is hereby granted, free of charge, to any person obtaining a     #
# copy of this software and associated documentation files (the "Software"),  #
# to deal in the Software without restriction, including without limitation   #
# the rights to use, copy, modify, merge, publish, distribute, sublicense,    #
# and/or sell copies of the Software, and to permit persons to whom the       #
# Software is furnished to do so, subject to the following conditions:        #
#                                                                             #
# The above copyright notice and this permission notice shall be included in  #
# all copies or substantial portions of the Software.                         #
#                                                                             #
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR  #
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,    #
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE #
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER      #
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING     #
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER         #
# DEALINGS IN THE SOFTWARE.                                                   #
###############################################################################

import os
import objects as obj
import argparse
import ConfigParser
import re
import shutil
import tempfile
from pprint import pformat, pprint
from datetime import datetime

cwd = os.path.dirname(os.path.abspath(__file__)) + os.sep

def name_to_path(name):
    """Creates a path to a license out of its name."""
    return cwd + "licenses" + os.sep + name + ".txt"

def terminate(code):
    """Store modified config settings and exit."""
    with open(cwd + config_file, "wb") as fp:
        config.write(fp)
    os._exit(code)

config_file = "config.conf"

config = ConfigParser.ConfigParser()
config.read(cwd + config_file)

sample_text = "Software license information goes here."

d_license = config.get("defaults", "license")
d_company = config.get("defaults", "company")
d_owner = config.get("defaults", "owner")
d_editor = config.get("defaults", "editor")
d_settings = {"tab": config.getint("defaults", "tab"),
              "width": config.getint("defaults", "width"),
              "skip_line": config.getint("defaults", "skip_line"),
              "buffer_size": config.getint("defaults", "buffer_size")}
default_key = {"l": "license", "c": "company", "o": "owner", "t": "tab", 
               "w": "width", "mn": "magic_number", "e": "editor", 
               "bs": "buffer_size"}
seeables = ["all", "defaults", "profiles", "licenses", "sample"]

parser = argparse.ArgumentParser(description = \
                                     ("A friendly and modifiable program for "
                                      "slipping copyright notices into your "
                                      "source code."))
setattr(parser, "d_settings", d_settings)
setattr(parser, "default_key", default_key)
setattr(parser, "seeables", seeables)

# loading named entities
parser.add_argument("--profile", "-p", type = str,
                    help = "the comment style profile to load")
parser.add_argument("--license", "-l", type = str, 
                    action = obj.LicenseTypeAction, dest = "license",
                    help = ("license to load; default is %s"
                            % d_license))
parser.add_argument("--force_apply", "-fa", action = "store_true", 
                    default = False,
                    help = ("apply license to files even if no profile "
                            "or explicit settings are loaded"))

# settings
parser.add_argument("--tab", "-t", type = int, action = obj.SetAction,
                    dest = "settings", default = {},
                    help = ("tab width of document (there shoulldn't be any "
                            "tabs in your license"))
parser.add_argument("--width", "-w", type = int, action = obj.SetAction,
                    default = d_settings["width"], dest = "settings", 
                    help = ("maximum line width in source code"))
parser.add_argument("--top_begin", "-tb", type = str, action = obj.SetAction,
                    dest = "settings", default = {},
                    help = ("start of string marking the upper boundary of "
                            "commented license"))
parser.add_argument("--top_fill", "-tf", type = str, action = obj.SetAction,
                    dest = "settings", default = {},
                    help = ("string to repeat along the upper boundary of "
                            "commented license"))
parser.add_argument("--top_ljust", "-tl", type = str, action = obj.SetAction,
                    dest = "settings", default = {},
                    help = ("whether to left justify the fill along the "
                            "upper boundary of the commented license; "
                            "use True or False"))
parser.add_argument("--top_end", "-te", type = str, action = obj.SetAction,
                    dest = "settings", default = {},
                    help = ("end of string marking the upper boundary of "
                            "commented license"))
parser.add_argument("--left_wall", "-lw", type = str, action = obj.SetAction,
                    dest = "settings", default = {},
                    help = ("left wall of commented license; surrounds "
                            "text of licesne; include any spaces desired as "
                            "buffer"))
parser.add_argument("--right_wall", "-rw", type = str, action = obj.SetAction,
                    dest = "settings", default = {},
                    help = ("right wall of commented license; surrounds "
                            "text of licesne; include any spaces desired as "
                            "buffer"))
parser.add_argument("--bottom_begin", "-bb", type = str, dest = "settings", 
                    default = {}, action = obj.SetAction,
                    help = ("start of string marking the lower boundary of "
                            "commented license"))
parser.add_argument("--bottom_fill", "-bf", type = str, action = obj.SetAction,
                    dest = "settings", default = {},
                    help = ("string to repeat along the lower boundary of "
                            "commented license"))
parser.add_argument("--bottom_ljust", "-bl", type = str, dest = "settings",
                    default = {}, action = obj.SetAction,
                    help = ("whether to left justify the fill along the "
                            "lower boundary of the commented license; "
                            "use True or False"))
parser.add_argument("--bottom_end", "-be", type = str, action = obj.SetAction,
                    dest = "settings", default = {},
                    help = ("end of string marking the lower boundary of "
                            "commented license"))
parser.add_argument("--skip_line", "-sl", type = int, dest = "settings", 
                    default = {}, action = obj.SetAction,
                    help = ("number of lines to skip, if possible, "
                            "before inserting the copyright notice; use this "
                            "to hop over shebangs and other magic numbers"))
parser.add_argument("--buffer_size", "-bs", type = int, dest = "settings",
                    default = {}, action = obj.SetAction,
                    help = ("number of blank lines to use as a buffer both "
                            "above and below the commented license"))

# storing and managing named entities
parser.add_argument("--store_in_place", "-sip", action = 'store_true', 
                    default = False,
                    help = ("overwrite the named comment profile currently "
                            "loaded with the substitutions currently made"))
parser.add_argument("--store_as", "-sa", type = str, metavar = "NAME",
                    help = ("name to store currently loaded comment "
                            "profile under"))
parser.add_argument("--rename_profile", "-rp", type = str, nargs = "+",
                    metavar = ("OLD", "NEW"), default = [],
                    action = obj.RenameAction,
                    help = ("rename a named profile"))
parser.add_argument("--remove_profile", "-rmp", type = str, nargs = "+",
                    metavar = "PROFILE", default = [],
                    help = "remove these profiles from the library")
parser.add_argument("--import_license", "-il", type = str, nargs = "+",
                    action = obj.ImportAction, dest = "imports", default = [],
                    metavar = ("FILE", "LICENSE_NAME"), 
                    help = ("import a file into the license library"))
parser.add_argument("--rename_license", "-rl", type = str, nargs = "+",
                    metavar = ("OLD", "NEW"), default = [],
                    action = obj.RenameAction,
                    help = ("rename a named license"))
parser.add_argument("--remove_license", "-rml", type = str, nargs = "+",
                    metavar = "LICENSE", default = [],
                    help = "remove these licenses from the library")
parser.add_argument("--edit_license", "-el", type = str, nargs = "+",
                    default = [],
                    help = ("open up a license by name to edit using the "
                            "editor specified on the command line or in the "
                            "defaults; note that imports and renames are "
                            "performed before editing"))
parser.add_argument("--editor", "-e", type = str, default = d_editor,
                    help = ("editor to use for editing the license this time; "
                            "%s by defaults" % d_editor))

# setting defaults
parser.add_argument("--default_license", "-dl", type = str,
                    metavar = "LICENSE", action = obj.DefaultAction,
                    dest = "defaults", default = [],
                    help = ("set a previously imported license as default"))
parser.add_argument("--default_company", "-dc", type = str,
                    metavar = "COMPANY", action = obj.DefaultAction,
                    dest = "defaults", default = [],
                    help = ("set default company"))
parser.add_argument("--default_owner", "-do", type = str,
                    metavar = "OWNER", action = obj.DefaultAction,
                    dest = "defaults", default = [],
                    help = ("set list of default copyright holders"))
parser.add_argument("--default_tab", "-dt", type = int, dest = "defaults",
                    default = [], action = obj.DefaultAction, 
                    help = ("default tab width to use in all source code"))
parser.add_argument("--default_width", "-dw", type = int, dest = "defaults",
                    action = obj.DefaultAction, default = [],
                    help = ("default line width to use in all source code"))
parser.add_argument("--default_skip_line", "-dmn", type = str, 
                    action = obj.DefaultAction, nargs = "+", dest = "defaults",
                    default = [],
                    help = ("set default number of lines to skip; added for "
                            "completeness; you probably shouldn't use it"))
parser.add_argument("--default_buffer_size", "-dbs", type = int,
                    action = obj.DefaultAction, dest = "defaults",
                    default = [],
                    help = ("set default number of blank lines to use as "
                            "buffers around the commented license"))
parser.add_argument("--default_editor", "-de", type = str,
                    action = obj.DefaultAction, dest = "defaults",
                    help = ("text editor to use when opening licenses to "
                            "edit."))

# set one time substitutions
parser.add_argument("--year", "-y", type = str,
                    help = ("replace <year> with this once"))
parser.add_argument("--company", "-c", type = str,
                    help = ("replace <company> with this once"))
parser.add_argument("--owner", "-o", type = str,
                    help = ("replace <owner> with this once"))
parser.add_argument("--value", "-v", type = str, nargs = '+', default = [],
                    action = obj.ValueAdded, metavar = ("OLD", "NEW"),
                    help = ("replace <OLD> with NEW once"))
parser.add_argument("--no_substitution", "-ns", action = "store_true",
                    default = False, 
                    help = ("don't perform any substitutions of "
                            "<brocketed fields>"))

# produce commented licenses and either write to file or view
parser.add_argument("--apply_to", "-a", type = str, nargs = "+",
                    metavar = "SOURCE", default = [],
                    help = ("a list of source files to apply the current "
                            "settings to"))
parser.add_argument("--see", "-s", type = str, action = obj.SeeSomeAction,
                    nargs = "+", metavar = "SEEABLE", dest = "must_see",
                    default = [],
                    help = ("see some information; options include defaults, "
                            "profiles, licenses and sample, which means that "
                            "the currently selected license will be printed "
                            "to the screen using the currently selected "
                            "comment profile"))
args = parser.parse_args()
# remove stuff
for toremove in args.remove_license:
    try:
        os.remove(name_to_path(toremove))
    except OSError as err:
        if err.errno == 2:
            # fail silently unless --silent, --verbose  support added
            pass
for toremove in args.remove_profile:
    try:
        assert config.remove_option("profiles", toremove) == True
    except AssertionError:
        # fail silently unless --silent, --verbose  support added
        pass

# import and rename stuff
for filepath, newname in args.imports:
    shutil.copy(filepath, name_to_path(newname))
for old, new in args.rename_profile:
    olddata = config.get("profiles", old)
    if olddata:
        config.set("profiles", new, config.get("profiles", old))
        config.remove_option("profiles", old)
for old, new in args.rename_license:
    try:
        os.rename(name_to_path(old), name_to_path(new))
    except OSError as err:
        if err.errno == 2:
            pass
        
# adjust defaults
for name, value in args.defaults:
    config.set("defaults", name, value)

# edit licenses
for license_file in args.edit_license:
    path = name_to_path(license_file)
    if not args.editor:
        print "No editor designated"
        terminate(1)
    if os.path.exists(path):
        os.system("%s %s" % (args.editor, path))
    else:
        print "No license named %s found." % (license_file)
        terminate(1)

# load license if needed
if args.apply_to or "sample" in args.must_see:
    # load license
    if not args.license:
        args.license = d_license
    if args.license:
        license_file = name_to_path(args.license)
        try:
            license_text = open(license_file, "r").read().rstrip("\n")
        except:
            print "No license named '%s' found" % (args.license)
            terminate(1)
    else:
        print "No license known or knowable."
        terminate(1)
    if not args.no_substitution:
        # swap in replacements in the text
        args.value.append(("owner", args.owner if args.owner else d_owner))
        args.value.append(("company", 
                            args.company if args.company else d_company))
        args.value.append(("year", 
                           args.year if args.year else datetime.now().year))
        # an even number of backslashes doesn't affect substitution
        pieces = license_text.split("\\\\")
        for old, new in args.value:
            # make all substitutions unless brocket preceded by a backslash
            pieces = [re.sub(r"(?<!\\)<%s>" % old, str(new), piece) 
                      for piece in pieces]
        pieces = [re.sub(r"\\(?P<brocketed>\<.*?\>)", "\g<brocketed>", piece)
                  for piece in pieces]
        # replace doubled backslashes, throughing first of every pair away
        license_text = "\\".join(pieces)

# load profile if needed
must_store = args.store_as or args.store_in_place
if args.apply_to or "sample" in args.must_see or must_store:
    # create Commentator
    if args.profile:
        # load settings from named profile
        try:
            settings = eval(config.get("profiles", str(args.profile)))
        except ConfigParser.NoOptionError:
            print "No settings profile named %s" % (args.profile)
            terminate(1)
    else:
        settings = {}
    for setting in args.settings:
        # swap in any settings explicitly set in the cmdline
        settings[setting] = args.settings[setting]
    for setting in d_settings:
        # only swap in default settings if not set elsewhere
        if setting not in settings:
            settings[setting] = d_settings[setting]
    com = obj.Commentator(settings)

# manage named profiles
if args.store_in_place:
    if args.profile:
        config.set("profiles", args.profile, com.get_storage())
    else:
        print "Can't store in place because o named profile specified."
        terminate(1)
if args.store_as:
    config.set("profiles", args.store_as, com.get_storage())

# see what must be seen
if "defaults" in args.must_see:
    for var, val in config.items("defaults"):
        print "default %s: %s" % (var, val)
if "licenses" in args.must_see:
    for filename in os.listdir("./licenses"):
        print "license: %s" % (filename)
if "profiles" in args.must_see:
    for var, val in config.items("profiles"):
        print "profile: %s" % (var)
        # get rid of braces
        dicstr = pformat(eval(val)).replace("{", " ")[:-1]
        for line in dicstr.split("\n"):
            # get rid of single quotes around the data member names
            line = line.replace("'", "")
            line = line.replace("'", "")
            line = line.lstrip(" ")
            print "\t%s" % (line)
if "sample" in args.must_see:
    print com.get_boxed(license_text)

# modify the files
if any([args.profile, args.settings, args.force_apply]):
    for filename in args.apply_to:
        fin = open(filename, "r")
        fout = tempfile.NamedTemporaryFile(prefix = "tmp%s" % filename, 
                                           dir = ".", suffix = "txt", 
                                           delete = False)
        for i in range(com.skip_line):
            line = fin.readline()
            fout.write(line)
        fout.write(com.get_boxed(license_text) + "\n")
        for line in fin.readlines():
            fout.write(line)
        fout.flush()
        os.rename(fout.name, filename)
        fout.close
else:
    if args.apply_to:
        print ("To write to a file, you must either specify a comment "
               "profile, explicitly set some commenting settings, or use "
               "the flag --force_apply")
        terminate(1)

terminate(0)
