Volumes
=========

* Galaxy: [![Ansible Galaxy](https://img.shields.io/badge/galaxy-tcharl.ansible_volumes-660198.svg?style=flat)](https://galaxy.ansible.com/tcharl/ansible_volumes)
* Lint & requirements: ![Molecule](https://github.com/OsgiliathEnterprise/ansible-volumes/workflows/Molecule/badge.svg)
* Tests: [![Build Status](https://travis-ci.org/OsgiliathEnterprise/ansible-volumes.svg?branch=master)](https://travis-ci.org/OsgiliathEnterprise/ansible-volumes)
* Chat: [![Join the chat at https://gitter.im/OsgiliathEnterprise/platform](https://badges.gitter.im/OsgiliathEnterprise/platform.svg)](https://gitter.im/OsgiliathEnterprise/platform?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

This role is an extension of the [most used lvm cookbook](https://github.com/mrlesmithjr/ansible-manage-lvm).
It add the ability to create thinpools and their associated metadata

Role Variables
--------------

In addition to the [usual variables](https://github.com/mrlesmithjr/ansible-manage-lvm/blob/master/README.md), you can declare some more in order to configure thinpools

```yaml
---
lvmetanames:
  ...
  metadata: <another lvname> # declares the metadata logical volume 
```

```yaml
---
lvmetanames:
  ...
  autoextendtreshold: <number> # threshold of the autoextend profile
  autoextendpercent: <number> # percentage of the autoextend profile
```

Full example
```yaml
---
  vars:
    lvm_groups:
      - vgname: myvg
        disks:
          - /dev/sdb1
        create: true
        lvnames:
          - lvname: notathinpool # original role
            size: 40%VG
            opts: "" 
            create: true
            filesystem: xfs
            mntp: /var/stuff
            mount: true
        lvmetanames:
          - lvname: thinpool
            size: 40%VG
            opts: "--wipesignatures y"
            create: true
            metadata: myvg/thinpoolmeta
            autoextendtreshold: 80
            autoextendpercent: 20
            filesystem: xfs
            mntp: /var/lib/docker
            mount: true
          - lvname: thinpoolmeta
            size: 10%VG
            opts: "--wipesignatures y"
            create: true
    manage_lvm: true
```


Dependencies
------------

As said, [mrlesmithjr.ansible-manage-lvm](https://github.com/mrlesmithjr/ansible-manage-lvm)

Example Playbook
----------------

See the [vars declared](https://github.com/OsgiliathEnterprise/ansible-volumes/blob/master/molecule/default/molecule.yml) on the molecule test, as well as [their impact](https://github.com/OsgiliathEnterprise/ansible-manage-lvm-plus/blob/master/molecule/default/tests/test_default.py) 

License
-------

[Apache-2](https://www.apache.org/licenses/LICENSE-2.0)

Author Information
------------------

* Twitter [@tcharl](https://twitter.com/Tcharl)
* Github [@tcharl](https://github.com/Tcharl)
* LinkedIn [Charlie Mordant](https://www.linkedin.com/in/charlie-mordant-51796a97/)