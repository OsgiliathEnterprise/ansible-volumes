# Design: fix nested mount point creation for LVM filesystems

## Context

See proposal.md for motivation. Current flow relevant to this change:

- `tasks/main.yml` → `prereq.yml` (installs `xfsprogs`, then statically imports `mrlesmithjr.manage_lvm` with the top-level `lvm_groups`; since scenario LVs live under `lvmetanames` rather than `lvnames`, this pass only creates VGs) → "Loop over vgs" (`vg.yml`) → per-LV `include_tasks: lv.yml`.
- `tasks/lv.yml` includes `mrlesmithjr.manage_lvm` once per LV with a single-LV `lvm_groups` built from the `avlv` loop variable, passing `mntp: "{{ avlv.mntp | default(omit) }}"` and `mount: "{{ avlv.mount | default(false) }}"`.
- The vendored dependency's `tasks/create_fs.yml`: the mount task (line 67) is gated on `lv.mount|bool`, but the `xfs_growfs {{ lv.mntp }}` task (line 85) runs whenever a new xfs LV was created (`lvchanged.changed`) with **no** mount guard. `ansible.posix.mount` itself creates missing nested directories (mkdir -p semantics), so with `mount=true` nested paths already work; the failure only hits unmounted xfs LVs that still carry an `mntp`.
- Constraint (user decision): the vendored `mrlesmithjr.manage_lvm` role is **not** modified.

## Goals / Non-Goals

**Goals:**
- Converge succeeds for LVs whose `mntp` parent directories do not exist yet, in all molecule scenarios (`default`, `parallels`, `kvm`).
- A newly created xfs LV that defines an `mntp` always has a valid mounted target when the dependency's unguarded `xfs_growfs` task runs.
- Idempotent: re-runs against existing directory trees report no change and do not fail.

**Non-Goals:**
- No changes to `mrlesmithjr.manage_lvm` (vendored upstream role stays pristine).
- No changes to VG creation, thinpool conversion (`pool.yml`), autoextend profiles, or the `prereq.yml` xfsprogs install logic.
- No new variables in `defaults/`; behavior is derived from existing per-LV keys only.

## Decisions

### D1: Pre-create the mount point directory tree in `tasks/lv.yml`, immediately before the `include_role`

Add one task to `lv.yml`:

```yaml
- name: Lv | ensure mountpoint directory exists {{ avlv.mntp }}
  ansible.builtin.file:
    path: "{{ avlv.mntp }}"
    state: directory
  become: true
  when:
    - avlv.mntp is defined
    - avlv.mntp != 'None'
```

- `file: state=directory` has mkdir -p semantics (creates all missing parents) and is idempotent.
- Gated on `mntp` being defined/non-`None` only — deliberately a superset of the spec's "real filesystem + mntp" condition, so it also protects `pool.yml`'s unmount task (`state: absent` against `avlv.mntp`) and any future consumer path that references the path without mounting.
- **Alternatives considered:**
  - Pre-create once in `prereq.yml` by looping over `lvm_groups` subelements — rejected: duplicates loop plumbing; `lv.yml` already has the per-LV `avlv` variable at exactly the hand-off point where the directory must exist.
  - Rely solely on `ansible.posix.mount`'s built-in mkdir -p — rejected: only runs when `mount=true`, which is precisely the case that fails today (see D2).

### D2: Default `mount` to true for LVs with a real filesystem + mntp, in `lv.yml` vars

Replace `mount: "{{ avlv.mount | default(false) }}"` with an expression where an explicit `avlv.mount` always wins and the implicit default is computed from the other keys:

```yaml
mount: >-
  {{ (avlv.mount if avlv.mount is defined else
      ((avlv.mntp is defined and avlv.mntp != 'None') and
       (avlv.filesystem | default('None') not in ('None', 'swap')))) }}
```

