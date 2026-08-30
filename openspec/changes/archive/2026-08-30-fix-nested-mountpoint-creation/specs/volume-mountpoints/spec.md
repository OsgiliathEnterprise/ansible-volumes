## Purpose

Defines how the role provisions mount points for LVM logical volumes: creation of nested mount point directory trees before filesystem/mount hand-off, and the default mounting behavior for LVs that define both a real filesystem and a mount point.

## ADDED Requirements

### Requirement: Nested mount point directories are created before filesystem provisioning
When an LV defines a real filesystem (any value other than `None` or `swap`) and an `mntp`, the role SHALL ensure the complete directory tree of `mntp` — including all missing parent directories — exists on the target host before the LV is handed to `mrlesmithjr.manage_lvm` for filesystem creation and mounting. Directory creation MUST be idempotent: re-running against an already-existing mount point MUST NOT fail or report a change.

#### Scenario: Nested mount point whose parents do not exist yet
- **WHEN** converge runs for an xfs LV with `mntp: /var/nfs/volume` on a host where `/var` exists but `/nfs` does not
- **THEN** the directory tree `/var/nfs/volume` is created before filesystem creation and mounting proceed, AND converge completes without `xfs_growfs: path resolution failed for /var/nfs/volume: No such file or directory`

#### Scenario: Mount point already exists from a previous run
- **WHEN** converge re-runs on a host where the LV's mount point directory tree already exists
- **THEN** directory creation reports no change and the run does not fail

### Requirement: LVs with a filesystem and mount point are mounted by default
When an LV defines both a real filesystem (any value other than `None` or `swap`) and an `mntp`, the role SHALL pass `mount=true` to `mrlesmithjr.manage_lvm` unless the LV definition explicitly sets `mount`. An explicit `mount: false` in the LV definition SHALL be honored as-is. LVs without a real filesystem (filesystem `None` or `swap`) MUST NOT be auto-mounted by this defaulting, even if an `mntp` is present.

#### Scenario: Mount point and filesystem defined without explicit mount flag
- **WHEN** an LV defines `filesystem: xfs` and an `mntp` but no `mount` key
- **THEN** the volume is mounted at `mntp` after creation, with a corresponding fstab entry present on the host

#### Scenario: Explicit opt-out of mounting
- **WHEN** an LV defines `filesystem: xfs`, an `mntp`, and explicit `mount: false`
- **THEN** no mount or fstab entry is created for that volume by this role

### Requirement: Molecule scenarios exercise a nested, not-yet-existing mount point
The molecule converge scenarios (`default`, `parallels`, `kvm`) SHALL include an xfs LV whose `mntp` is a nested path (at least two levels below an existing directory) that does not exist on the base image, and the shared testinfra suite SHALL verify the resulting state.

#### Scenario: Nested LV converges in all scenarios
- **WHEN** any molecule scenario's converge runs against a fresh host
- **THEN** the nested-mount-point LV is created, formatted as xfs, mounted at its `mntp`, and the run completes successfully

#### Scenario: Verification asserts nested mount point state
- **WHEN** the testinfra verification suite runs after converge
- **THEN** tests assert that the nested mount point path exists as a directory, is the mount point of an xfs filesystem, and accepts file writes
