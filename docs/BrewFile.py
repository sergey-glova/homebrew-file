#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Brew-file: Manager for packages of Homebrew
https://github.com/rcmdnk/homebrew-file

requirement: Python 2.7 or later
"""

from __future__ import print_function

import os
import sys

__prog__ = os.path.basename(__file__)
__description__ = __doc__
__author__ = "rcmdnk"
__copyright__ = "Copyright (c) 2013 rcmdnk"
__credits__ = ["rcmdnk"]
__license__ = "MIT"
__version__ = "v5.1.0"
__date__ = "5/Jan/2018"
__maintainer__ = "rcmdnk"
__email__ = "rcmdnk@gmail.com"
__status__ = "Prototype"


def my_decode(word):  # pragma: no cover
    """Decode when python3 is used."""

    if sys.version_info.major > 2:
        return word.decode()

    return word


def my_input(word):  # pragma: no cover
    """Input method compatibility."""

    if sys.version_info.major > 2:
        return input(word)

    return raw_input(word)


def open_output_file(name, mode="w"):
    """Helper function to open a file even if it doesn't exist."""
    if os.path.dirname(name) != "" and \
            not os.path.exists(os.path.dirname(name)):
        os.makedirs(os.path.dirname(name))
    return open(name, mode)


def to_bool(val):
    if type(val) == bool:
        return val
    elif type(val) == int or (type(val) == str and val.isdigit()):
        return bool(int(val))
    elif type(val) == str:
        if val.lower() == "true":
            return True
        else:
            return False
    else:  # pragma: no cover
        return False


class Tee:
    """Module to write out in two ways at once."""

    def __init__(self, out1, out2=sys.stdout, use2=True):
        """__init__"""

        try:
            from cStringIO import StringIO
        except ImportError:  # pragma: no cover
            from io import StringIO
        if type(out1) == str:
            self.out1name = out1
            self.out1 = StringIO()
        else:
            self.out1name = ""
            self.out1 = out1
        self.use2 = use2
        if self.use2:
            if type(out2) == str:
                self.out2name = out2
                self.out2 = StringIO()
            else:
                self.out2name = ""
                self.out2 = out2

    def __del__(self):
        """__del__"""

        if self.out1name != "":
            self.out1.close()
        if self.use2:
            if self.out2name != "":
                self.out2.close()

    def write(self, text):
        """Write w/o line break."""

        self.out1.write(text)
        if self.use2:
            self.out2.write(text)

    def writeln(self, text):
        """Write w/ line break."""

        self.out1.write(text + "\n")
        if self.use2:
            self.out2.write(text + "\n")

    def flush(self):
        """Flush the output"""

        self.out1.flush()
        if self.use2:
            self.out2.flush()

    def close(self):
        """Close output files."""

        if self.out1name != "":
            f = open_output_file(self.out1name, "w")
            f.write(self.out1.getvalue())
            f.close()
        if self.use2:
            if self.out2name != "":
                f = open(self.out2name, "w")
                f.write(self.out2.getvalue())
                f.close()
        self.__del__()


class BrewHelper:
    """Helper functions for BrewFile."""

    def __init__(self, opt):
        self.opt = opt

    def readstdout(self, proc):
        while True:
            line = my_decode(proc.stdout.readline()).rstrip()
            code = proc.poll()
            if line == '':
                if code is not None:
                    break
                else:  # pragma: no cover
                    continue
            yield line

    def proc(self, cmd, print_cmd=True, print_out=True,
             exit_on_err=True, separate_err=False, print_err=True, shell=False,
             verbose=1, env={}):
        """ Get process output."""
        import shlex
        import subprocess
        if type(cmd) != list:
            cmd = shlex.split(cmd)
        cmd_orig = " ".join(["$"] + cmd)
        if cmd[0] == "brew":
            cmd = ["command"] + cmd
        if print_cmd:
            self.info(cmd_orig, verbose)
        if shell:
            cmd = ' '.join(cmd)
        all_env = os.environ.copy()
        for k, v in env.items():
            all_env[k] = v
        lines = []
        try:
            if separate_err:
                if print_err:
                    stderr = None
                else:
                    stderr = open(os.devnull, 'w')
            else:
                stderr = subprocess.STDOUT
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=stderr,
                                 env=all_env, shell=shell)
            if separate_err and not print_err:
                stderr.close()
            for line in self.readstdout(p):
                lines.append(line)
                if print_out:
                    self.info(line, verbose)
            ret = p.wait()
        except OSError as e:
            if print_out:
                lines = [" ".join(cmd) + ": " + str(e)]
                self.info(lines[0].strip(), verbose)
            ret = -1

        if exit_on_err and ret != 0:
            if not (print_out and self.opt["verbose"] >= verbose):
                print("\n".join(lines))
            sys.exit(ret)

        return (ret, lines)

    def info(self, text, verbose=2):
        if self.opt["verbose"] < verbose:
            return
        print(text)

    def warn(self, text, verbose=1):
        self.info("\033[33;1m" + text + "\033[m", verbose)

    def err(self, text, verbose=0):
        self.info("\033[31;1m" + text + "\033[m", verbose)

    def banner(self, text, verbose=1):
        max = 0
        for l in text.split("\n"):
            if max < len(l):
                max = len(l)
        self.info("\n"+"#"*max+"\n"+text+"\n" + "#"*max+"\n", verbose)

    def brew_val(self, name):
        if name not in self.opt:
            self.opt[name] = self.proc("brew --" + name, False, False)[1][0]
        return self.opt[name]


