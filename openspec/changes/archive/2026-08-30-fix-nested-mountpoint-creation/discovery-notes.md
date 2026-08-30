# Discovery notes: fix-nested-mountpoint-creation

## Task 3.4 — Sibling-role spot-check (D2 auto-mount impact)

All `lvm_groups` consumers of this role found via grep (`mntp:` across `ansible/roles/`, excluding this role). Assessment per design risk note: LVs with a real filesystem + `mntp` but no explicit `mount` key will now auto-mount.

| Consumer (scenario files) | LV | filesystem | mntp | Explicit `mount`? | D2 impact |
|---|---|---|---|---|---|
| tcharl.orchestration_csi (default/parallels/kvm prepare.yml) | nfs_exposed | xfs | /var/nfs | `true` | None — explicit key wins, identical to before |
| tcharl.ansible_containerization (all scenarios converge.yml) | thinpool | xfs | /var/lib/docker | `true` | None; sibling thinpoolmeta has no mntp → pre-creation skipped, mount computes false (unchanged) |
| tcharl.nfs_client (all scenarios prepare.yml) | nfs_exposed | xfs | /var/nfs | `true` | None |
| tcharl.ansible_container_registry (all scenarios converge.yml) | thinpool | xfs | /var/lib/docker | `true` | None; thinpoolmeta unchanged as above |
| tcharl.nfs_server (all scenarios converge.yml) | nfs_exposed | xfs | /var/nfs | `true` | None |
| **tcharl.ansible_orchestration** (default, kvm, parallels prepare.yml) | nfs_exposed | xfs | /var/nfs/volume | **absent** | **Behavior change: LV now auto-mounted + fstab entry.** Previously left unmounted locally while `expose_nfs` exported the path — i.e. NFS served an empty rootfs directory and the 4G XFS LV was unused. `tcharl.nfs_server` has no mount task of its own (only ensures the dir in `nfs-entry.yml`), so this is a fix, not a regression. The `csi_mount: true` key set alongside is referenced nowhere in tcharl.nfs_server tasks (dead key). |
| tcharl.ansible_orchestration default_noreset_kube prepare.yml | nfs_exposed, nfs_exposed2 | xfs | /var/nfs/csi, /var/nfs/volume | `true` on both | None |

**Conclusion:** no consumer genuinely needs `mount: false`; none flagged. The single behavior change (ansible_orchestration's `nfs_exposed`) aligns with the role's intent and is expected to be beneficial — recommend a follow-up review of that scenario's converge output after this change lands, but no code action required now.

## Task 3.2 — Idempotence observation (out of scope)

Second converge reports one spurious `changed` from `community.general.lvol` on the pre-existing `thinpoolmeta` LV (`size: 10%VG`) — a %VG rounding/tolerance quirk in the community role, present before this change; all subsequent lvol passes within the same run report `ok`. The directory pre-creation task itself is fully idempotent (`changed=false`, mode 0755 preserved).
