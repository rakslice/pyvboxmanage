from pyvboxmanage import VBoxManage


def main():
    v = VBoxManage()
    print "VirtualBox version is %r" % v.version()

    for entry in v.list(v.ENUM_TYPE_OSTYPES):
        print entry

    # assert v.vm_exists(u"i do not exist") == False


if __name__ == "__main__":
    main()