class BrewInfo:
    """Homebrew information storage."""

    def __init__(self, helper, filename=""):

        self.brew_input_opt = {}
        self.pip_input_opt = {}
        self.gem_input_opt = {}

        self.brew_input = []
        self.tap_input = []
        self.cask_input = []
        self.pip_input = []
        self.gem_input = []
        self.appstore_input = []
        self.file_input = []

        self.before_input = []
        self.after_input = []
        self.cmd_input = []

        self.brew_list_opt = {}
        self.pip_list_opt = {}
        self.gem_list_opt = {}

        self.brew_list = []
        self.tap_list = []
        self.cask_list = []
        self.pip_list = []
        self.gem_list = []
        self.appstore_list = []
        self.file_list = []

        self.tap_packs = []
        self.tap_casks = []
        self.cask_nocask_list = []

        self.list_dic = {
            "brew_input_opt": self.brew_input_opt,
            "pip_input_opt": self.pip_input_opt,
            "gem_input_opt": self.gem_input_opt,
            "brew_input": self.brew_input,
            "tap_input": self.tap_input,
            "cask_input": self.cask_input,
            "pip_input": self.pip_input,
            "gem_input": self.gem_input,
            "appstore_input": self.appstore_input,
            "file_input": self.file_input,
            "before_input": self.before_input,
            "after_input": self.after_input,
            "cmd_input": self.cmd_input,
            "brew_list_opt": self.brew_list_opt,
            "pip_list_opt": self.pip_list_opt,
            "gem_list_opt": self.gem_list_opt,
            "brew_list": self.brew_list,
            "tap_list": self.tap_list,
            "cask_list": self.cask_list,
            "cask_nocask_list": self.cask_nocask_list,
            "pip_list": self.pip_list,
            "gem_list": self.gem_list,
            "appstore_list": self.appstore_list,
            "file_list": self.file_list,
            "tap_packs": self.tap_packs,
            "tap_casks": self.tap_casks,
        }
        self.filename = filename
        self.helper = helper

    def set_file(self, filename):
        self.filename = filename

    def get_file(self):
        return self.filename

    def get_dir(self):
        return os.path.dirname(self.filename)

    def check_file(self):
        if os.path.exists(self.filename):
            return True
        else:
            return False

    def check_dir(self):
        if os.path.exists(self.get_dir()):
            return True
        else:
            return False

    def clear(self):
        self.clear_input()
        self.clear_list()

        del self.tap_packs[:]
        del self.tap_casks[:]

    def clear_input(self):
        self.brew_input_opt.clear()
        self.pip_input_opt.clear()
        self.gem_input_opt.clear()

        del self.brew_input[:]
        del self.tap_input[:]
        del self.cask_input[:]
        del self.pip_input[:]
        del self.gem_input[:]
        del self.appstore_input[:]
        del self.file_input[:]

        del self.before_input[:]
        del self.after_input[:]
        del self.cmd_input[:]

    def clear_list(self):
        self.brew_list_opt.clear()
        self.pip_list_opt.clear()
        self.gem_list_opt.clear()

        del self.brew_list[:]
        del self.tap_list[:]
        del self.cask_list[:]
        del self.cask_nocask_list[:]
        del self.pip_list[:]
        del self.gem_list[:]
        del self.appstore_list[:]
        del self.file_list[:]

    def input_to_list(self):
        self.clear_list()
        self.brew_list.extend(self.brew_input)
        self.brew_list_opt.update(self.brew_input_opt)
        self.pip_list_opt.update(self.pip_input_opt)
        self.gem_list_opt.update(self.gem_input_opt)
        self.tap_list.extend(self.tap_input)
        self.cask_list.extend(self.cask_input)
        self.pip_list.extend(self.pip_input)
        self.gem_list.extend(self.gem_input)
        self.appstore_list.extend(self.appstore_input)
        self.file_list.extend(self.file_input)

    def sort(self):
        core = 0
        homebrew_taps = []
        cask = 0
        cask_taps = []
        other_taps = []
        for t in self.tap_list:
            if t == "homebrew/core":
                core = 1
            elif t in ["caskroom/cask", "homebrew/cask"]:
                cask = 1
            elif t.startswith("homebrew/"):
                homebrew_taps.append(t)
            elif t.startswith("caskroom/"):
                cask_taps.append(t)
            else:
                other_taps.append(t)
        homebrew_taps.sort()
        cask_taps.sort()
        other_taps.sort()
        self.tap_list = []
        if core == 1:
            self.tap_list.append("homebrew/core")
        self.tap_list += homebrew_taps
        if cask == 1:
            self.tap_list.append("homebrew/cask")
        self.tap_list += cask_taps
        self.tap_list += other_taps

        self.brew_list.sort()
        self.tap_casks.sort()
        self.gem_list.sort()

        self.appstore_list.sort(
            key=lambda x: x.split()[1].lower() if len(x.split()) > 1
            else x.split()[0])

    def get(self, name):
        import copy
        return copy.deepcopy(self.list_dic[name])

    def remove(self, name, package):
        if type(self.list_dic[name]) == list:
            self.list_dic[name].remove(package)
        elif type(self.list_dic[name]) == dict:
            del self.list_dic[name][package]

    def set_val(self, name, val):
        if type(self.list_dic[name]) == list:
            del self.list_dic[name][:]
            self.list_dic[name].extend(val)
        elif type(self.list_dic[name]) == dict:
            self.list_dic[name].clear()
            self.list_dic[name].update(val)

    def add(self, name, val):
        if type(self.list_dic[name]) == list:
            self.list_dic[name].extend(val)
        elif type(self.list_dic[name]) == dict:
            self.list_dic[name].update(val)

    def read(self, filename=""):
        self.clear_input()

        try:
            if filename == "":
                f = open(self.filename, "r")
            else:
                f = open(filename, "r")
        except IOError:
            return False

        lines = f.readlines()
        f.close()
        import re
        is_ignore = False
        self.tap_input.append("direct")
        for l in lines:
            if re.match("# *BREWFILE_ENDIGNORE", l):
                is_ignore = False
            if re.match("# *BREWFILE_IGNORE", l):
                is_ignore = True
            if is_ignore:
                continue
            if re.match(" *$", l) is not None or\
                    re.match(" *#", l) is not None:
                continue
            args = l.replace("'", "").replace('"', "").\
                replace(",", " ").replace("[", "").replace("]", "")
            args = self.helper.proc('echo \\"' + args + '\\"', False, False,
                                    False, True, True, shell=True
                                    )[1][0].split()
            cmd = args[0]
            p = args[1] if len(args) > 1 else ""
            if len(args) > 2 and p in ["tap", "cask", "pip", "gem"]:
                args.pop(0)
                cmd = args[0]
                p = args[1]
                if self.helper.opt["form"] == "none":
                    self.helper.opt["form"] = "cmd"
            if len(args) > 2 and cmd in ["brew", "cask", "gem"] and \
                    p == "install":
                args.pop(1)
                p = args[1]
                if self.helper.opt["form"] == "none":
                    self.helper.opt["form"] = "cmd"

            if len(args) > 2:
                if args[2] == "args:":
                    opt = " " + " ".join(["--" + x for x in args[3:]]).strip()
                    if self.helper.opt["form"] == "none":
                        self.helper.opt["form"] = "bundle"
                else:
                    opt = " " + " ".join(args[2:]).strip()
            else:
                opt = ""
            excmd = " ".join(l.split()[1:]).strip()

            if self.helper.opt["form"] == "none":
                if cmd in ["brew", "tap", "tapall", "pip", "gem"]:
                    if '"' in l or "'" in l:
                        self.helper.opt["form"] = "bundle"

            if cmd == "brew" or cmd == "install":
                self.brew_input.append(p)
                self.brew_input_opt[p] = (opt)
            elif cmd == "tap":
                self.tap_input.append(p)
            elif cmd == "tapall":
                self.tap_input.append(p)
                self.get_tap(p)
                for tp in self.tap_packs:
                    self.brew_input.append(tp)
                    self.brew_input_opt[tp] = ""
            elif cmd == "cask":
                self.cask_input.append(p)
            elif cmd == "pip":
                self.pip_input.append(p)
                self.pip_input_opt[p] = (opt)
            elif cmd == "gem":
                self.gem_input.append(p)
                self.gem_input_opt[p] = (opt)
            elif cmd == "appstore":
                self.appstore_input.append(re.sub("^ *appstore *", "", l).
                                           strip().strip("'").strip('"'))
            elif cmd == "file" or cmd.lower() == "brewfile":
                self.file_input.append(p)
            elif cmd == "before":
                self.before_input.append(excmd)
            elif cmd == "after":
                self.after_input.append(excmd)
            else:
                self.cmd_input.append(l.strip())

    def get_tap_path(self, tap):
        """Get tap path"""
        if tap == "direct":
            return self.helper.brew_val("cache") + "/Formula"

        tap_user = os.path.dirname(tap)
        tap_repo = os.path.basename(tap)
        return self.helper.brew_val("repository") + "/Library/Taps" +\
            "/" + tap_user + "/homebrew-" + tap_repo

    def get_tap(self, tap):
        """Helper for tap configuration file"""
        tap_path = self.get_tap_path(tap)
        if not os.path.isdir(tap_path):
            return
        self.set_val("tap_packs", list(map(lambda x: x.replace(".rb", ""),
                                           filter(lambda y: y.endswith(".rb"),
                                                  os.listdir(tap_path)))))
        path = tap_path + "/Formula"
        if os.path.isdir(path):
            self.add("tap_packs", list(map(lambda x: x.replace(".rb", ""),
                                           filter(lambda y: y.endswith(".rb"),
                                                  os.listdir(path)))))
        path = tap_path + "/Casks"
        if os.path.isdir(path):
            self.set_val("tap_casks",
                         list(map(lambda x: x.replace(".rb", ""),
                                  filter(lambda y: y.endswith(".rb"),
                                         os.listdir(tap_path + "/Casks")))))

    def packout(self, pack):
        if self.helper.opt["form"] in ["brewdler", "bundle"]:
            return "'" + pack + "'"
        else:
            return pack

    def get_leaves(self):
        leavestmp = self.helper.proc("brew leaves", False, False)[1]
        leaves = []
        for l in leavestmp:
            leaves.append(l.split("/")[-1])
        return leaves

    def get_info(self, package=""):
        if package == "":
            package = "--installed"
        import json
        infotmp = json.loads(
            self.helper.proc("brew info --json=v1 " + package, False, False,
                             True, True)[1][0])
        info = {}
        for i in infotmp:
            info[i["name"]] = i
        return info

    def get_installed(self, package, package_info=""):
        """get installed version of brew package"""
        if type(package_info) != dict:  # pragma: no cover
            package_info = self.get_info(package)[package]

        installed = {}
        version = ""
        if package_info["linked_keg"] is None:
            version = self.helper.proc("ls -l " +
                                       self.helper.brew_val("prefix") +
                                       "/opt/" + package,
                                       False, False, False, False)[1][0]
            version = version.split("/")[-1]
            if "No such file or directory" in version:
                version = ""
        else:
            version = package_info["linked_keg"]

        if version == "":
            installed = package_info["installed"][0]
        else:
            for i in package_info["installed"]:
                if i["version"] == version:
                    installed = i
                    break
        return installed

    def get_option(self, package, package_info=""):
        """get install options from brew info"""

        # Get options for build
        if type(package_info) != dict:  # pragma: no cover
            package_info = self.get_info(package)[package]

        opt = ""
        installed = self.get_installed(package, package_info)
        if len(installed["used_options"]) > 0:
            opt = " " + " ".join(installed["used_options"])
        for k, v in package_info["versions"].items():
            if installed["version"] == v and k != "stable":
                if k == "head":
                    opt += " --HEAD"
                else:
                    opt += " --" + k
        return opt

    def convert_option(self, opt):
        if opt != "" and self.helper.opt["form"] in ["brewdler", "bundle"]:
            import re
            opt = ", args: [" + ", ".join(
                ["'" + re.sub("^--", "", x) + "'" for x in opt.split()]) + "]"
        return opt

    def write(self):
        # Prepare output
        out = Tee(self.get_file(), sys.stdout, self.helper.opt["verbose"] > 1)

        # commands for each format
        if self.helper.opt["form"] in ["file", "none"]:
            cmd_before = "before "
            cmd_after = "after "
            cmd_other = ""
            cmd_install = "brew "
            cmd_tap = "tap "
            cmd_cask = "cask "
            cmd_pip = "pip "
            cmd_gem = "gem "
            cmd_cask_nocask = "#cask "
            cmd_appstore = "appstore "
            cmd_file = "file "
        elif self.helper.opt["form"] in ["brewdler", "bundle"]:
            cmd_before = "#before "
            cmd_after = "#after "
            cmd_other = "#"
            cmd_install = "brew "
            cmd_tap = "tap "
            cmd_cask = "cask "
            cmd_pip = "#pip "
            cmd_gem = "#gem "
            cmd_cask_nocask = "#cask "
            cmd_appstore = "#appstore "
            cmd_file = "#file "
        elif self.helper.opt["form"] in ["command", "cmd"]:
            # Shebang for command format
            out.writeln("#!/usr/bin/env bash\n")
            out.writeln("#BREWFILE_IGNORE")
            out.writeln("if ! which brew >& /dev/null;then")
            out.writeln("  brew_installed=0")
            out.writeln("  echo Homebrew is not installed!")
            out.writeln("  echo Install now...")
            out.writeln("  echo ruby -e \\\"\$\(curl -fsSL "
                        "https://raw.githubusercontent.com/Homebrew/"
                        "install/master/install\)\\\"")
            out.writeln("  ruby -e \"$(curl -fsSL "
                        "https://raw.githubusercontent.com/Homebrew/"
                        "install/master/install)\"")
            out.writeln("  echo")
            out.writeln("fi")
            out.writeln("#BREWFILE_ENDIGNORE")

            cmd_before = ""
            cmd_after = ""
            cmd_other = ""
            cmd_install = "brew install "
            cmd_tap = "brew tap "
            cmd_cask = "brew cask install "
            cmd_pip = "brew pip "
            cmd_gem = "brew gem install "
            cmd_cask_nocask = "#brew cask install "
            cmd_appstore = "#appstore "
            cmd_file = "#file "

        # sort
        self.sort()

        # Before commands
        if len(self.before_input) > 0:
            out.writeln("# Before commands")
            for c in self.before_input:
                out.writeln(cmd_before + c)

        # Taps
        if len(self.tap_list) > 0:
            isfirst = True

            def first_tap_write(out, isfirst):
                if isfirst:
                    out.writeln("\n# tap repositories and their packages")

            def first_tap_pack_write(out, isfirst, direct_first, isfirst_pack,
                                     tap, cmd_tap):
                first_tap_write(out, isfirst)
                if not direct_first and isfirst_pack:
                    out.writeln("\n" +
                                cmd_tap + self.packout(tap))

            for t in self.tap_list:
                isfirst_pack = True
                self.get_tap(t)
                direct_first = False
                if t == "direct":
                    direct_first = True

                if not self.helper.opt["caskonly"]:
                    first_tap_pack_write(out, isfirst, direct_first,
                                         isfirst_pack, t, cmd_tap)
                    isfirst = isfirst_pack = False

                    for p in self.brew_list[:]:
                        if p.split("/")[-1].replace(
                                ".rb", "") in self.tap_packs:
                            if direct_first:
                                direct_first = False
                                out.writeln("\n## " + "Direct install")
                            pack = self.packout(p) +\
                                self.convert_option(self.brew_list_opt[p])
                            out.writeln(cmd_install + pack)
                            self.brew_list.remove(p)
                            del self.brew_list_opt[p]
                for tc in self.tap_casks:
                    if tc in self.cask_list:
                        first_tap_pack_write(out, isfirst, False,
                                             isfirst_pack, t, cmd_tap)
                        isfirst = isfirst_pack = False
                        out.writeln(cmd_cask + self.packout(tc))
                        self.cask_list.remove(tc)

        # Brew packages
        if not self.helper.opt["caskonly"] and len(self.brew_list) > 0:
            out.writeln("\n# Other Homebrew packages")
            for p in self.brew_list:
                pack = self.packout(p) +\
                    self.convert_option(self.brew_list_opt[p])
                out.writeln(cmd_install + pack)

        # pip packages
        if not self.helper.opt["caskonly"] and len(self.pip_list) > 0:
            out.writeln("\n# Other pip packages")
            for p in self.pip_list:
                pack = self.packout(p)
                if len(self.pip_list_opt[p]) == 1:
                    pack = pack + "=" + self.pip_list_opt[p][0].strip()
                out.writeln(cmd_pip + pack)

        # gem packages
        if not self.helper.opt["caskonly"] and len(self.gem_list) > 0:
            out.writeln("\n# Other gem packages")
            for p in self.gem_list:
                pack = self.packout(p) + self.gem_list_opt[p]
                out.writeln(cmd_gem + pack)

        # Casks
        if len(self.cask_list) > 0:
            out.writeln("\n# Other Cask applications")
            for c in self.cask_list:
                out.writeln(cmd_cask + self.packout(c))

        # Installed by cask, but cask files were not found...
        if len(self.cask_nocask_list) > 0:  # pragma: no cover
            out.writeln("\n# Below applications were installed by Cask,")
            out.writeln("# but do not have corresponding casks.\n")
            for c in self.cask_nocask_list:
                out.writeln(cmd_cask_nocask + self.packout(c))

        # App Store applications
        if self.helper.opt["appstore"] and len(self.appstore_list) > 0:
            out.writeln("\n# App Store applications")
            for a in self.appstore_list:
                out.writeln(cmd_appstore + self.packout(a))

        # Additional files
        if len(self.file_list) > 0:
            out.writeln("\n# Additional files")
            for f in self.file_list:
                out.writeln(cmd_file + self.packout(f))

        # Other commands
        if len(self.cmd_input) > 0:
            out.writeln("\n# Other commands")
            for c in self.cmd_input:
                out.writeln(cmd_other + c)

        # After commands
        if len(self.after_input) > 0:
            out.writeln("\n# After commands")
            for c in self.after_input:
                out.writeln(cmd_after + c)

        # Close Brewfile
        out.close()

        # Change permission for exe/normal file
        if self.helper.opt["form"] in ["command", "cmd"]:
            self.helper.proc("chmod 755 %s" % self.get_file(), False, False,
                             False)
        else:
            self.helper.proc("chmod 644 %s" % self.get_file(), False, False,
                             False)


