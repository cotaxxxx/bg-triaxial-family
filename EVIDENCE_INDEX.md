# Three-axis research: source and evidence index

> This index records **copied source artifacts**, not mathematical certification.

## Provenance (read-only originals)

| Original repository | Ref | Full commit | Original prefix | Imported folder | Files |
|---|---|---|---|---|---:|
| `cotaxxxx/bg-spheroid-family` | `origin/codex/triaxial-first-atlas-20261120` | `5fbd120e992321ccdbbe26120cea0eab36b88c75` | `runs/2026-11-20/CODEX_TRIAXIAL_FIRST_ATLAS/` | `evidence/source-snapshots/codex-first-atlas/` | 4 |
| `cotaxxxx/bg-spheroid-family` | `origin/codex/triaxial-rectangle-20261120` | `b46205e6f97899c87154fc439d4f68a139ad89ce` | `runs/2026-11-20/CODEX_TRIAXIAL_RECTANGLE/` | `evidence/source-snapshots/codex-rectangle/` | 100 |
| `cotaxxxx/bg-spheroid-family` | `origin/codex/triaxial-rectangle-interval-20261120` | `43854bcbe4ccb0595505ba30c327ffee906897cd` | `runs/2026-11-20/CODEX_TRIAXIAL_RECTANGLE_INTERVAL/` | `evidence/source-snapshots/codex-rectangle-interval/` | 9 |
| `cotaxxxx/bg-spheroid-family` | `origin/claude/triaxial-map-audit-20261120` | `5535968b7eae55c101a7c0180b6f2161dcc8e209` | `runs/2026-11-20/CLAUDE_AUDIT_CODEX_TRIAXIAL_RECTANGLE/` | `evidence/source-snapshots/claude-audit-rectangle/` | 11 |
| `cotaxxxx/bg-spheroid-family` | `origin/claude/triaxial-map-audit-20261120` | `5535968b7eae55c101a7c0180b6f2161dcc8e209` | `runs/2026-11-20/CLAUDE_TRIAXIAL_FIRST_MAP/` | `evidence/source-snapshots/claude-first-map/` | 8 |
| `cotaxxxx/basepoint-geometry` | `43b71569` | `43b715692427a8680f4b380746cc0c87376a5ad1` | `diagnostics/triaxial_map_20261120/` | `evidence/source-snapshots/basepoint-v56-independent-map/` | 60 |

## Additional inputs
- `evidence/audits/V56/CHAT_AUDIT_D_TRI_CCR_MAP_V56.md`: local audit file, SHA-256 `dbdd118de6c2dbba2ba5255247b3e023a195c232ddd761241d013aa795527650` (DIAGNOSTIC_ONLY).
- `calibration/V60/input/V60_PC_BUNDLE.tar.gz`: original input archive, SHA-256 `75c023743e6bcbfb561c4b88b31560da81036261d4d729969128fd6f0a2693af`; `unpacked/` is an exact extracted input copy. Manifest entries checked by `sha256sum -c`.
- The V60 run is a **96-combination calibration** of layers I and II, not a certificate or adopted final result. No in-progress `out/` files were included.

## Distinguish completeness from storage
- Original documents for V55/V56 and the identified rectangle-interval studies are imported without alteration, with separate source paths above.
- The V60 input archive includes the Reader 0.5 source and V57 numeric reference scripts.
- **V57 A1 evidence, V58, V59 and V59-B source originals are now imported** into [`evidence/chat-originals/`](evidence/chat-originals/) from `cotaxxxx/bg-spheroid-family` commit `acc24d74f105ecaf7d320378dff819c2e4724050`. See [`PROVENANCE.md`](evidence/chat-originals/PROVENANCE.md). The 110 original files were byte-for-byte checked against the source commit on 2026-11-21. Five folders passed their own `SHA256SUMS.txt` checks; the four files in `GEOENCLOSURE_STANDARD` (which has no folder SHA manifest) were compared directly to the source commit. This confirms file identity, **not** mathematical correctness.
- **V60 result package and subsequent audit are not yet included here**; the current V60 materials are inputs and calibration plans only.
- A1 is the user-reported adoption level; no global independent certification is implied. Layers I–III remain open in the main rectangle.
- This repository is public. Before adding new code or reports, check for credentials and confidential information.

## File integrity
- `evidence/SHA256_COPIES.txt` lists the SHA-256 hashes of the actual copied files. Hash identity alone does not prove mathematical correctness.
