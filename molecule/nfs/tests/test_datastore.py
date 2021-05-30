testinfra_hosts = ["datastore.osgiliath.test"]


def test_nfs_is_exported(host):
    with host.sudo():
        command = """exportfs | egrep -c '/var/nfs.*world'"""
        cmd = host.run(command)
    assert '1' in cmd.stdout


def test_nfs_keytab_is_configured(host):
    with host.sudo():
        command = """ipa service-show nfs/datastore.osgiliath.test | \
        grep -c 'Keytab: True'"""
        cmd = host.run(command)
    assert '1' in cmd.stdout


def test_nfs_server_is_running(host):
    with host.sudo():
        command = """service nfs-server status | grep -c 'active'"""
        cmd = host.run(command)
    assert int(cmd.stdout.rstrip()) >= 1