class BrewFile:

    """Main class of Brew-file."""

    def __init__(self):
        """initialization."""

        # Set default values
        self.opt = {}

        # Prepare helper, need verbose first
        self.opt["verbose"] = int(
            os.environ.get("HOMEBREW_BRWEFILE_VERBOSE", 1))
        self.helper = BrewHelper(self.opt)

        # First check Homebrew
        self.check_brew_cmd()

        # Other default values
        self.opt["command"] = ""
        self.opt["input"] = os.environ.get("HOMEBREW_BREWFILE", "")
        brewfile_config = os.environ["HOME"] + "/.config/brewfile/Brewfile"
        brewfile_home = os.environ["HOME"] + "/.brewfile/Brewfile"
        if self.opt["input"] == "":
            if not os.path.isfile(brewfile_config) and\
                    os.path.isfile(brewfile_home):
                self.opt["input"] = brewfile_home
            else:
                self.opt["input"] = brewfile_config
        self.opt["backup"] = os.environ.get("HOMEBREW_BREWFILE_BACKUP", "")
        self.opt["leaves"] = to_bool(
            os.environ.get("HOMEBREW_BREWFILE_LEAVES", False))
        self.opt["on_request"] = to_bool(
            os.environ.get("HOMEBREW_BREWFILE_ON_REQUEST", False))
        self.opt["top_packages"] = os.environ.get(
            "HOMEBREW_BREWFILE_TOP_PACKAGES", "")
        self.opt["form"] = "none"
        self.opt["repo"] = ""
        self.opt["noupgradeatupdate"] = False
        self.opt["link"] = True
        self.opt["caskonly"] = False
        self.opt["dryrun"] = True
        self.opt["initialized"] = False
        self.opt["cask_repo"] = "caskroom/cask"
        self.opt["reattach_formula"] = "reattach-to-user-namespace"
        self.opt["mas_formula"] = "mas"
        self.opt["pip_pack"] = "brew-pip"
        self.opt["gem_pack"] = "brew-gem"
        self.opt["my_editor"] = os.environ.get("EDITOR", "vim")
        self.opt["is_brew_cmd"] = False
        self.opt["is_cask_cmd"] = False
        self.opt["cask_cmd_installed"] = False
        self.opt["mas_cmd"] = "mas"
        self.opt["is_mas_cmd"] = 0
        self.opt["mas_cmd_installed"] = False
        self.opt["reattach_cmd_installed"] = False
        self.opt["is_pip_cmd"] = False
        self.opt["pip_cmd_installed"] = False
        self.opt["is_gem_cmd"] = False
        self.opt["gem_cmd_installed"] = False
        self.opt["args"] = []
        self.opt["yn"] = False
        self.opt["brew_packages"] = ""
        self.opt["homebrew_ruby"] = False

        cask_opts = self.parse_env_opts(
            "HOMEBREW_CASK_OPTS", {"--appdir": "", "--fontdir": ""})

        if not os.path.isdir(self.brew_val("prefix") + "/Caskroom") and\
                os.path.isdir(
                    "/opt/homebrew-cask/Caskroom"):  # pragma: no cover
            self.opt["caskroom"] = "/opt/homebrew-cask/Caskroom"
        else:
            self.opt["caskroom"] =\
                self.brew_val("prefix") + "/Caskroom"
        self.opt["appdir"] = cask_opts["--appdir"].rstrip("/") \
            if cask_opts["--appdir"] != ""\
            else os.environ["HOME"] + "/Applications"
        self.opt["appdirlist"] = ["/Applications",
                                  os.environ["HOME"] + "/Applications"]
        if self.opt["appdir"].rstrip("/") not in self.opt["appdirlist"]:
            self.opt["appdirlist"].append(self.opt["appdir"])
        self.opt["appdirlist"] += [x.rstrip("/") + "/Utilities"
                                   for x in self.opt["appdirlist"]]
        self.opt["appdirlist"] = [x for x in self.opt["appdirlist"]
                                  if os.path.isdir(x)]
        # fontdir may be used for application search, too
        self.opt["fontdir"] = cask_opts["--fontdir"]

        self.opt["appstore"] = to_bool(
            os.environ.get("HOMEBREW_BREWFILE_APPSTORE", True))

        gem_opts = self.parse_env_opts("HOMEBREW_GEM_OPTS")
        if "--homebrew-ruby" in gem_opts:  # pragma: no cover
            self.opt["homebrew_ruby"] = True

        self.int_opts = ["verbose"]
        self.float_opts = []

        self.brewinfo = BrewInfo(self.helper, self.opt["input"])
        self.brewinfo_ext = []
        self.opt["read"] = False

        self.pack_deps = {}
        self.top_packs = []

    def parse_env_opts(self, env_var, base_opts=None):
        """Returns a dictionary parsed from an environment variable"""

        if base_opts is not None:
            opts = base_opts.copy()
        else:
            opts = {}

        env_var = env_var.upper()
        env_opts = os.environ.get(env_var, None)
        if env_opts:

            # these can be flags ("--flag") or values ("--key=value")
            # but not weirdness ("--foo=bar=baz")
            user_opts = {key.lower(): value for (key, value) in
                         [pair.partition("=")[::2] for pair in env_opts.split()
                          if pair.count("=") < 2]}

            if user_opts:
                opts.update(user_opts)
            else:  # pragma: no cover
                self.warn("%s: \"%s\" is not a proper format." %
                          (env_var, env_opts), 0)
                self.warn("Ignoring the value.\n", 0)

        return opts

    def set_args(self, **kw):
        """Set arguments."""
        for k, v in kw.items():
            self.opt[k] = v

        for k in self.int_opts:
            self.opt[k] = int(self.opt[k])
        for k in self.float_opts:  # pragma: no cover
            self.opt[k] = float(self.opt[k])

        self.brewinfo.set_file(self.opt["input"])

    def ask_yn(self, question):  # pragma: no cover
        """Helper for yes/no."""
        if self.opt["yn"]:
            print(question + " [y/n]: y")
            return True

        yes = ["yes", "y", ""]
        no = ["no", "n"]

        yn = my_input(question + " [y/n]: ").lower()
        while True:
            if yn in yes:
                return True
            elif yn in no:
                return False
            else:
                yn = my_input("Answer with yes (y) or no (n): ").lower()

    def verbose(self):
        try:
            v = self.opt["verbose"]
        except:  # pragma: no cover
            v = 10
        return v

    def proc(self, cmd, print_cmd=True, print_out=True,
             exit_on_err=True, separate_err=False, print_err=True,
             verbose=1, env={"HOMEBREW_NO_AUTO_UPDATE": "1"}):
        return self.helper.proc(
            cmd=cmd, print_cmd=print_cmd, print_out=print_out,
            exit_on_err=exit_on_err, separate_err=separate_err,
            print_err=print_err, verbose=verbose, env=env)

    def info(self, text, verbose=2):
        self.helper.info(text, verbose)

    def warn(self, text, verbose=1):
        self.helper.warn(text, verbose)

    def err(self, text, verbose=1):
        self.helper.err(text, verbose)

    def banner(self, text, verbose=1):
        self.helper.banner(text, verbose)

    def remove(self, path):
        """Helper to remove file/directory."""
        import shutil
        if os.path.islink(path) or os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
        else:
            self.warn("Tried to remove non usual file/directory:" + path, 0)

    def brew_val(self, name):
        return self.helper.brew_val(name)

    def read_all(self, force=False):
        if not force and self.opt["read"]:
            return
        del self.brewinfo_ext[:]
        self.read(self.brewinfo)
        if self.opt["cask_cmd_installed"]:
            if not self.opt["cask_repo"] in self.get("tap_input"):
                self.brewinfo.tap_input.append(self.opt["cask_repo"])
        if self.opt["mas_cmd_installed"]:
            p = os.path.basename(self.opt["mas_formula"])
            if p not in self.get("brew_input"):
                self.brewinfo.brew_input.append(p)
                self.brewinfo.brew_input_opt[p] = ""
        if self.opt["reattach_cmd_installed"]:  # pragma: no cover
            p = os.path.basename(self.opt["reattach_formula"])
            if p not in self.get("brew_input"):
                self.brewinfo.brew_input.append(p)
                self.brewinfo.brew_input_opt[p] = ""
        if self.opt["pip_cmd_installed"]:  # pragma: no cover
            if not self.opt["pip_pack"] in self.get("brew_input"):
                self.brewinfo.brew_input.append(self.opt["pip_pack"])
                self.brewinfo.brew_input_opt[self.opt["pip_pack"]] = ""
        if self.opt["gem_cmd_installed"]:  # pragma: no cover
            if not self.opt["gem_pack"] in self.get("brew_input"):
                self.brewinfo.brew_input.append(self.opt["gem_pack"])
                self.brewinfo.brew_input_opt[self.opt["gem_pack"]] = ""
        self.opt["read"] = True

    def read(self, brewinfo):
        brewinfo.read()
        for f in brewinfo.get("file_input"):
            f = os.path.expandvars(os.path.expanduser(f))
            if os.path.isabs(f):
                b = BrewInfo(self.helper, f)
            else:
                b = BrewInfo(self.helper, brewinfo.get_dir() + "/" + f)
            self.brewinfo_ext.append(b)
            self.read(b)

    def input_to_list(self, only_ext=False):
        if not only_ext:
            self.brewinfo.input_to_list()
        for b in self.brewinfo_ext:
            b.input_to_list()

    def write(self):
        self.banner("# Initialize " + self.brewinfo.get_file())
        self.brewinfo.write()
        for b in self.brewinfo_ext:
            self.banner("# Initialize " + b.get_file())
            b.write()

    def get(self, name, only_ext=False):
        l = self.brewinfo.get(name)
        if type(l) == list:
            if only_ext:
                del l[:]
            for b in self.brewinfo_ext:
                l += b.get(name)
        elif type(l) == dict:
            if only_ext:
                l.clear()
            for b in self.brewinfo_ext:
                l.update(b.get(name))
        return l

    def remove_pack(self, name, package):
        if package in self.brewinfo.get(name):
            self.brewinfo.remove(name, package)
        else:  # pragma: no cover
            for b in self.brewinfo_ext:
                if package in b.get(name):
                    b.remove(name, package)

    def repo_name(self):
        return self.opt["repo"].split("/")[-1].split(".git")[0]

    def user_name(self):
        return self.opt["repo"].split("/")[-2].split(":")[-1]

    def input_dir(self):
        return os.path.dirname(self.opt["input"])

    def input_file(self):
        return self.opt["input"].split("/")[-1]

    def repo_file(self):
        """Helper to build Brewfile path for the repository."""
        return self.input_dir() + "/" +\
            self.user_name() + "_" + self.repo_name() + "/" + self.input_file()

    def init_repo(self):
        os.chdir(self.brewinfo.get_dir())
        branches = self.proc("git branch", False, False, True, True)[1]
        if len(branches) != 0:
            return

        self.info("Initialize the repository with README.md/Brewfile.", 1)
        self.info("$ cd " + self.brewinfo.get_dir(), 1)
        os.chdir(self.brewinfo.get_dir())
        if not os.path.exists("README.md"):
            f = open("README.md", "w")
            f.write(
                "# " + self.repo_name() + "\n\n"
                "Package list for [homebrew](http://brew.sh/).\n\n"
                "Managed by "
                "[homebrew-file](https://github.com/rcmdnk/homebrew-file).")
            f.close()
        open(self.brewinfo.get_file(), "a").close()

        if self.check_gitconfig():
            self.proc("git add -A")
            self.proc(["git", "commit", "-m",
                       "\"Prepared by " + __prog__ + "\""])
            self.proc("git push -u origin master")

    def clone_repo(self):
        ret = self.proc("git clone " + self.opt["repo"] + " \"" +
                        self.brewinfo.get_dir() + "\"",
                        True, True, False)[0]
        if ret != 0:  # pragma: no cover
            self.err(
                "can't clone " + self.opt["repo"] + ".\n"
                "please check the repository, or reset with\n"
                "    $ " + __prog__ + " set_repo", 0)
            sys.exit(ret)

        self.init_repo()

    def check_github_repo(self):  # pragma: no cover
        """helper to check and create GitHub repository."""
        try:
            from urllib2 import urlopen, HTTPError
        except:
            from urllib.request import urlopen
            from urllib.error import HTTPError

        url = "https://github.com/" + self.user_name() + "/" + self.repo_name()

        # Check if the repository already exists or not.
        exist_repo = True
        try:
            urlopen(url)
        except HTTPError:
            exist_repo = False

        # Clone if exists
        if exist_repo:
            self.clone_repo()
            return

        # Create new repository #
        print("GitHub repository: " + self.user_name() + "/" +
              self.repo_name() + " doesn't exist.")
        ans = self.ask_yn("do you want to create the repository?")
        if not ans:
            exit(0)

        # Try to create w/o two-factor code
        try:
            import requests
        except ImportError:
            print("To create a repository, " +
                  "you need to install 'requests' module.")
            ans = self.ask_yn("Do you want to install now?")
            if not ans:
                print("Please prepare Brewfile repository.")
                exit(0)
            else:
                ret = self.proc("pip --version", False, False, False)
                if ret != 0:
                    self.proc("easy_install pip")
                self.proc("pip install requests")
                print("Now please run `brew file set_repo` again.")
                exit(0)

        import json
        url = "https://api.github.com/user/repos"
        description = "package list for Homebrew"
        data = {"name": self.repo_name(), "description": description,
                "auto_init": "true"}
        headers = {}
        is_ok = True

        # Check password
        import getpass
        password = getpass.getpass("GitHub password: ")

        while True:
            r = requests.post(url=url, data=json.dumps(data),
                              auth=(self.user_name(), password),
                              headers=headers)
            if r.ok:
                break
            if r.json()["message"] == "Bad credentials":
                password = getpass.getpass(
                    "\033[31;1mWrong password!\033[0m GitHub password: ")
                continue
            if r.json()["message"] ==\
                    "Must specify two-factor authentication OTP code.":
                is_ok = False
                break
            self.err(r.json()["message"])
            sys.exit(1)

        if not is_ok:
            # Try with two-factor code
            twofac = my_input("GitHub two-factor code: ")
            headers.update({"X-Github-OTP": twofac})
            while True:
                r = requests.post(url=url, data=json.dumps(data),
                                  auth=(self.user_name(), password),
                                  headers=headers)
                if r.ok:
                    break
                if r.json()["message"] ==\
                        "Must specify two-factor authentication OTP code.":
                    twofac = getpass.getpass("\033[31;1mWrong code!\033[0m "
                                             "GitHub two-factor code: ")
                    headers.update({"X-Github-OTP": twofac})
                    continue
                self.err(r.json()["message"], 0)
                sys.exit(1)

        # Clone and initialize
        self.clone_repo()

    def check_repo(self):
        """Check input file for GitHub repository."""
        import re
        self.brewinfo.set_file(self.opt["input"])

        # Check input file
        if not os.path.exists(self.opt["input"]):
            return

        # Check input file if it points repository or not
        self.opt["repo"] = ""
        f = open(self.opt["input"], "r")
        lines = f.readlines()
        f.close()
        for l in lines:
            if re.match(" *git ", l) is None:
                continue
            git_line = l.split()
            if len(git_line) > 1:
                self.opt["repo"] = git_line[1]
                break
        if self.opt["repo"] == "":
            return

        # Check repository name and add git@github.com: if necessary
        if (not self.opt["repo"].startswith("git://") and
                not self.opt["repo"].startswith("git@") and
                not self.opt["repo"].startswith("http")):
            self.opt["repo"] = "git@github.com:" + self.opt["repo"]

        # Set Brewfile in the repository
        self.brewinfo.set_file(self.repo_file())
        if self.brewinfo.check_file():
            return

        # If repository is empty, initialize it.
        if self.brewinfo.check_dir():
            self.init_repo()
            return

        # Check and prepare repository
        if self.opt["repo"].find("github") != -1:
            self.check_github_repo()
        else:  # pragma: no cover
            self.clone_repo()

    def check_gitconfig(self):
        if (self.opt["repo"].startswith("git://") or
                self.opt["repo"].startswith("http")):
            self.info(
                "You are using repository of %s" % self.opt["repo"] +
                "\nUse git protocol (git@...) to push your Brewfile update.",
                0)
            return False
        name = self.proc("git config user.name", False, False, False, True)[1]
        email = self.proc(
            "git config user.email", False, False, False, True)[1]
        if len(name) == 0 or len(email) == 0:
            self.warn(
                "You don't have user/email information in your .gitconfig.\n"
                "To commit and push your update, run\n"
                '  git config --global user.email "you@example.com"\n'
                '  git config --global user.name "Your Name"\n'
                'and try again.', 0)
            return False
        return True

    def repomgr(self, cmd=""):
        """Helper of repository management."""
        pull = False
        push = False
        if cmd == "pull":
            pull = True
            push = False
        elif cmd == "push":
            pull = False
            push = True

        # Check the repository
        if self.opt["repo"] == "":
            self.err("Please set a repository, or reset with:", 0)
            self.err("    $ " + __prog__ + " set_repo\n", 0)
            sys.exit(1)

        # Clone if it doesn't exist
        if not self.brewinfo.check_dir():  # pragma: no cover
            self.clone_repo()

        # pull/push
        self.info("$ cd " + self.brewinfo.get_dir(), 1)
        os.chdir(self.brewinfo.get_dir())
        if pull:
            self.proc("git pull")
            return
        elif push:
            if self.check_gitconfig():
                self.proc("git add -A")
                self.proc(["git", "commit", "-m",
                           "\"Update the package list\""],
                          exit_on_err=False)
                self.proc("git push")
            return

    def brew_cmd(self):
        noinit = False
        if len(self.opt["args"]) > 0 and "noinit" in self.opt["args"]:
            noinit = True
            self.opt["args"].remove("noinit")

        exe = "brew"
        cmd = self.opt["args"][0] if len(self.opt["args"]) > 0 else ""
        subcmd = self.opt["args"][1] if len(self.opt["args"]) > 1 else ""
        args = self.opt["args"]
        env = {}
        if cmd == "cask":
            self.check_cask_cmd(True)
        elif cmd == "pip":
            self.opt["args"].pop(0)
            exe = "brew-pip"
            self.check_pip_cmd(True)
            env["HOMEBREW_CELLAR"] = os.environ.get(
                "HOMEBREW_CELLAR",
                self.brew_val("cellar"))
        elif cmd == "gem":
            exe = "brew-gem"
            self.opt["args"].pop(0)
            self.check_gem_cmd(True)
            if self.opt["homebrew_ruby"] and\
                    "--homebrew-ruby" not in self.opt["args"]:
                self.opt["args"].append("--homebrew-ruby")

        (ret, lines) = self.proc([exe] + self.opt["args"],
                                 False, True, False, env=env)

        if ret != 0 or noinit:
            sys.exit(ret)

        if cmd in ["cask"]:
            args = self.opt["args"][2:]
        elif cmd in ["pip"]:
            args = self.opt["args"]
        else:
            args = self.opt["args"][1:]
        nargs = len(args)

        if cmd not in ["instal", "install", "reinstall", "tap",
                       "rm", "remove", "uninstall", "untap", "cask",
                       "pip", "gem"] or\
                nargs == 0 or\
                (cmd == "cask" and subcmd not in
                    ["instal", "install", "rm", "remove", "uninstall"]) or\
                (cmd == "gem" and subcmd not in
                    ["instal", "install", "uninstall"]):
            # Not install/remove command, no init.
            sys.exit(0)

        global_opts = []
        packages = []
        opts = {}
        if cmd in ["gem"]:
            packages.append(args[0])
            opts[packages[0]] = args[1:]
        elif cmd in ["pip"]:
            pip_upgrade = False
            for v in args:
                if v.find("/") != -1 or v.find("tar.gz") != -1 or\
                        v.find(".zip") != -1:
                    # lock packages
                    sys.exit(0)
                elif v in ["-h", "--help", "--version"]:
                    sys.exit(0)
                elif v in ["-u", "--upgrade"]:
                    pip_upgrade = True
                elif v in ["-k", "--keg-only", "-v", "--verbose"]:
                    pass
                elif not v.startswith("-"):
                    p_array = v.split("=")
                    packages.append(p_array[0])
                    if len(p_array) > 1:
                        opts[p_array[0]] = [p_array[1]]
                    else:
                        opts[p_array[0]] = []
        else:
            for v in args:
                if v.startswith("-"):
                    if len(packages) == 0:
                        global_opts.append(v)
                    else:
                        opts[packages[-1]].append(v)
                else:
                    packages.append(v)
                    opts[packages[-1]] = []

        if self.brewinfo.check_file():
            self.read_all()

        if (cmd in ["rm", "remove", "uninstall", "reinstall"] or
                (cmd == "cask" and subcmd in ["rm", "remove", "uninstall"]) or
                (cmd == "pip" and pip_upgrade) or
                (cmd == "gem" and subcmd in ["uninstall"])):
            for p in packages:
                input_list = "brew_input"
                if cmd == "cask":
                    input_list = "cask_input"
                elif p.startswith("pip-") or cmd == "pip":
                    input_list = "pip_input"
                    p = p.replace("pip-", "")
                elif p.startswith("gem-") or cmd == "gem":
                    input_list = "gem_input"
                    p = p.replace("gem-", "")
                is_removed = False
                for bi in self.get(input_list):
                    if p == bi or p == bi.split("/")[-1].replace(".rb", ""):
                        self.remove_pack(input_list, bi)
                        if input_list == "brew_input":
                            self.remove_pack("brew_input_opt", bi)
                        elif input_list == "pip_input":
                            self.remove_pack("pip_input_opt", bi)
                        elif input_list == "gem_input":
                            self.remove_pack("gem_input_opt", bi)
                        is_removed = True
                        break
                if cmd not in ["reinstall", "pip"] and not is_removed:
                    self.warn(p + " is not in Brewfile.")
                    self.warn("Try 'brew file init' to clean up Brewfile")
        if (cmd in ["instal", "install", "reinstall", "pip"] or
                (cmd == "cask" and subcmd in ["instal", "install"]) or
                (cmd == "gem" and subcmd in ["instal", "install"])):
            input_list = "brew_input"
            if cmd == "cask":
                input_list = "cask_input"
            elif cmd == "pip":
                input_list = "pip_input"
            elif cmd == "gem":
                input_list = "gem_input"
            for p in packages:
                porig = p
                psplit = p.split("/")
                t = ""
                if len(psplit) > 0:
                    if len(psplit) == 3 and not p.startswith("http") and\
                            not p.startswith("ftp") and not p.startswith("/"):
                        p = psplit[-1]
                        t = "/".join(psplit[:-1])
                    else:
                        t = "direct"
                if p in self.get(input_list) or\
                        p.split("/")[-1].replace(".rb", "")\
                        in self.get(input_list):
                    self.warn(p + " is already in Brewfile.")
                    self.warn("Do 'brew file init' to clean up Brewfile")
                    continue
                if cmd == "cask":
                    self.brewinfo.cask_input.append(p)
                    self.brewinfo.cask_input.sort()
                elif cmd == "pip":
                    self.brewinfo.pip_input.append(p)
                    self.brewinfo.pip_input.sort()
                    if len(opts[porig]) > 0:
                        self.brewinfo.pip_input_opt[p] =\
                            " " + " ".join(opts[porig]).strip()
                    else:
                        self.brewinfo.pip_input_opt[p] = ""
                elif cmd == "gem":
                    self.brewinfo.gem_input.append(p)
                    self.brewinfo.gem_input.sort()
                    if len(opts[porig]) > 0:
                        self.brewinfo.gem_input_opt[p] =\
                            " " + " ".join(opts[porig]).strip()
                    else:
                        self.brewinfo.gem_input_opt[p] = ""
                else:
                    self.brewinfo.brew_input.append(p)
                    if len(opts[porig]) > 0:
                        self.brewinfo.brew_input_opt[p] =\
                            " " + " ".join(opts[porig]).strip()
                    else:
                        self.brewinfo.brew_input_opt[p] = ""
                    for p_dep in self.proc(
                            "brew deps " + p, False, False)[1]:
                        if p_dep not in self.get(input_list) and \
                                (not (self.opt["leaves"] and
                                      self.opt["on_request"]) or
                                 p_dep in self.opt["top_packages"].split(",")):
                            self.brewinfo.brew_input.append(p_dep)
                            self.brewinfo.brew_input_opt[p_dep] = ""
                    self.brewinfo.brew_input.sort()
                if t != "" and t not in self.get("tap_input"):
                    self.brewinfo.tap_input.append(t)
                    self.brewinfo.tap_input.sort()
        elif cmd == "tap":
            for p in packages:
                if p in self.get("tap_input"):
                    self.warn(p + " is already in Brewfile.")
                    self.warn("Do 'brew file init' to clean up Brewfile")
                self.brewinfo.tap_input.append(p)
            self.brewinfo.tap_input.sort()
        elif cmd == "untap":
            for p in packages:
                if p not in self.get("tap_input"):
                    self.warn(p + " is not in Brewfile.")
                    self.warn("Do 'brew file init' to clean up Brewfile")
                self.remove_pack("tap_input", p)

        self.input_to_list()
        self.initialize_write()

    def check_brew_cmd(self):  # pragma: no cover
        """Check Homebrew"""
        if self.proc("which brew", False, False, False, verbose=1)[0] != 0:
            print("Homebrew has not been installed, install now...")
            cmd = "curl -O https://raw.githubusercontent.com/" +\
                  "Homebrew/install/master/install"
            self.proc(cmd, True, True, False, verbose=0)
            cmd = "ruby install"
            self.proc(cmd, True, True, False, verbose=0)
            (ret, lines) = self.proc("brew doctor", True, True, False,
                                     verbose=0)
            if ret != 0:
                for l in lines:
                    sys.stdout.write(l)
                print("")
                self.warn("\nCheck brew environment and fix problems\n"
                          "# You can check with:\n"
                          "#     $ brew doctor", 0)

    def check_cask_cmd(self, force=False):
        """Check cask is installed or not"""
        if self.opt["is_cask_cmd"]:
            return True
        if os.path.isdir(self.brewinfo.get_tap_path(self.opt["cask_repo"])):
            self.opt["is_cask_cmd"] = True
            return True
        ret = self.proc(["brew", "tap", self.opt["cask_repo"]],
                        True, True, False)[0]
        if ret != 0:  # pragma: no cover
            self.err("\nFailed to install " +
                     self.opt["cask_repo"] + "\n", 0)
            sys.exit(ret)
        if not self.opt["cask_repo"] in self.get("tap_list"):
            self.brewinfo.tap_list.append(self.opt["cask_repo"])
        self.opt["is_cask_cmd"] = True
        self.opt["cask_cmd_installed"] = True
        return self.opt["is_cask_cmd"]

    def check_mas_cmd(self, force=False):
        """Check mas is installed or not"""
        if self.opt["is_mas_cmd"] != 0:
            return self.opt["is_mas_cmd"]

        if self.proc("type mas", False, False, False)[0] != 0:
            sw_vers = self.proc("sw_vers -productVersion",
                                False, False, False)[1][0].split(".")
            if int(sw_vers[0]) < 10 or (int(sw_vers[0]) == 10 and
                                        int(sw_vers[1]) < 11):
                self.warn("You are using older OS X. mas is not used.", 3)
                self.opt["is_mas_cmd"] = -1
                return self.opt["is_mas_cmd"]
            self.info(self.opt["mas_formula"] + " has not been installed.")
            if not force:
                ans = self.ask_yn("Do you want to install %s?" %
                                  self.opt["mas_formula"])
                if not ans:  # pragma: no cover
                    self.warn("If you need it, please do:")
                    self.warn("    $ brew install %s"
                              % (self.opt["mas_formula"]))
                    self.opt["is_mas_cmd"] = -2
                    return self.opt["is_mas_cmd"]
            ret = self.proc(["brew", "install", self.opt["mas_formula"]],
                            True, True, False)[0]
            if ret != 0:  # pragma: no cover
                self.err("\nFailed to install " +
                         self.opt["mas_formula"] + "\n", 0)
                self.opt["is_mas_cmd"] = -1
                return self.opt["is_mas_cmd"]
            p = os.path.basename(self.opt["mas_formula"])
            if p not in self.get("brew_list"):
                self.brewinfo.brew_list.append(p)
                self.brewinfo.brew_list_opt[p] = ""

        if self.proc(self.opt["mas_cmd"], False, False, False)[0] != 0:
            # fail?
            self.opt["is_mas_cmd"] = -1
            return self.opt["is_mas_cmd"]
        else:
            self.opt["is_mas_cmd"] = 1

        is_tmux = os.environ.get("TMUX", "")
        if is_tmux != "":  # pragma: no cover
            if self.proc("type reattach-to-user-namespace",
                         False, False, False)[0] != 0:
                if not force:
                    ans = self.ask_yn(
                        "You need %s in tmux. Do you want to install it?" %
                        self.opt["reattach_formula"])
                    if not ans:  # pragma: no cover
                        self.warn("If you need it, please do:")
                        self.warn("    $ brew install %s"
                                  % (self.opt["reattach_formula"]))
                        return self.opt["is_mas_cmd"]
                ret = self.proc(["brew", "install",
                                 self.opt["reattach_formula"]],
                                True, True, False)[0]
                if ret != 0:  # pragma: no cover
                    self.err("\nFailed to install " +
                             self.opt["reattach_formula"] + "\n", 0)
                    self.opt["is_mas_cmd"] = -1
                    return self.opt["is_mas_cmd"]
                p = os.path.basename(self.opt["reattach_formula"])
                if p not in self.get("brew_list"):
                    self.brewinfo.brew_list.append(p)
                    self.brewinfo.brew_list_opt[p] = ""
                self.opt["reattach_cmd_installed"] = True
            self.opt["mas_cmd"] = "reattach-to-user-namespace mas"

        return self.opt["is_mas_cmd"]

    def check_pip_cmd(self, force=False):
        """Check pip is installed or not"""
        if self.opt["is_pip_cmd"]:
            return True
        if self.proc("brew pip -h", False, False, False)[0] == 0:
            self.opt["is_pip_cmd"] = True
            return True
        self.info(self.opt["pip_pack"] + " has not been installed.")
        if not force:  # pragma: no cover
            ans = self.ask_yn("Do you want to install %s?" %
                              self.opt["pip_pack"])
            if not ans:  # pragma: no cover
                self.warn("If you need it, please do:")
                self.warn("    $ brew install %s" % (self.opt["pip_pack"]))
                return self.opt["is_pip_cmd"]

        ret = self.proc(["brew", "install", self.opt["pip_pack"]],
                        True, True, False)[0]
        if ret != 0:  # pragma: no cover
            self.err("\nFailed to install " +
                     self.opt["pip_pack"] + "\n", 0)
            sys.exit(ret)
        if not self.opt["pip_pack"] in self.get("brew_list"):
            self.brewinfo.brew_list.append(self.opt["pip_pack"])
            self.brewinfo.brew_list_opt[self.opt["pip_pack"]] = ""
        self.opt["is_pip_cmd"] = True
        self.opt["pip_cmd_installed"] = True
        return self.opt["is_pip_cmd"]

    def check_gem_cmd(self, force=False):
        """Check gem is installed or not"""
        if self.opt["is_gem_cmd"]:
            return True
        if self.proc("brew gem -h", False, False, False)[0] == 0:
            self.opt["is_gem_cmd"] = True
            return True
        self.info(self.opt["gem_pack"] + " has not been installed.")
        if not force:
            ans = self.ask_yn("Do you want to install %s?" %
                              self.opt["gem_pack"])
            if not ans:  # pragma: no cover
                self.warn("If you need it, please do:")
                self.warn("    $ brew install %s"
                          % (self.opt["gem_pack"]))
                return self.opt["is_gem_cmd"]

        ret = self.proc(["brew", "install", self.opt["gem_pack"]],
                        True, True, False)[0]
        if ret != 0:  # pragma: no cover
            self.err("\nFailed to install " +
                     self.opt["gem_pack"] + "\n", 0)
            sys.exit(ret)
        if not self.opt["gem_pack"] in self.get("brew_list"):
            self.brewinfo.brew_list.append(self.opt["gem_pack"])
            self.brewinfo.brew_list_opt[self.opt["gem_pack"]] = ""
        self.opt["is_gem_cmd"] = True
        self.opt["gem_cmd_installed"] = True
        return self.opt["is_gem_cmd"]

    def get_appstore_list(self):
        """Get AppStore Application List"""

        apps = []

        if self.check_mas_cmd(True) == 1:
            (ret, lines) = self.proc(self.opt["mas_cmd"] + " list",
                                     False, False, separate_err=True)
            apps = sorted(lines, key=lambda x: " ".join(x.split()[1:]).lower())
            if len(apps) > 0 and apps[0] == "No installed apps found":
                apps = []
        else:  # pragma: no cover
            import glob
            apps_tmp = []
            for d in self.opt["appdirlist"]:
                apps_tmp += [
                    ("/".join(x.split("/")[:-3]).split(".app")[0])
                    for x in glob.glob(d + "/*/Contents/_MASReceipt/receipt")]
            # Another method
            # Sometime it can't find applications which have not been used?
            # (ret, app_tmp) = self.proc(
            #     "mdfind 'kMDItemAppStoreHasReceipt=1'", False, False)
            for a in apps_tmp:
                print(a)
                apps_id = self.proc(
                    "mdls -name kMDItemAppStoreAdamID -raw '%s.app'" % a,
                    False, False)[1][0]
                apps.append("%s %s" %
                            (apps_id, a.split("/")[-1].split(".app")[0]))

        return apps

    def get_cask_list(self, force=False):
        """Get Cask List"""

        if not self.check_cask_cmd(force):  # pragma: no cover
            return (False, [])
        (ret, lines) = self.proc("brew cask list", False, False,
                                 separate_err=True, print_err=False)
        packages = []
        for l in lines:
            if "Warning: nothing to list" in l or "=>" in l or "->" in l:
                continue
            packages.append(l)
        return (True, packages)

    def get_list(self):
        """Get List"""

        # Clear lists
        self.brewinfo.clear_list()

        # Brew packages
        if not self.opt["caskonly"]:
            info = self.brewinfo.get_info()
            full_list = self.proc("brew list", False, False)[1]
            if self.opt["on_request"]:
                leaves = []
                for p in info:
                    installed = self.brewinfo.get_installed(p, info[p])
                    if installed["installed_on_request"] is True or\
                            installed["installed_on_request"] is None:
                        leaves.append(p)

            elif self.opt["leaves"]:
                leaves = self.brewinfo.get_leaves()
            else:
                import copy
                leaves = copy.deepcopy(full_list)

            for p in self.opt["top_packages"].split(","):
                if p == "":
                    continue
                if p in full_list and p not in leaves:
                    leaves.append(p)

            # pip/gem
            # pip/gem packages are not in brew info list
            for p in full_list:
                if p.startswith("pip-"):
                    package = p.replace("pip-", "")
                    self.brewinfo.pip_list.append(package)
                    self.brewinfo.pip_list_opt[package] = ""
                elif p.startswith("gem-"):
                    package = p.replace("gem-", "")
                    self.brewinfo.gem_list.append(package)
                    self.brewinfo.gem_list_opt[package] = ""
                else:
                    continue
                if p in leaves:
                    leaves.remove(p)

            for p in info:
                if p not in leaves:
                    continue
                self.brewinfo.brew_list.append(p)
                self.brewinfo.brew_list_opt[p] =\
                    self.brewinfo.get_option(p, info[p])

        # Taps
        (ret, lines) = self.proc("brew tap", False, False,
                                 env={"HOMEBREW_NO_AUTO_UPDATE": "1"})

        self.brewinfo.set_val("tap_list", lines)
        self.brewinfo.add("tap_list", ["direct"])

        # Casks
        for p in self.get_cask_list()[1]:
            if len(p.split()) == 1:
                self.brewinfo.cask_list.append(p)
            else:  # pragma: no cover
                self.warn("The cask file of " + p +
                          " doesn't exist.", 0)
                self.warn("Please check later.\n\n", 0)
                self.brewinfo.cask_nocask_list.append(p)

        # App Store
        if self.opt["appstore"]:
            self.brewinfo.set_val("appstore_list", self.get_appstore_list())

    def clean_list(self):
        """Remove duplications between brewinfo.list to extra files' input"""

        # Cleanup extra files
        for b in self.brewinfo_ext:
            for l in ["brew", "tap", "cask", "pip", "gem", "appstore"]:
                for p in b.get(l+"_input"):
                    if p not in self.brewinfo.get(l+"_list"):
                        b.remove(l+"_input", p)

        # Copy input to list for extra files.
        self.input_to_list(only_ext=True)

        # Loop over lists to remove duplications.
        # tap_list is not checked for overlap removal.
        # Keep it in main list in any case.
        for l in ["brew", "cask", "cask_nocask", "pip", "gem", "appstore"]:
            if l == "cask_nocask":
                i = "cask"
            else:
                i = l
            for p in self.brewinfo.get(l+"_list"):
                if p in self.get(i+"_input", True):
                    self.brewinfo.remove(l+"_list", p)

        # Keep file in main Brewfile
        self.brewinfo.file_list.extend(self.brewinfo.file_input)
        self.input_to_list(only_ext=True)

    def set_brewfile_repo(self):
        """Set Brewfile repository"""
        import re

        # Check input file
        if os.path.exists(self.opt["input"]):
            prev_repo = ""
            f = open(self.opt["input"], "r")
            lines = f.readlines()
            f.close()
            for l in lines:
                if re.match(" *git ", l) is None:
                    continue
                git_line = l.split()
                if len(git_line) > 1:
                    prev_repo = git_line[1]
                    break
            if self.opt["repo"] == "":
                print("Input file: " + self.opt["input"] +
                      " is already there.")
                if prev_repo != "":
                    print("git repository for Brewfile is already set as " +
                          prev_repo + ".")

            if self.opt["backup"] != "":
                ans = self.ask_yn("Do you want to overwrite it?")
                if ans:
                    os.rename(self.opt["input"], self.opt["backup"])
                    self.info("Ok, old input file was moved to " +
                              self.opt["backup"], 1)
                else:  # pragma: no cover
                    sys.exit(0)

        # Get repository
        if self.opt["repo"] == "":  # pragma: no cover
            print("\nSet repository,\n" +
                  "\"non\" (or empty) for local Brewfile " +
                  "(" + self.opt["input"] + "),\n" +
                  "<user>/<repo> for github repository,")
            self.opt["repo"] = my_input(
                "or full path for other git repository: ")
            self.banner("# Set Brewfile repository as " +
                        self.opt["repo"])

        if self.opt["repo"] in ["non", ""]:  # pragma: no cover
            self.set_brewfile_local()
            return
        else:
            # Write repository to the input file
            f = open_output_file(self.opt["input"], "w")
            f.write("git " + self.opt["repo"])
            f.close()
            self.check_repo()

    def set_brewfile_local(self):
        """Set Brewfile to local file"""
        self.initialize(False, False)

    def initialize(self, check=True, check_input=True):
        """Initialize Brewfile"""
        if self.opt["initialized"]:
            return

        if check == 1:
            if not os.path.exists(self.opt["input"]):
                ans = self.ask_yn("Do you want to set a repository (y)? " +
                                  "((n) for local Brewfile).")
                if ans:
                    self.set_brewfile_repo()
            else:
                if self.opt["repo"] != "":
                    print("You are using Brewfile of " + self.opt["repo"] +
                          ".")
                else:
                    print(self.opt["input"] + " is already there.")
                    if self.opt["backup"] != "":
                        os.rename(self.opt["input"], self.opt["backup"])
                    else:
                        ans = self.ask_yn("Do you want to overwrite it?")
                        if ans:
                                self.info("Ok, old input file was moved to " +
                                          self.opt["backup"], 1)
                        else:  # pragma: no cover
                            sys.exit(0)

        # Get installed package list
        self.get_list()

        # Read inputs
        if check_input:
            if self.brewinfo.check_file():
                self.read_all()

            # Remove duplications between brewinfo.list to extra files' input
            self.clean_list()

        # write out
        self.initialize_write()

    def initialize_write(self):
        self.write()
        self.banner("# You can edit " + self.brewinfo.get_file() + " with:\n"
                    "#     $ " + __prog__ + " edit")
        self.opt["initialized"] = True

    def check_input_file(self):
        """Check input file"""

        if not self.brewinfo.check_file():
            self.warn(
                "Input file " + self.brewinfo.get_file() + " is not found.", 0)
            ans = self.ask_yn(
                "Do you want to initialize from installed packages?")
            if ans:
                self.initialize(False)
                return
            else:  # pragma: no cover
                self.err("Ok, please prepare brewfile", 0)
                self.err("or you can initialize " +
                         self.brewinfo.get_file() + " with:", 0)
                self.err("    $ " + __prog__ + " init", 0)
                sys.exit(1)

    def get_files(self, is_print=False):
        """Get Brewfiles"""
        self.read_all()
        files = [x.get_file() for x in [self.brewinfo] + self.brewinfo_ext]
        if is_print:
            print("\n".join(files))
        return files

    def edit_brewfile(self):
        """Edit brewfiles"""
        import shlex
        import subprocess
        self.editor = shlex.split(self.opt["my_editor"])
        subprocess.call(self.editor + self.get_files())

    def cat_brewfile(self):
        """Cat brewfiles"""
        import subprocess
        subprocess.call(["cat"] + self.get_files())

    def clean_non_request(self):
        """Clean up non requested packages."""
        if self.opt["dryrun"]:
            self.banner("# This is dry run.")

        info = self.brewinfo.get_info()
        leaves = self.brewinfo.get_leaves()
        for p in info:
            if p not in leaves:
                continue
            installed = self.brewinfo.get_installed(p, info[p])
            if installed["installed_on_request"] is False:
                cmd = "brew uninstall " + p
                if self.opt["dryrun"]:
                    print(cmd)
                else:
                    self.proc(cmd, False, True)

        if self.opt["dryrun"]:
            self.banner("# This is dry run.\n"
                        "# If you want to enforce cleanup, use '-C':\n"
                        "#     $ " + __prog__ + " clean_non_request -C")

    def cleanup(self):
        """Clean up."""
        if self.opt["dryrun"]:
            self.banner("# This is dry run.")

        # Check up packages in the input file
        self.read_all()
        info = self.brewinfo.get_info()

        def add_dependncies(package):
            for pac in info[package]["dependencies"]:
                p = pac.split("/")[-1]
                if p not in info:
                    continue
                if p not in self.get("brew_input"):
                    self.brewinfo.brew_input.append(p)
                    self.brewinfo.brew_input_opt[p] = ""
                    add_dependncies(p)
        for p in self.get("brew_input"):
            if p not in info:
                continue
            add_dependncies(p)

        # Clean up App Store applications
        if self.opt["appstore"] and \
                len(self.get("appstore_list")) > 0:  # pragma: no cover
            self.banner("# Clean up App Store applications")
            uninstall = self.proc("type uninstall", False, False, False)
            if uninstall == 0:
                cmd = "sudo uninstall"
            else:
                cmd = "sudo rm -rf"
            n_uninstall = 0
            try:
                from urllib2 import quote
            except:
                from urllib.parse import quote

            for p in self.get("appstore_list"):
                identifier = p.split()[0]
                if identifier.isdigit() and len(identifier) == 9:
                    package = " ".join(p.split()[1:])
                else:
                    identifier = ""
                    package = p
                isinput = False
                for pi in self.get("appstore_input"):
                    i_identifier = pi.split()[0]
                    if i_identifier.isdigit() and len(i_identifier) == 9:
                        i_package = " ".join(pi.split()[1:])
                    else:
                        i_identifier = ""
                        i_package = pi
                    if package == i_package:
                        isinput = True
                        break
                if isinput:
                    continue
                tmpcmd = cmd
                package = " ".join(p.split()[1:])
                for d in self.opt["appdirlist"]:
                    a = "%s/%s.app" % (d, package)
                    if os.path.isdir(a):
                        if uninstall == 0:
                            cmd += " file:///" + quote(a)
                        else:
                            cmd += " '%s'" % a
                        continue
                if cmd == tmpcmd:
                    continue
                n_uninstall += 1
                if self.opt["dryrun"]:
                    print(cmd)
                self.remove_pack("appstore_list", p)
            if not self.opt["dryrun"] and n_uninstall > 0:
                self.proc(cmd, True, True, False)

        # Clean up cask packages
        if len(self.get("cask_list")) > 0:
            self.banner("# Clean up cask packages")
            for p in self.get("cask_list"):
                if p in self.get("cask_input"):
                    continue
                self.check_cask_cmd(True)
                cmd = "brew cask uninstall " + p
                if self.opt["dryrun"]:
                    print(cmd)
                else:
                    self.proc(cmd, True, True)
                self.remove_pack("cask_list", p)

        # Skip clean up cask at tap if any cask packages exist
        if len(self.get("cask_list")) > 0:
            self.remove_pack("tap_list", self.opt["cask_repo"])

        # Clean up pip packages
        if len(self.get("pip_list")) > 0:
            self.banner("# Clean up pip packages")
            for p in self.get("pip_list"):
                if p in self.get("pip_input"):
                    continue
                cmd = "brew uninstall --ignore-dependencies pip-" + p
                if self.opt["dryrun"]:
                    print(cmd)
                else:
                    self.proc(cmd, True, True, False)
                self.remove_pack("pip_list", p)
                self.remove_pack("pip_list_opt", p)
        # Skip clean up brew-pip at brew if any pip packages exist
        if len(self.get("pip_list")) > 0:
            self.remove_pack("brew_list", self.opt["pip_pack"])
            self.remove_pack("brew_list_opt", self.opt["pip_pack"])

        # Clean up gem packages
        if len(self.get("gem_list")) > 0:
            self.banner("# Clean up gem packages")
            for p in self.get("gem_list"):
                if p in self.get("gem_input"):
                    continue
                cmd = "brew uninstall --ignore-dependencies gem-" + p
                if self.opt["dryrun"]:
                    print(cmd)
                else:
                    self.proc(cmd, True, True, False)
                self.remove_pack("gem_list", p)
                self.remove_pack("gem_list_opt", p)
        # Skip clean up brew-gem at brew if any gem packages exist
        if len(self.get("gem_list")) > 0:
            self.remove_pack("brew_list", self.opt["gem_pack"])
            self.remove_pack("brew_list_opt", self.opt["gem_pack"])

        # Clean up brew packages
        if len(self.get("brew_list")) > 0:
            self.banner("# Clean up brew packages")
            for p in self.get("brew_list"):
                if p in self.get("brew_input"):
                    continue
                # Use --ignore-dependencies option to remove packages w/o
                # formula (tap of which could be removed before).
                cmd = "brew uninstall --ignore-dependencies " + p
                if self.opt["dryrun"]:
                    print(cmd)
                else:
                    self.proc(cmd, False, True)

        # Clean up tap packages
        if len(self.get("tap_list")) > 0:
            self.banner("# Clean up tap packages")
            for p in self.get("tap_list"):
                if p in self.get("tap_input"):
                    continue
                self.brewinfo.get_tap(p)
                untapflag = True
                for tp in self.brewinfo.tap_packs:
                    if tp in self.get("brew_input"):
                        # Keep the Tap as related package is remained
                        untapflag = False
                        break
                if not untapflag:
                    continue
                for tc in self.brewinfo.tap_casks:
                    if tc in self.get("cask_input"):
                        # Keep the Tap as related cask is remained
                        untapflag = False
                        break
                if not untapflag:
                    continue
                cmd = "brew untap " + p
                if self.opt["dryrun"]:
                    print(cmd)
                else:
                    self.proc(cmd, True, True)

        # Clean up cashe
        self.banner("# Clean up cache")
        cmd0 = "brew cleanup --force"
        cmd1 = "rm -rf " + self.brew_val("cache")
        if self.opt["dryrun"]:
            print(cmd0)
            print(cmd1)
            # Dry run message
            self.banner("# This is dry run.\n"
                        "# If you want to enforce cleanup, use '-C':\n"
                        "#     $ " + __prog__ + " clean -C")
        else:
            self.proc(cmd0, False)
            self.proc(cmd1, False)

    def install(self):
        """Install"""
        # Reinit flag
        reinit = 0

        # Check packages in the input file
        self.read_all()

        # before commands
        for c in self.get("before_input"):
            self.proc(c)

        # Tap
        for p in self.get("tap_input"):
            if p in self.get("tap_list") or p == "direct":
                continue
            self.proc("brew tap " + p)

        # Cask
        for p in self.get("cask_input"):
            if p in self.get("cask_list"):
                continue
            self.check_cask_cmd(True)
            self.proc("brew cask install --force " + p)

        if not self.opt["caskonly"]:
            # pip
            for p in self.get("pip_input"):
                if p in self.get("pip_list"):
                    # if sorted(self.get("pip_input_opt")[p].split()) ==\
                    #         sorted(self.get("pip_list_opt")[p].split()):
                    #     continue
                    # else:
                    #     self.proc(
                    #         "brew uninstall --ignore-dependencies pip-" + p)
                    continue

                self.check_pip_cmd(True)
                self.proc("brew pip " + p + self.get("pip_input_opt")[p])

            # gem
            for p in self.get("gem_input"):
                if p in self.get("gem_list"):
                    # if sorted(self.get("gem_input_opt")[p].split()) ==\
                    #         sorted(self.get("gem_list_opt")[p].split()):
                    #     continue
                    # else:
                    #     self.proc(
                    #         "brew uninstall --ignore-dependencies gem-" + p)
                    continue
                self.check_gem_cmd(True)
                self.proc("brew gem install " + p +
                          self.get("gem_input_opt")[p])

            # Brew
            for p in self.get("brew_input"):
                cmd = "install"
                if p in self.get("brew_list"):
                    if sorted(self.get("brew_input_opt")[p].split()) ==\
                              sorted(self.get("brew_list_opt")[p].split()):
                        continue
                    else:
                        cmd = "reinstall"
                (ret, lines) = self.proc("brew " + cmd + " " + p +
                                         self.get("brew_input_opt")[p])
                if ret != 0:  # pragma: no cover
                    self.warn("Can not install " + p + "."
                              "Please check the package name.\n"
                              "" + p + " may be installed "
                              "by using web direct formula.", 0)
                    continue
                for l in lines:
                    if l.find("ln -s") != -1:
                        if self.opt["link"]:
                            cmdtmp = l.split()
                            cmd = []
                            for c in cmdtmp:
                                if c.startswith("~/"):
                                    cmd.append(os.path.expanduser(c))
                                else:
                                    cmd.append(c)
                            self.proc(cmd)
                    if l.find("brew linkapps") != -1:
                        if self.opt["link"]:
                            self.proc("brew linkapps")
                if p in self.get("brew_list") and\
                        self.get("brew_input_opt")[p] !=\
                        self.get("brew_list_opt")[p]:
                    self.brewinfo.add("brew_input_opt",
                                      {p: self.brewinfo.get_option(p)})
                    reinit = 1

        # App Store
        if self.opt["appstore"]:  # pragma: no cover
            mas_flag = 0
            for p in self.get("appstore_input"):
                if p in self.get("appstore_list"):
                    continue
                identifier = p.split()[0]
                if identifier.isdigit() and len(identifier) >= 9:
                    package = " ".join(p.split()[1:])
                else:
                    identifier = ""
                    package = p
                islist = False
                for pl in self.get("appstore_list"):
                    l_identifier = pl.split()[0]
                    if l_identifier.isdigit() and len(l_identifier) >= 9:
                        l_package = " ".join(pl.split()[1:])
                    else:
                        l_identifier = ""
                        l_package = pl
                    if package == l_package:
                        islist = True
                        break
                if islist:
                    continue
                if mas_flag == 0:
                    mas_flag = self.check_mas_cmd(True)
                self.info("Installing " + package)
                if identifier != "":
                    if mas_flag == 1:
                        self.proc(self.opt["mas_cmd"] + " install " +
                                  identifier)
                    else:
                        self.info("Please install %s from AppStore." %
                                  package, 0)
                        self.proc(
                            "open -W 'macappstore://itunes.apple.com/app/id%s'"
                            % (identifier))
                else:
                    self.warn("No id or wrong id information was given for "
                              "AppStore App: %s.\n"
                              "Please install it manually." % package,
                              0)  # pragma: no cover

        # Other commands
        for c in self.get("cmd_input"):
            self.proc(c)

        # after commands
        for c in self.get("after_input"):
            self.proc(c)

        # Initialize if commands are installed
        if self.opt["cask_cmd_installed"] or\
                self.opt["mas_cmd_installed"] or\
                self.opt["reattach_cmd_installed"] or\
                self.opt["pip_cmd_installed"] or\
                self.opt["gem_cmd_installed"] or\
                reinit:
            self.opt["cask_cmd_installed"] = self.opt["mas_cmd_installed"] =\
                self.opt["reattach_cmd_installed"] =\
                self.opt["pip_cmd_installed"] =\
                self.opt["gem_cmd_installed"] = False
            self.input_to_list()
            self.initialize_write()
        return 0

    def find_app(self, app, taps, casks, nonapp_casks,
                 casks_noinst, nonapp_casks_noinst):
        """Helper function for Cask"""
        self.check_cask_cmd(True)
        [cask_user, cask_repo_name] = self.opt["cask_repo"].split("/")
        cask_namer = self.brewinfo.get_tap_path(self.opt["cask_repo"]) +\
            "/developer/bin/generate_cask_token"
        tap_cands = []
        name_cands = []
        lines = self.proc([cask_namer, '"' + app.split("/")[-1].lower() + '"'],
                          False, False, False)[1]
        for l in lines:
            if l.find("Proposed token") != -1:
                name_cands.append(l.split()[2])
            if l.find("already exists") != -1:
                for t in taps:
                    tname = t.split('/')[0]+"/homebrew-"+t.split('/')[1]
                    if l.split("'")[1].find(tname) != -1:
                        tap_cands.append(t)
                        break
        if len(tap_cands) == 0:
            del name_cands[:]

        installed = False
        clist = list(casks.values()) + nonapp_casks +\
            [x for x_list in casks_noinst.values() for x in x_list] +\
            nonapp_casks_noinst
        if len(name_cands) > 0 and\
                len([x for x in clist if x[0] == name_cands[0] and x[2]]) > 0:
            installed = True
        else:
            for c in [x for x in clist if app in x[5]]:
                if c[2]:
                    installed = True
                    tap_cands = [c[1]]
                    name_cands = [c[0]]
                    break
                if c[0] not in name_cands:
                    tap_cands.append(c[1])
                    name_cands.append(c[0])
        if len(name_cands) == 0:
            self.info("Non Cask app: " + app, 2)
        elif installed:
            self.info("Installed by Cask:" + app + name_cands[0], 2)
        else:
            self.info("Installed directly, instead of by Cask:" +
                      app + ", Cask candidates: " + ", ".join(name_cands), 2)
        return (tap_cands, installed, name_cands)

    def find_brew_app(self, name, tap):
        """Helper function for Cask to find app installed by brew install"""

        check = "has_cask"
        tap_brew = tap
        opt = ""
        if os.path.isfile(self.brew_val("repository") +
                          "/Library/Formula/" + name + ".rb"):
            if type(self.opt["brew_packages"]) == str:
                self.opt["brew_packages"] = self.proc("brew list", False,
                                                      False)[1]
            if name in self.opt["brew_packages"]:
                check = "brew"
                opt = self.brewinfo.get_option(name)
                if os.path.islink(self.brew_val("repository") +
                                  "/Library/Formula/" + name + ".rb"):
                    link = os.readlink(self.brew_val("repository") +
                                       "/Library/Formula/" + name + ".rb")
                    tap_brew = link.replace("../Taps/", "").\
                        replace("homebrew-").replace("/"+name+".rb")
                else:
                    tap_brew = ""
        return (check, tap_brew, opt)

    def check_cask(self):
        """Check applications for Cask"""
        import re
        self.banner("# Starting to check applications for Cask...")

        # First, get App Store applications
        appstore_list = {}
        for p in self.get_appstore_list():  # pragma: no cover
            pinfo = p.split()
            identifier = pinfo[0]
            if identifier.isdigit() and len(identifier) == 9:
                package = " ".join(pinfo[1:])
            else:
                identifier = ""
                package = p
            (pname, version) = package.split("(")
            appstore_list[pname.strip()] = [identifier, "(" + version]

        # Get cask list, force to install brew-cask
        # if it has not been installed.
        (ret, installed_casks) = self.get_cask_list(True)

        # Set cask directories and reset application information list
        taps = list(filter(
            lambda t: os.path.isdir(self.brewinfo.get_tap_path(t) + "/Casks"),
            self.proc("brew tap", False, False,
                      env={"HOMEBREW_NO_AUTO_UPDATE": "1"})[1]))
        apps = dict([d, {True: [], False: []}]
                    for d in taps + ["", "appstore"])
        brew_apps = {}

        # Set applications directories
        app_dirs = self.opt["appdirlist"]
        apps_check = {"cask": dict([d, 0] for d in app_dirs),
                      "cask_obsolete": dict([d, 0] for d in app_dirs),
                      "has_cask": dict([d, 0] for d in app_dirs),
                      "brew": dict([d, 0] for d in app_dirs),
                      "appstore": dict([d, 0] for d in app_dirs),
                      "no_cask": dict([d, 0] for d in app_dirs)}

        # Load casks
        casks = {}
        nonapp_casks = []
        casks_noinst = {}
        nonapp_casks_noinst = []
        for t in taps:
            d = self.brewinfo.get_tap_path(t) + "/Casks"
            for cask in list(map(
                    lambda x: x.replace(".rb", ""),
                    filter(lambda y: y.endswith(".rb"), os.listdir(d)))):
                cask_apps = []
                installed = False
                noinst = True
                if cask in installed_casks:
                    noinst = False
                with open(d + "/" + cask + ".rb", "r") as f:
                    content = f.read()
                for l in content.split("\n"):
                    cask_app = ""
                    if re.search("^ *name ", l):
                        cask_app = re.sub("^ *name ", "",
                                          l).strip('"\' ') + ".app"
                    elif re.search("^ *app ", l):
                        cask_app = re.sub("^ *app ", "",
                                          l).strip('"\' ').split("/")[-1]
                    elif re.search("\.app", l):
                        cask_app = l.split(".app")[0].split("/")[-1].\
                            split("'")[-1].split('"')[-1]
                    elif re.search("^ *pkg ", l):
                        cask_app = re.sub("^ *pkg ", "", l).strip('"\' ').\
                            split("/")[-1].replace(".pkg", "")
                    if cask_app != "" and cask_app not in cask_apps:
                        cask_apps.append(cask_app)

                    if not noinst and re.search("^ *version ", l):
                        if os.path.isdir(
                                self.opt["caskroom"] + "/" + cask + "/" +
                                re.sub("^ *version ", "", l).strip('"\': ')):
                            installed = True
                if noinst:
                    if len(cask_apps) == 0:
                        nonapp_casks_noinst.append([cask, t, installed,
                                                    False, content, cask_apps])
                    else:
                        for a in cask_apps:
                            if a in casks_noinst:
                                casks_noinst[a].append(
                                    [cask, t, installed, False,
                                     content, cask_apps])
                            else:
                                casks_noinst[a] = [[cask, t, installed,
                                                    False, content, cask_apps]]
                else:
                    if len(cask_apps) == 0:
                        nonapp_casks.append([cask, t, installed,
                                             False, content, cask_apps])
                    else:
                        for a in cask_apps:
                            casks[a] = [cask, t, installed, False,
                                        content, cask_apps]

        # Get applications
        napps = 0
        for d in app_dirs:
            for app in [x for x in os.listdir(d)
                        if not x.startswith(".") and x != "Utilities" and
                        os.path.isdir(d + "/" + x)]:
                check = "no_cask"
                aname = app.replace(".app", "")
                if aname in appstore_list.keys():  # pragma: no cover
                    tap = "appstore"
                    installed = False
                    if appstore_list[aname][0] != "":
                        name = appstore_list[aname][0] + " " + aname +\
                            " " + appstore_list[aname][1]
                    else:
                        name = ""
                    check = "appstore"
                elif app in casks.keys() or\
                        app.split(".")[0] in casks.keys():
                    app_key = app if app in casks.keys() else app.split(".")[0]
                    tap = casks[app_key][1]
                    installed = casks[app_key][2]
                    name = casks[app_key][0]
                    for a in filter(lambda k: casks[k][0] == name,
                                    casks.keys()):
                        casks[a][3] = True
                    casks[app_key][3] = True
                    if installed:
                        check = "cask"
                    elif name != "":
                        installed = True
                        check = "cask_obsolete"
                else:
                    app_find = app
                    if not app.endswith(".app"):
                        app_find = d + "/" + app
                    (tap_cands, installed, name_cands) = self.find_app(
                        app_find, taps, casks, nonapp_casks,
                        casks_noinst, nonapp_casks_noinst)
                    if len(name_cands) > 0:
                        for name in name_cands:
                            for c in filter(lambda x: x[0] == name,
                                            nonapp_casks):
                                nonapp_casks.remove(c)
                            for a in filter(lambda k: casks[k][0] == name,
                                            casks.keys()):
                                casks[a][3] = True
                    name = ""
                    if installed:
                        check = "cask"
                        name = name_cands[0]
                        tap = tap_cands[0]
                    elif len(name_cands) > 0:
                        for n, t in zip(name_cands, tap_cands):
                            (check, tap, opt) =\
                                self.find_brew_app(n, t)
                            if check == "brew":
                                name = n
                                break
                    if name == "":
                        if len(tap_cands) > 0:
                            for n, t in zip(name_cands, tap_cands):
                                apps[t][installed].append(
                                    (n, d + "/" + app, check))
                        else:
                            name = tap = ""
                if check != "has_cask":
                    if check != "brew":
                        apps[tap][installed].append(
                            (name, d + "/" + app, check))
                    else:
                        if tap not in brew_apps:
                            brew_apps[tap] = []
                        brew_apps[tap].append((name, d + "/" + app, opt))
                apps_check[check][d] += 1
                napps += 1

        # Make list
        casks_in_others = []
        out = Tee("Caskfile", sys.stdout, self.verbose() > 1)

        out.writeln("# Cask applications")
        out.writeln("# Please copy these lines to your Brewfile"
                    " and use with `" + __prog__ + " install`.\n")

        out.writeln("# Main tap repository for " + self.opt["cask_repo"])
        out.writeln("tap " + self.opt["cask_repo"])
        out.writeln("")
        if len(apps[self.opt["cask_repo"]][True]) > 0:
            out.writeln("# Apps installed by Cask in " + self.opt["cask_repo"])
            for (name, app_path, check) in\
                    sorted(x for x in apps[self.opt["cask_repo"]][True]
                           if x[2] != "cask_obsolete"):
                if name not in casks_in_others:
                    out.writeln(
                        "cask " + name +
                        " # " + app_path.replace(os.environ["HOME"], "~"))
                    casks_in_others.append(name)
                else:
                    out.writeln(
                        "#cask " + name +
                        " # " + app_path.replace(os.environ["HOME"], "~"))

            if len([x for x in apps[self.opt["cask_repo"]][True]
                    if x[2] == "cask_obsolete"]) > 0:
                out.writeln(
                    "\n# There are new version for following applications.")
                for (name, app_path, check) in\
                        sorted(x for x in apps[self.opt["cask_repo"]][True]
                               if x[2] == "cask_obsolete"):
                    if name not in casks_in_others:
                        out.writeln(
                            "cask " + name +
                            " # " + app_path.replace(os.environ["HOME"], "~"))
                        casks_in_others.append(name)
                    else:
                        out.writeln(
                            "#cask " + name +
                            " # " + app_path.replace(os.environ["HOME"], "~"))
            out.writeln("")

        if len([x[0] for x in list(casks.values()) + nonapp_casks
                if x[1] == self.opt["cask_repo"] and not x[3]]) > 0:
            out.writeln("# Cask is found, but no applications are found " +
                        "(could be fonts, system settins, " +
                        "or installed in other directory.)")
            for name in sorted(
                    x[0] for x in list(casks.values()) + nonapp_casks
                    if x[1] == self.opt["cask_repo"] and x[2] and not x[3]):
                if name not in casks_in_others:
                    out.writeln("cask " + name)
                    casks_in_others.append(name)
            if len([x[0] for x in list(casks.values()) + nonapp_casks
                   if x[1] == self.opt["cask_repo"] and
                   not x[2] and not x[3]]) > 0:
                out.writeln(
                    "\n# There are new version for following applications.")
                for name in sorted(
                        x[0] for x in list(casks.values()) + nonapp_casks
                        if x[1] == self.opt["cask_repo"] and
                        not x[2] and not x[3]):
                    if name not in casks_in_others:
                        out.writeln("cask install " + name)
                        casks_in_others.append(name)
            out.writeln("")

        if len(apps[self.opt["cask_repo"]][False]) > 0:
            out.writeln("# Apps installed directly instead of by Cask in " +
                        self.opt["cask_repo"])
            for (name, app_path, check) in\
                    sorted(x for x in apps[self.opt["cask_repo"]][False]):
                out.writeln("#cask " + name +
                            " # " + app_path.replace(os.environ["HOME"], "~"))
            out.writeln("")

        for t in filter(lambda x: x != self.opt["cask_repo"] and
                        x != "" and x != "appstore", taps):
            out.writeln("# Casks in " + t)
            out.writeln("tap " + t)
            out.writeln("")
            if len(apps[t][True]) > 0:
                out.writeln("# Apps installed by Cask in " + t)
                for (name, app_path, check) in\
                        sorted(x for x in apps[t][True]
                               if x[2] != "cask_obsolete"):
                    if name not in casks_in_others:
                        out.writeln("cask " + name + " # " +
                                    app_path.replace(os.environ["HOME"], "~"))
                        casks_in_others.append(name)
                    else:
                        out.writeln("#cask " + name + " # " +
                                    app_path.replace(os.environ["HOME"], "~"))

                if len([x for x in apps[t][True]
                        if x[2] == "cask_obsolete"]) > 0:  # pragma: no cover
                    out.writeln(
                        "# There are new version for following applications.")
                    for (name, app_path, check) in\
                            sorted(x for x in apps[t][True]
                                   if x[2] == "cask_obsolete"):
                        if name not in casks_in_others:
                            out.writeln(
                                "cask " + name + " # " +
                                app_path.replace(os.environ["HOME"], "~"))
                            casks_in_others.append(name)
                        else:
                            out.writeln(
                                "#cask " + name + " # " +
                                app_path.replace(os.environ["HOME"], "~"))
                out.writeln("")

            if len([x[0] for x in list(casks.values()) + nonapp_casks
                    if x[1] == t and not x[3]]) > 0:
                out.writeln("# Cask is found, but no applications are found.\n"
                            "# (fonts, system settins, "
                            "or installed in other directory.)")
                for name in sorted(x[0]
                                   for x in list(casks.values()) + nonapp_casks
                                   if x[1] == t and x[2] and not x[3]):
                    if name not in casks_in_others:
                        out.writeln("cask " + name)
                        casks_in_others.append(name)
                if len([x[0] for x in list(casks.values()) + nonapp_casks
                        if x[1] == t and not x[2] and not x[3]]) > 0:
                    out.writeln(
                        "# There are new version for following applications.")
                    for name in sorted(x[0]
                                       for x in list(casks.values()) +
                                       nonapp_casks
                                       if x[1] == t and not x[2] and not x[3]):
                        if name not in casks_in_others:
                            out.writeln("cask " + name)
                            casks_in_others.append(name)
                out.writeln("")

            if len(apps[t][False]) > 0:
                out.writeln(
                    "# Apps installed directly instead of by Cask in " + t)
                for (name, app_path, check) in apps[t][False]:
                        out.writeln("#cask " + name + " # " +
                                    app_path.replace(os.environ["HOME"], "~"))
                out.writeln("")

        if len(brew_apps.keys()) > 0:
            out.writeln("# Apps installed by brew install command")
            if "" in brew_apps:
                for (name, app_path, opt) in brew_apps[""]:
                    out.writeln("brew " + name + " " + opt + " # " +
                                app_path.replace(os.environ["HOME"], "~"))
            for tap in [x for x in brew_apps.keys() if x != ""]:
                out.writeln("tap " + tap)
                for (name, app_path, opt) in brew_apps[tap]:
                    out.writeln("brew " + name + " " + opt + " # " +
                                app_path.replace(os.environ["HOME"], "~"))
            out.writeln("")

        if len(apps["appstore"][False]) > 0:  # pragma: no cover
            out.writeln("# Apps installed from AppStore")
            for x in apps["appstore"][False]:
                print(" ".join(x[0].split()[1:]).lower())
            for (name, app_path, check) in sorted(
                    apps["appstore"][False],
                    key=lambda x: " ".join(x[0].split()[1:]).lower()):
                if name != "":
                    out.writeln("appstore " + name + " # " + app_path)
                else:
                    out.writeln("#appstore # " + app_path)
            out.writeln("")

        if len(apps[""][False]) > 0:
            out.writeln("# Apps installed but no casks are available")
            out.writeln("# (System applications or directory installed.)")
            for (name, app_path, check) in apps[""][False]:
                    out.writeln("# " + app_path)

        out.close()

        # Summary
        self.banner("# Summary")
        if self.verbose() > 0:
            print("Total:", napps, "apps have been checked.")
            print("Apps in",
                  [d.replace(os.environ["HOME"], "~") for d in app_dirs], "\n")
            maxlen = max(len(x.replace(os.environ["HOME"], "~"))
                         for x in app_dirs)
            if sum(apps_check["cask"].values()) > 0:
                print("Installed by Cask:")
                for d in app_dirs:
                    if apps_check["cask"][d] == 0:
                        continue
                    print("{0:<{1}s} : {2:d}".format(d.replace(
                        os.environ["HOME"], "~"), maxlen,
                        apps_check["cask"][d]))
                print("")
            if sum(apps_check["cask_obsolete"].values())\
                    > 0:  # pragma: no cover
                print("Installed by Cask (New version is availble, " +
                      "try `brew cask upgrade`):")
                for d in app_dirs:
                    if apps_check["cask_obsolete"][d] == 0:
                        continue
                    print("{0:<{1}s} : {2:d}".format(d.replace(
                        os.environ["HOME"], "~"), maxlen,
                        apps_check["cask_obsolete"][d]))
                print("")
            if sum(apps_check["brew"].values()) > 0:
                print("Installed by brew install command")
                for d in app_dirs:
                    if apps_check["brew"][d] == 0:
                        continue
                    print("{0:<{1}s} : {2:d}".format(d.replace(
                        os.environ["HOME"], "~"), maxlen,
                        apps_check["brew"][d]))
                print("")
            if sum(apps_check["has_cask"].values()) > 0:
                print("Installed directly, but casks are available:")
                for d in app_dirs:
                    if apps_check["has_cask"][d] == 0:
                        continue
                    print("{0:<{1}s} : {2:d}".format(d.replace(
                        os.environ["HOME"], "~"), maxlen,
                        apps_check["has_cask"][d]))
                print("")
            if sum(apps_check["appstore"].values()) > 0:  # pragma: no cover
                print("Installed from Appstore")
                for d in app_dirs:
                    if apps_check["appstore"][d] == 0:
                        continue
                    print("{0:<{1}s} : {2:d}".format(d.replace(
                        os.environ["HOME"], "~"), maxlen,
                        apps_check["appstore"][d]))
                print("")
            if sum(apps_check["no_cask"].values()) > 0:
                print("No casks")
                for d in app_dirs:
                    if apps_check["no_cask"][d] == 0:
                        continue
                    print("{0:<{1}s} : {2:d}".format(d.replace(
                        os.environ["HOME"], "~"), maxlen,
                        apps_check["no_cask"][d]))
                print("")

    def make_pack_deps(self):
        """Make package dependencies"""
        packs = self.get("brew_list")
        self.pack_deps = {}
        for p in packs:
            deps = self.proc("brew deps --1 " + p, False, False)[1]
            self.pack_deps[p] = []
            for d in deps:
                if d in packs:
                    self.pack_deps[p].append(d)
        dep_packs = []
        for v in self.pack_deps.values():
            dep_packs.extend(v)
        self.top_packs = [x for x in packs if x not in dep_packs]
        if self.opt["verbose"] > 1:
            def print_dep(p, depth=0):
                if depth != 0:
                    print("#", end="")
                    for i in range(depth-2):
                        print(" ", end="")
                print(p)
                for deps in self.pack_deps[p]:
                    print_dep(deps, depth+2)
            for p in packs:
                if p not in dep_packs:
                    print_dep(p)

    def my_test(self):
        self.make_pack_deps()

        out = Tee("test_file")
        out.write("test\n")
        out.close()
        out = Tee(sys.stdout, "test_file")
        out.write("test\n")
        out.flush()
        out.close()
        self.remove("test_file")
        os.mkdir("dir")
        self.remove("dir")
        self.remove("aaa")
        self.brewinfo.read()
        print("read input:", len(self.brewinfo.brew_input))
        self.brewinfo.clear()
        print("read input cleared:", len(self.brewinfo.brew_input))
        self.brewinfo.set_file("/test/not/correct/file/path")
        self.brewinfo.read()
        self.brewinfo.check_dir()
        self.brewinfo.set_val("brew_input_opt", {"test_pack": "test opt"})
        self.brewinfo.add("brew_input_opt", {"test_pack2": "test opt2"})
        print(self.brewinfo.get("brew_input_opt"))
        self.brewinfo.read("testfile")
        self.brewinfo.get_tap("/aaa/bbb")

    def execute(self):
        """Main execute function"""
        # Cask list check
        if self.opt["command"] == "casklist":
            self.check_cask()
            sys.exit(0)

        # Set BREWFILE repository
        if self.opt["command"] == "set_repo":
            self.set_brewfile_repo()
            sys.exit(0)

        # Set BREWFILE to local file
        if self.opt["command"] == "set_local":
            self.set_brewfile_local()
            sys.exit(0)

        # Change brewfile if it is repository's one.
        self.check_repo()

        # Do pull/push for the repository.
        if self.opt["command"] in ["pull", "push"]:
            self.repomgr(self.opt["command"])
            sys.exit(0)

        # brew command
        if self.opt["command"] == "brew":
            self.brew_cmd()
            sys.exit(0)

        # Initialize
        if self.opt["command"] in ["init", "dump"]:
            self.initialize()
            sys.exit(0)

        # Check input file
        # If the file doesn't exist, initialize it.
        self.check_input_file()

        # Edit
        if self.opt["command"] == "edit":
            self.edit_brewfile()
            sys.exit(0)

        # Cat
        if self.opt["command"] == "cat":
            self.cat_brewfile()
            sys.exit(0)

        # Get files
        if self.opt["command"] == "get_files":
            self.get_files(is_print=True)
            sys.exit(0)

        # Cleanup
        if self.opt["command"] == "clean_non_request":
            self.clean_non_request()
            sys.exit(0)

        # Get list for cleanup/install
        self.get_list()

        # Cleanup
        if self.opt["command"] == "clean":
            self.cleanup()
            sys.exit(0)

        # Install
        if self.opt["command"] == "install":
            self.install()
            sys.exit(0)

        # Update
        if self.opt["command"] == "update":
            if not self.opt["noupgradeatupdate"]:
                self.proc("brew update")
                self.proc("brew upgrade --fetch-HEAD")
                self.proc("brew cask upgrade")
            if self.opt["repo"] != "":
                self.repomgr("pull")
            self.install()
            if not self.opt["dryrun"]:
                self.cleanup()
            self.initialize(False)
            if self.opt["repo"] != "":
                self.repomgr("push")
            sys.exit(0)

        # test
        if self.opt["command"] == "test":
            self.my_test()
            sys.exit(0)

        # No command found
        self.err("Wrong command: " + self.opt["command"],
                 0)  # pragma: no cover
        self.err("Execute `" + __prog__ +
                 " help` for more information.", 0)  # pragma: no cover
        sys.exit(1)  # pragma: no cover