Semantics:
| `avlv.mount` | `mntp` | `filesystem` | passed to dependency |
|---|---|---|---|
| defined (true/false) | any | any | the explicit value, unchanged |
| undefined | defined + real fs | xfs/ext4/... | `True` (auto-mount) |
| undefined | missing or `None` | any | `False` (today's behavior) |
| undefined | defined | `None`/`swap` | `False` (no meaningful mount target) |

- The dependency consumes the value via `lv.mount|bool`, so rendered `"True"`/`"False"` strings are safe.
- **Alternatives considered:** a `set_fact` in `main.yml` or a new key in `defaults/` — rejected: per-LV scoping at the include site keeps the diff minimal and local to where the value is consumed; no global variable surface area added.

### D3: Scenario LV reproduces the reported topology — nested under an existing mount point

Add one LV to all three scenario `converge.yml` files, placed **after** `nfs_exposed` in `lvmetanames`:

```yaml
- lvname: nfs_nested
  size: 512M
  create: true
  filesystem: xfs
  mntp: /var/nfs/volume
  # no explicit mount key on purpose: exercises the new default-mount behavior (D2)
```

- Size must exceed `mkfs.xfs`'s minimum (~300MB): an initial 256M attempt failed with "Filesystem must be larger than 300MB", so 512M is used (matches `nfs_exposed`).

- `/var/nfs/volume` is nested inside `nfs_exposed`'s mount point (`/var/nfs`) — reproduces the user's exact failure topology and additionally proves directory creation works *inside an already-mounted xfs volume*.
- Ordering matters: `lv.yml` processes LVs in list order, so `nfs_nested` must come after `nfs_exposed`; a misordered definition fails loudly at mount time (no silent corruption).
- The new LV intentionally omits `mount:` to exercise D2's auto-mount path; the existing LVs keep their explicit `mount: true`.

### D4: Tests in the shared suite (`molecule/default/tests/test_default.py`, symlinked by all scenarios)

Follow the file's existing style (raw commands via `host.run` with `sudo`, plus `host.file` where already used):
- directory exists: `sudo test -d /var/nfs/volume`
- mounted as xfs at that path: `sudo mountpoint -q /var/nfs/volume` and/or `xfs_info /dev/non-persistent/nfs_nested | grep -c 'ftype=1'` (mirrors the existing `test_formating_is_xfs`)
- writable: write a file via `host.run("sudo touch ...")` and read it back

## Risks / Trade-offs

- [Behavior change: LVs with real fs + mntp but no explicit `mount` now auto-mount and get fstab entries] → All current molecule converge files set `mount: true` explicitly, so scenario behavior is unchanged. Mitigation: spot-check sibling roles' `lvm_groups` definitions (`tcharl.nfs_server`, `tcharl.ansible_containerization`, `tcharl.ansible_virtualization`, ...) for LVs relying on the old implicit no-mount default; auto-mounting matches the intent of specifying a mount point, and any consumer that truly wants no mount can now set explicit `mount: false`.
- [Ordering dependency between `nfs_exposed` and `nfs_nested`] → Enforced by list order in all three converge files (D3); failure mode is a loud mount error, not silent corruption.
- [Explicit `mount: false` on an xfs LV with mntp still hits the dependency's unguarded `xfs_growfs` on first creation] → Accepted limitation of not patching the vendored role; this is a contradictory configuration (requesting a mount point while refusing to mount). Documented here; out of scope.
- [`file: state=directory` fails if `mntp` exists as a regular file] → Correct behavior: loud failure on misconfiguration rather than silent overwrite.
- [fstab entries persist across re-runs on long-lived hosts] → `ansible.posix.mount` is idempotent; destroy/create molecule cycles discard the VM anyway.

## Migration Plan

No data migration. The change takes effect on the next converge of any host using the role: missing mount point trees are created and previously-unmounted fs+mntp LVs get mounted + fstab entries (idempotent thereafter). Rollback = revert the commit; any auto-created directories/fstab entries left behind are harmless (empty dirs, or removable fstab lines) — no state corruption.

## Open Questions

- None blocking: scenario LV name (`nfs_nested`) and identical updates to all three scenarios are recorded as assumptions in tasks.md. Size settled at 512M during implementation (mkfs.xfs minimum >300MB).
