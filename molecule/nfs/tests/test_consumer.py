testinfra_hosts = ["consumer.osgiliath.test"]

# TODO try to make this one working
# def test_nfs_is_mounted(host):
#    with host.sudo():
#        command = r"""mount | \
#        grep -c 'auto.consumer.osgiliath.test.net on /net type autofs'"""
#        cmd = host.run(command)
#    assert '1' in cmd.stdout


# TODO remove once automount is working
def test_nfs_is_mounted_through_fstab(host):
    with host.sudo():
        command = r"""mount | \
        grep -c 'datastore.osgiliath.test:/var/nfs on /net type nfs4'"""
        cmd = host.run(command)
    assert '1' in cmd.stdout


def test_autofs_is_activated_in_sssd(host):
    with host.sudo():
        command = r"""cat /etc/sssd/sssd.conf | \
        egrep -c 'services.*=.*autofs'"""
        cmd = host.run(command)
    assert '1' in cmd.stdout
