from pyvboxmanage import VBoxManage


def main():
    v = VBoxManage()
    print "VirtualBox version is %r" % v.version()


if __name__ == "__main__":
    main()
