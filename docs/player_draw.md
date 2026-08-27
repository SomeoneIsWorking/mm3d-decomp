# MM3D Player draw and base mesh visibility

Ground truth: retail Majora's Mask 3D `CTR-P-AJRE` `.code`, loaded at
`0x00100000` as ARM little-endian. The CMB identities and mesh inventories come
from the same retail RomFS through the repository's `CtrRom`, GAR, and corrected
CMB v10 parser.

## Player callback identities

The function at `0x001f47ec` installs four consecutive Player actor callbacks at
`0x006919ac`:

| callback | VA |
|---|---:|
| init | `0x001f5e88` |
| destroy | `0x001f71ec` |
| update | `0x001f9e80` |
| draw | `0x001f9038` |

This directly identifies `FUN_001f9038` as `Player_Draw`; it does not depend on
an inferred function shape. The function is 3480 bytes and its main Player body
route calls `FUN_00201074`, which first calls the mesh visibility reset below.

## Base mesh reset

`FUN_0020cfa4(Player*)` is the first mesh-selection stage. It enumerates every
mesh group in the live form model, disables groups not in a form-specific base
set, and enables the base groups. Visibility is routed through
`FUN_00219c20(Player*, meshId, visible)`: nonzero branches to the model virtual at
`0x0021ac14`; zero branches to the virtual at `0x0021ac24`.

The function copies a five-by-five `s32` table from `0x00626b5c`. Its rows are:

```text
{ 10,  7,  6,  5, 28 }
{ 12,  6,  7,  9, 29 }
{  9, 10, -1, 13, 33 }
{ 12, -1, -1, 10, 30 }
{ -1, -1, -1, 11, 32 }
```

Columns follow the runtime Player form enum: Fierce Deity, Goron, Zora, Deku,
Human. Duplicate and `-1` slots collapse to these base masks:

| form | base-visible mesh IDs |
|---|---|
| Fierce Deity | `9, 10, 12` |
| Goron | `6, 7, 10` |
| Zora | `6, 7` |
| Deku | `5, 9, 10, 11, 13` |
| Human | `28, 29, 30, 32, 33` |

The retail assets corroborate the table structurally. Human mesh IDs 28/29 are
the body groups and 30/32/33 are face/head groups; the excluded Human range
contains mutually exclusive hands, bows, hookshot, three shields, four swords,
and sheaths. Drawing the whole CMB therefore renders baked variants
simultaneously rather than a valid Player state.

## Retail body inventory

Exact-member parsing gives:

| form | CMB version | bones | meshes | mesh IDs |
|---|---:|---:|---:|---:|
| Fierce Deity | 10 | 24 | 27 | 13 (`0..12`) |
| Goron | 10 | 24 | 14 | 12 (`0..11`) |
| Zora | 10 | 28 | 30 | 17 (`0..16`) |
| Deku | 10 | 24 | 22 | 16 (`0..15`) |
| Human | 10 | 26 | 93 | 34 (`0..33`) |

Reproduce with `tools/mm_player_cmb_dump.py ARCHIVE_PATH CMB_MEMBER_PATH` in
the parent zelda3d repository. The tool requires `ZELDA3D_MM3D_ROM` and never
writes extracted asset bytes.

## Remaining draw-policy frontier

The base reset is only the first retail stage. `FUN_0020cfa4` continues with
form/state additions, and `FUN_00211aa4` selects hand, weapon, sheath, shield,
instrument, mask, and form-specific variants. Those selectors are not yet
ported: their static tables and 3DS Player fields must be aligned to the N64
`Player` fields before enabling any equipment group. Applying another game's
mesh map, defaulting to all groups, or guessing from texture names is not valid.

## Port integration evidence

The first native-port submission trace reported the renderer default
`0xffffffffffffffff` for every form. The recovered policy was correct, but the
MM draw seam omitted the emit-order snapshot that carries material overrides to
deferred draws. After adding that snapshot centrally, live form submissions
were Human `0x370000000`, Deku `0x2e20`, Goron `0x4c0`, Zora `0xc0`, and Fierce
Deity `0x1600`, exactly matching the recovered table above.
