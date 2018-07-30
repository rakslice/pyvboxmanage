"""
A library around functionality for managing VirtualBox virtual machines provided by the VBoxManage tool.
"""

import os
import sys
import subprocess


if sys.platform == "win32":
    LINE_SEPARATOR = "\r\n"
else:
    LINE_SEPARATOR = "\n"


def chomp_platform_newline(s):
    assert s.endswith(LINE_SEPARATOR)
    s = s[:-len(LINE_SEPARATOR)]
    return s


def read_registry_string_from_hklm(key_path, value_name):
    import _winreg
    key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, key_path, 0, _winreg.KEY_READ | _winreg.KEY_WOW64_64KEY)
    try:
        value, type_id = _winreg.QueryValueEx(key, value_name)
        assert type_id == _winreg.REG_SZ
        return value
    finally:
        _winreg.CloseKey(key)


def parse_colon_tab_dict_list(output):
    l = []
    cur = {}
    for line in output.split(LINE_SEPARATOR):
        if line == "":
            if cur != {}:
                l.append(cur)
                cur = {}
        else:
            if ":" not in line:
                continue
            try:
                key, val = line.split(":", 1)
            except ValueError:
                print repr(line)
                raise
            val = val.strip()
            cur[key] = val
    if cur != {}:
        l.append(cur)
    return l


class VBoxManage(object):
    def __init__(self):
        self.vboxmanage_cmd = self.find_vboxmanage_cmd()

    ENUM_TYPE_OSTYPES = "ostypes"

    NIC_TYPE_PCNET_FAST_3 = "Am79C973"
    NIC_TYPE_PCNET_PCI_2 = "Am79C970A"

    @staticmethod
    def find_vboxmanage_cmd():
        if sys.platform == "win32":
            vbox_dir = read_registry_string_from_hklm(r"SOFTWARE\Oracle\VirtualBox", r"InstallDir")
            assert os.path.isdir(vbox_dir)
            vboxmanage_filename = os.path.join(vbox_dir, "VBoxManage.exe")
            assert os.path.isfile(vboxmanage_filename)
            return vboxmanage_filename
        else:
            return "VBoxManage"

    def run_cmd(self, args):
        """:type args: list of str"""
        subprocess.check_call([self.vboxmanage_cmd] + args)

    def run_cmd_output(self, args):
        """:type args: list of str"""
        return subprocess.check_output([self.vboxmanage_cmd] + args)

    def version(self):
        return chomp_platform_newline(self.run_cmd_output(["-v"]))

    def list(self, enum_type):
        """
        List selectable things
        :type enum_type: str
        :param enum_type: typically one of the ENUM_TYPES_* constants
        """
        output = self.run_cmd_output(["list", enum_type])
        return parse_colon_tab_dict_list(output)

    def create_vm(self, vm_name, os_type):
        """
        :type vm_name: unicode
        :type os_type: str
        """
        self.run_cmd(["createvm", "--name", vm_name.encode("utf-8"), "--ostype", os_type, "--register"])

    def set_ram_size(self, vm_name, ram_mb):
        """:type vm_name: unicode
        :type ram_mb: int"""
        self.run_cmd(["modifyvm", vm_name.encode("utf-8"), "--memory", str(ram_mb)])

    def vm_exists(self, vm_name):
        """:type vm_name: unicode"""
        try:
            self.run_cmd(["showvminfo", vm_name.encode("utf-8")])
        except subprocess.CalledProcessError, e:
            assert e.returncode == 1
            return False
        return True

    def create_hd(self, hd_filename, hd_size_mb):
        """:type hd_filename: unicode
        :type hd_size_mb: int"""
        self.run_cmd(["createmedium", "disk",
                      "--filename", hd_filename.encode("utf-8"),
                      "--size", str(hd_size_mb),
                      "--variant", "Standard",
                      ])

    def ensure_ide(self, vm_name):
        if "ide0" not in self.get_storage_controller_names(vm_name):
            self.run_cmd(["storagectl", vm_name.encode("utf-8"), "--add", "ide", "--name", "ide0"])

    def attach_ide_hd(self, vm_name, hd_filename, port, device):
        """:type vm_name: unicode
        :type hd_filename: unicode
        :type port: int
        :type device:int
        """
        self.run_cmd(["storageattach", vm_name.encode("utf-8"),
                      "--storagectl", "ide0",
                      "--type", "hdd",
                      "--medium", hd_filename.encode("utf-8"),
                      "--port", str(port),
                      "--device", str(device),
                      ])

    def attach_optical(self, vm_name, iso_filename, port, device):
        """:type vm_name: unicode
        :type iso_filename: unicode
        :type port: int
        :type device:int
        """
        self.run_cmd(["storageattach", vm_name.encode("utf-8"),
                      "--storagectl", "ide0",
                      "--type", "dvddrive",
                      "--medium", iso_filename.encode("utf-8"),
                      "--port", str(port),
                      "--device", str(device),
                      ])

    def remove_optical(self, vm_name, port, device):
        """:type vm_name: unicode
        :type port: int
        :type device:int
        """
        print self.get_storage_controller_names(vm_name)
        self.run_cmd(["storageattach", vm_name.encode("utf-8"),
                      "--storagectl", "ide0",
                      "--port", str(port),
                      "--device", str(device),
                      "--medium", "emptydrive",
                      ])

    def ensure_floppy_controller(self, vm_name):
        """:type vm_name: unicode"""
        if "floppy0" not in self.get_storage_controller_names(vm_name):
            self.run_cmd(["storagectl", vm_name.encode("utf-8"), "--add", "floppy", "--name", "floppy0"])

    def attach_floppy(self, vm_name, floppy_image_filename, device):
        """:type vm_name: unicode
        :type floppy_image_filename: unicode
        :type device: int
        """
        self.run_cmd(["storageattach", vm_name.encode("utf-8"),
                      "--storagectl", "floppy0",
                      "--type", "fdd",
                      "--medium", floppy_image_filename.encode("utf-8"),
                      "--device", str(device),
                      ])

    def start_vm(self, vm_name):
        """:type vm_name: unicode"""
        self.run_cmd(["startvm", vm_name.encode("utf-8")])

    def get_storage_controller_names(self, vm_name):
        """:type vm_name: unicode"""
        entries = parse_colon_tab_dict_list(self.run_cmd_output(["showvminfo", vm_name.encode("utf-8")]))
        assert len(entries) >= 1
        entry = entries[0]

        controller_names = []
        for key in entry.keys():
            if key.startswith("Storage Controller Name "):
                controller_name = entry[key]
                controller_names.append(controller_name)
        print controller_names
        return controller_names

    def set_nic_type(self, vm_name, nic_type):
        """:type vm_name: unicode
        :type nic_type: str"""
        self.run_cmd(["modifyvm", vm_name.encode("utf-8"), "--nictype1", nic_type])

    def nat_forward_port(self, vm_name, rule_name, host_port, guest_port):
        """
        :type vm_name: unicode
        :type rule_name: str
        :type host_port: int
        :type guest_port: int
        """
        self.run_cmd(["modifyvm", vm_name.encode("utf-8"), "--natpf1", "%s,tcp,,%d,,%d" % (rule_name, host_port, guest_port)])