def main():
    # Prepare BrewFile
    b = BrewFile()

    import argparse

    # Pre Parser
    pre_parser = argparse.ArgumentParser(
        add_help=False, usage=__prog__+"...")
    group = pre_parser.add_mutually_exclusive_group()
    group.add_argument("-i", "--init", action="store_const",
                       dest="command", const="init")
    group.add_argument("-s", "--set_repo", action="store_const",
                       dest="command", const="set_repo")
    group.add_argument("--set_local", action="store_const",
                       dest="command", const="set_local")
    group.add_argument("-c", "--clean", action="store_const",
                       dest="command", const="clean")
    group.add_argument("-u", "--update", action="store_const",
                       dest="command", const="update")
    group.add_argument("-e", "--edit", action="store_const",
                       dest="command", const="edit")
    group.add_argument("--cat", action="store_const",
                       dest="command", const="cat")
    group.add_argument("--test", action="store_const",
                       dest="command", const="test")
    group.add_argument("--commands", action="store_const",
                       dest="command", const="commands")
    group.add_argument("-v", "--version", action="store_const",
                       dest="command", const="version")

    # Parent parser
    file_parser = argparse.ArgumentParser(add_help=False)
    file_parser.add_argument(
        "-f", "--file", action="store", dest="input",
        default=b.opt["input"],
        help="Set input file (default: %(default)s). \n"
              "You can set input file by environmental variable,\n"
              "HOMEBREW_BREWFILE, like:\n"
              "    export HOMEBREW_BREWFILE=~/.brewfile")

    backup_parser = argparse.ArgumentParser(add_help=False)
    backup_parser.add_argument(
        "-b", "--backup", action="store", dest="backup",
        default=b.opt["backup"],
        help="Set backup file (default: %(default)s). \n"
             "If it is empty, no backup is made.\n"
             "You can set backup file by environmental variable,\n"
             " HOMEBREW_BREWFILE_BACKUP, like:\n"
             "    export HOMEBREW_BREWFILE_BACKUP=~/brewfile.backup")

    format_parser = argparse.ArgumentParser(add_help=False)
    format_parser.add_argument(
        "-F", "--format", "--form", action="store", dest="form",
        default=b.opt["form"],
        help="Set input file format (default: %(default)s). \n"
              "file (or none)    : brew vim --HEAD --with-lua\n"
              "brewdler or bundle: brew 'vim', args: ['with-lua', 'HEAD']\n"
              "  Compatible with "
              "[homebrew-bundle]"
              "(https://github.com/Homebrew/homebrew-bundle).\n"
              "command or cmd    : brew install vim --HEAD --with-lua\n"
              "  Can be used as a shell script.\n")

    leaves_parser = argparse.ArgumentParser(add_help=False)
    leaves_parser.add_argument(
        "--leaves", action="store_true", default=b.opt["leaves"],
        dest="leaves",
        help="Make list only for leaves (taken by `brew leaves`).\n"
             "You can set this by environmental variable,"
             " HOMEBREW_BREWFILE_LEAVES, like:\n"
             "    export HOMEBREW_BREWFILE_LEAVES=1")

    on_request_parser = argparse.ArgumentParser(add_help=False)
    on_request_parser.add_argument(
        "--on_request", action="store_true", default=b.opt["on_request"],
        dest="on_request",
        help="Make list only for packages installed on request.\n"
             "This option is given priority over 'leaves'.\n"
             "You can set this by environmental variable,"
             " HOMEBREW_BREWFILE_ON_REQUEST, like:\n"
             "    export HOMEBREW_BREWFILE_ON_REQUEST=1")

    top_packages_parser = argparse.ArgumentParser(add_help=False)
    top_packages_parser.add_argument(
        "--top_packages", action="store", default=b.opt["top_packages"],
        dest="top_packages",
        help="Packages to be listed even if they are under dependencies\n"
             "and `leaves`/'on_request' option is used.\n"
             "You can set this by environmental variable,\n"
             " HOMEBREW_BREWFILE_TOP_PACKAGES (',' separated), like:\n"
             "    export HOMEBREW_BREWFILE_TOP_PACKAGES=go,coreutils")

    noupgradeatupdate_parser = argparse.ArgumentParser(add_help=False)
    noupgradeatupdate_parser.add_argument(
        "-U", "--noupgrade", action="store_true",
        default=b.opt["noupgradeatupdate"], dest="noupgradeatupdate",
        help="Do not execute `brew update/brew upgrade`"
             " at `brew file update`.")

    repo_parser = argparse.ArgumentParser(add_help=False)
    repo_parser.add_argument(
        "-r", "--repo", action="store", default=b.opt["repo"], dest="repo",
        help="Set repository name. Use with set_repo.")

    link_parser = argparse.ArgumentParser(add_help=False)
    link_parser.add_argument(
        "-n", "--nolink", action="store_false", default=b.opt["link"],
        dest="link", help="Don't make links for Apps.")

    caskonly_parser = argparse.ArgumentParser(add_help=False)
    caskonly_parser.add_argument(
        "--caskonly", action="store_true", default=b.opt["caskonly"],
        dest="caskonly", help="Write out only cask related packages")

    appstore_parser = argparse.ArgumentParser(add_help=False)
    appstore_parser.add_argument(
        "--no_appstore", action="store_false", default=b.opt["appstore"],
        dest="appstore", help="Don't check AppStore applications.\n"
             "(For other than casklist command.)\n"
             "You can set input file by environmental variable:\n"
             "    export HOMEBREW_BRWEFILE_APPSTORE=0")

    dryrun_parser = argparse.ArgumentParser(add_help=False)
    dryrun_parser.add_argument(
        "-C", action="store_false", default=b.opt["dryrun"],
        dest="dryrun", help="Run clean as non dry-run mode.\n"
        "Use this option to run clean at update command, too.")

    yn_parser = argparse.ArgumentParser(add_help=False)
    yn_parser.add_argument(
        "-y", "--yes", action="store_true", default=b.opt["yn"],
        dest="yn", help="Answer yes to all yes/no questions.")

    verbose_parser = argparse.ArgumentParser(add_help=False)
    verbose_parser.add_argument("-V", "--verbose", action="store",
                                default=b.opt["verbose"],
                                dest="verbose", help="Verbose level 0/1/2")

    help_parser = argparse.ArgumentParser(add_help=False)
    help_parser.add_argument("-h", "--help", action="store_true",
                             default=False, dest="help",
                             help="Print Help (this message) and exit.")

    min_parsers = [file_parser, backup_parser, format_parser, leaves_parser,
                   on_request_parser, top_packages_parser, appstore_parser,
                   caskonly_parser, yn_parser, verbose_parser]
    subparser_options = {
        "parents": min_parsers,
        "formatter_class": argparse.RawTextHelpFormatter}

    # Main parser
    parser = argparse.ArgumentParser(
        add_help=False, prog=__prog__,
        parents=[file_parser, backup_parser, format_parser, leaves_parser,
                 on_request_parser, top_packages_parser,
                 noupgradeatupdate_parser, repo_parser, link_parser,
                 caskonly_parser, appstore_parser, dryrun_parser, yn_parser,
                 verbose_parser, help_parser],
        formatter_class=argparse.RawTextHelpFormatter,
        description=__description__)

    subparsers = parser.add_subparsers(
        title="subcommands", metavar="[command]", help="", dest="command")

    help = "Install packages in BREWFILE."
    subparsers.add_parser("install", description=help, help=help,
                          **subparser_options)
    help = "Execute brew command, and update BREWFILE."
    subparsers.add_parser("brew", description=help, help=help,
                          parents=min_parsers, add_help=False,
                          formatter_class=argparse.RawTextHelpFormatter)
    help = "or dump/-i/--init\nInitialize/Update BREWFILE "\
        "with installed packages."
    subparsers.add_parser(
        "init", description=help, help=help,
        parents=min_parsers+[link_parser, repo_parser],
        formatter_class=argparse.RawTextHelpFormatter)
    subparsers.add_parser(
        "dump",
        parents=min_parsers+[link_parser, repo_parser],
        formatter_class=argparse.RawTextHelpFormatter)
    help = "or -s/--set_repo\nSet BREWFILE repository (e.g. rcmdnk/Brewfile)."
    subparsers.add_parser(
        "set_repo", description=help, help=help,
        parents=min_parsers+[repo_parser],
        formatter_class=argparse.RawTextHelpFormatter)
    help = "or --set_local\nSet BREWFILE to local file."
    subparsers.add_parser(
        "set_local", description=help, help=help,
        parents=min_parsers,
        formatter_class=argparse.RawTextHelpFormatter)
    help = "Update BREWFILE from the repository."
    subparsers.add_parser("pull", description=help, help=help,
                          **subparser_options)
    help = "Push your BREWFILE to the repository."
    subparsers.add_parser("push", description=help, help=help,
                          **subparser_options)
    help = "or -c/--clean\nCleanup.\n"\
           "Uninstall packages not in the list.\n"\
           "Untap packages not in the list.\n"\
           "Cleanup cache (brew cleanup)\n"\
           "By default, cleanup runs as dry-run.\n"\
           "If you want to enforce cleanup, use '-C' option."
    subparsers.add_parser(
        "clean", description=help, help=help,
        parents=min_parsers+[dryrun_parser],
        formatter_class=argparse.RawTextHelpFormatter)
    help = "or --clean_non_request.\n"\
           "Uninstall packages which were installed as dependencies \n"\
           "but parent packages of which were already uninstalled.\n"\
           "By default, cleanup runs as dry-run.\n"\
           "If you want to enforce cleanup, use '-C' option."
    subparsers.add_parser(
        "clean_non_request", description=help, help=help,
        parents=min_parsers+[dryrun_parser],
        formatter_class=argparse.RawTextHelpFormatter)
    help = "or -u/--update\nDo brew update/upgrade, cask upgrade, pull, install,\n"\
           "init and push.\n"\
           "In addition, pull and push\n"\
           "will be done if the repository is assigned.\n"\
           "'clean' is also executed after install if you give -C option."
    subparsers.add_parser(
        "update", description=help, help=help,
        parents=min_parsers+[link_parser, noupgradeatupdate_parser,
                             dryrun_parser],
        formatter_class=argparse.RawTextHelpFormatter)
    help = "or -e/--edit\nEdit input files."
    subparsers.add_parser("edit", description=help, help=help,
                          **subparser_options)
    help = "or --cat\nShow contents of input files."
    subparsers.add_parser("cat", description=help, help=help,
                          **subparser_options)
    help = "Check applications for Cask."
    subparsers.add_parser("casklist", description=help, help=help,
                          parents=[verbose_parser],
                          formatter_class=argparse.RawTextHelpFormatter)
    help = "or --test. Used for test."
    subparsers.add_parser("test", description=help, help=help,
                          parents=min_parsers,
                          formatter_class=argparse.RawTextHelpFormatter)
    help = "Get Brewfile's full path, including additional files."
    subparsers.add_parser("get_files", description=help, help=help,
                          formatter_class=argparse.RawTextHelpFormatter)
    help = "or --commands\nShow commands."
    subparsers.add_parser("commands", description=help, help=help,
                          formatter_class=argparse.RawTextHelpFormatter)
    help = "or -v/--version\nShow version."
    subparsers.add_parser("version", description=help, help=help,
                          formatter_class=argparse.RawTextHelpFormatter)
    help = "or -h/--help\nPrint Help (this message) and exit.\n\n"\
        "Check https://homebrew-file.readthedocs.io for more details."
    subparsers.add_parser("help", description=help, help=help,
                          formatter_class=argparse.RawTextHelpFormatter)

    if len(sys.argv) == 1:
        parser.print_usage()
        print("")
        print("Execute `" + __prog__ + " help` to get help.")
        print("")
        print("Refer https://homebrew-file.readthedocs.io for more details.")
        sys.exit(1)

    if sys.argv[1] == "brew":
        args = sys.argv[1:]
        if len([x for x in args if x.startswith("-")]) > 0:
            v = sys.version_info
            if v.major == 2 and (
                    v.minor < 7 or(
                        v.minor == 7 and v.micro < 7)):  # pragma: no cover
                print("`brew-file brew ...` with option is available "
                      "only with Python 2.7.7 or later.\n"
                      "(Such Yosemite's default is 2.7.6.)\n"
                      "You can easily install newer version with Homebrew, "
                      "like:\n"
                      "    $ brew install python")
                sys.exit(1)
    else:
        (ns, args) = pre_parser.parse_known_args()
        if ns.command is not None:
            args = [ns.command] + args
        else:
            for a in args:
                if a in subparsers.choices.keys():
                    args.remove(a)
                    args = [a] + args
                    break
        if args[0] in ["-h", "--help"]:
            args[0] = "help"
    (ns, args_tmp) = parser.parse_known_args(args)
    args = vars(ns)
    args.update({"args": args_tmp})

    b.set_args(**args)

    if b.opt["command"] == "help":
        parser.print_help()
        sys.exit(0)
    elif b.opt["command"] == "brew":
        if len(args_tmp) > 0 and args_tmp[0] in ["-h", "--help"]:
            subparsers.choices[b.opt["command"]].print_help()
            sys.exit(0)
    elif "help" in args_tmp:
        subparsers.choices[b.opt["command"]].print_help()
        sys.exit(0)
    elif b.opt["command"] == "commands":
        commands = ["install", "brew", "init", "dump", "set_repo", "set_local",
                    "pull", "push", "clean", "clean_non_request", "update",
                    "edit", "cat", "casklist", "test",
                    "get_files", "commands", "version", "help"]
        commands_hyphen = ["-i", "--init", "-s", "--set_repo", "--set_local",
                           "-c", "--clean", "--clean_non_request", "-u",
                           "--update", "-e", "--edit", "--cat", "--test",
                           "--commands", "-v", "--version", "-h", "--help"]
        options = ["-f", "--file", "-b", "--backup",
                   "-F", "--format", "--form", "--leaves", "--on_request",
                   "--top_packages", "-U", "--noupgrade", "-r", "--repo", "-n",
                   "--nolink", "--caskonly", "--no_appstore", "-C",
                   "-y", "--yes", "-V", "--verbose"]
        print("commands:", " ".join(commands))
        print("commands_hyphen:", " ".join(commands_hyphen))
        print("options:", " ".join(options))
        sys.exit(0)
    elif b.opt["command"] == "version":
        b.proc("brew -v", False)
        print(__prog__ + " " + __version__ + " " + __date__)
        sys.exit(0)

    b.execute()


if __name__ == "__main__":
    main()
