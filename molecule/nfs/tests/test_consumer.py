testinfra_hosts = ["consumer.osgiliath.test"]

def test_nfs_is_mounted(host):
    with host.sudo():
        command = r"""df -h | \
        egrep -c 'datastore\.osgiliath\.test:/var/nfs.*/net'"""
        cmd = host.run(command)
    assert '1' in cmd.stdout
