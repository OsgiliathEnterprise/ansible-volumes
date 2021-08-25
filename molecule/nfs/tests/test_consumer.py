testinfra_hosts = ["consumer.osgiliath.test"]


def test_nfs_is_mounted(host):
    with host.sudo():
        command = r"""mount | \
        grep -c 'auto.consumer.osgiliath.test.net on /net type autofs'"""
        cmd = host.run(command)
    assert '1' in cmd.stdout
