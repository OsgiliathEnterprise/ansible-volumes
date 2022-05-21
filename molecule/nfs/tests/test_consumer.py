testinfra_hosts = ["consumer.osgiliath.test"]


def test_autofs_is_activated_in_sssd(host):
    with host.sudo():
        command = r"""cat /etc/sssd/sssd.conf | \
        egrep -c 'services.*=.*autofs'"""
        cmd = host.run(command)
    assert '1' in cmd.stdout


def test_nfs_is_mounted_through_autofs(host):
    with host.sudo():
        command = r"""
        echo '123ADMin' | \
        kinit admin > /dev/null && \
        mount | \
        grep -c 'auto.consumer.osgiliath.test.net on /net type autofs'"""
        cmd = host.run(command)
    assert '1' in cmd.stdout
