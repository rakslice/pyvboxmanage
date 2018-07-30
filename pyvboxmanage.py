"""
A library around functionality for managing VirtualBox virtual machines provided by the VBoxManage tool.
"""
import os

import sys

import subprocess


def chomp_newline(s):
    if sys.platform == "win32":
        assert s.endswith("\r\n")
        s = s[:-2]
    else:
        assert s.endswith("\n")
        s = s[:-1]
    return s


def read_registry_string_from_hklm(key_path, value_name):
    import _winreg as winreg
    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
    try:
        value, type_id = winreg.QueryValueEx(key, value_name)
        assert type_id == winreg.REG_SZ
        return value
    finally:
        winreg.CloseKey(key)


class VBoxManage(object):
    def __init__(self):
        self.vboxmanage_cmd = self.find_vboxmanage_cmd()

    def find_vboxmanage_cmd(self):
        if sys.platform == "win32":
            vbox_dir = read_registry_string_from_hklm(r"SOFTWARE\Oracle\VirtualBox", r"InstallDir")
            assert os.path.isdir(vbox_dir)
            vboxmanage_filename = os.path.join(vbox_dir, "VBoxManage.exe")
            assert os.path.isfile(vboxmanage_filename)
            return vboxmanage_filename
        else:
            return "VBoxManage"

    def run_cmd(self, args):
        subprocess.check_call([self.vboxmanage_cmd] + args)

    def run_cmd_output(self, args):
        return subprocess.check_output([self.vboxmanage_cmd] + args)

    def version(self):
        return chomp_newline(self.run_cmd_output(["-v"]))
