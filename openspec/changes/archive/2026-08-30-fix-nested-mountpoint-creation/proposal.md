# Proposal: fix nested mount point creation for LVM filesystems

## Why

The role fails when a logical volume defines a mount point whose parent directories do not exist yet (e.g. `mntp: /var/nfs/volume` while only `/var` exists). The vendored dependency `mrlesmithjr.manage_lvm` runs `xfs_growfs <mntp>` on every newly created xfs LV (`tasks/create_fs.yml:85`) without checking that the mount point was actually mounted — its `when` conditions lack the `lv.mount|bool` guard that the preceding mount task has. Since this role passes `mount: "{{ avlv.mount | default(false) }}"`, an unmounted xfs LV with a nested `mntp` never gets its directory tree created, and converge dies with:

```
fatal: [idm.osgiliath.test]: FAILED! => {"cmd": ["xfs_growfs", "/var/nfs/volume"], ...
"stderr": "xfs_growfs: path resolution failed for /var/nfs/volume: No such file or directory"}
```

## What Changes

- In `tasks/lv.yml`, ensure the full mount point directory tree (`avlv.mntp`) exists — including nested parent directories — before including `mrlesmithjr.manage_lvm` for that LV.
- Default `mount` to `true` (instead of `false`) when an LV defines both a real filesystem and an `mntp`, so the dependency mounts the volume before its unguarded `xfs_growfs` task runs. An explicit `mount: false` in the LV definition is still honored.
- Add an LV with a nested, not-yet-existing mount point (e.g. `/var/nfs/volume`) to the molecule converge scenarios (`default`, `parallels`, `kvm`).
- Add testinfra tests asserting the nested mount point directory exists, the filesystem is mounted there, and it is writable.

## Capabilities

### New Capabilities

- `volume-mountpoints`: Mount point provisioning behavior for LVM logical volumes — creation of nested mount point directory trees before filesystem/mount hand-off to `mrlesmithjr.manage_lvm`, default mounting of LVs that define both a real filesystem and an `mntp`, and molecule scenario coverage for nested (not-yet-existing) mount points.

### Modified Capabilities

(none — this role has no existing specs under `openspec/specs/`)

## Impact

- **Code**: `tasks/lv.yml` (new directory pre-creation task; `mount` defaulting logic in the vars passed to `mrlesmithjr.manage_lvm`).
- **Behavior change**: LVs that define a real filesystem + `mntp` but no explicit `mount` will now be auto-mounted and get an fstab entry. All current molecule converge files already set `mount: true` explicitly, so scenario behavior is unchanged; sibling roles consuming this role (`tcharl.nfs_server`, `tcharl.ansible_containerization`, `tcharl.ansible_virtualization`, etc.) should be spot-checked for LVs relying on the old implicit no-mount default (they will now be mounted — which matches the intent of specifying a mount point).
- **Tests**: `molecule/default/tests/test_default.py` (shared by all scenarios via symlink) and the three `converge.yml` files.
- **Out of scope / unchanged**: the vendored `mrlesmithjr.manage_lvm` role is not modified; no changes to VG/pool/autoextend flows.
