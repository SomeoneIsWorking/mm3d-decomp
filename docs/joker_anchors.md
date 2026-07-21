# MM3D (codename "joker") — static RE anchors and engine shape

Ground truth from the shipped binary. Derived with Ghidra headless; **no black-box probing**.

## Environment

```
# extract (repo-relative; needs a decrypted MM3D .3ds in ZELDA3D_MM3D_ROM)
python3 mm3d-decomp/tools/extract_code.py "$ZELDA3D_MM3D_ROM" scratch/re/mm3d.code
#   -> .text load addr 0x00100000, decompressed 0x5b1000 bytes

# import once (auto-analysis ~minutes)
analyzeHeadless build/ghidra mm3d -import scratch/re/mm3d.code \
  -processor ARM:LE:32:v6 -loader BinaryLoader -loader-baseAddr 0x00100000

# then reuse the oot3d script library
analyzeHeadless build/ghidra mm3d -process mm3d.code -noanalysis \
  -scriptPath oot3d-decomp/tools/ghidra_scripts -postScript <Script>.py
```

GOTCHA: `FindScalarOperand.py` prefixes hits with `SCALARHIT`. Grepping for a bare address returns
nothing and looks like a false negative — sanity-check any "0 hits" result against a constant that must
exist (`0x3F800000` → 928 hits).

## DEAD END — do not retry: CMB chunk magics are not referenced

`code.bin` contains **zero** references to `cmb `/`skl `/`sepd`/`vatr`/`prm ` — as immediates, as movw
halves, or as literal bytes — and the romfs has **no CRO/CRS modules**. The shipped engine does not
validate magics; it reads header pointers at fixed offsets. Anchor on something else.

## THE GOOD ANCHOR — assert strings carry ORIGINAL SOURCE PATHS

Asserts embed real filenames and line numbers, e.g.
`C:\Jenkins\workspace\joker\prog\game\sources\original\z_player.cpp(28254)`.
**283 such strings across 105 distinct .cpp files.** Xref a string VA (`FindDataWriters.py`) to get the
function that uses it — which effectively NAMES that function.

Modules present (105 total; the structurally interesting ones):

    z_room.cpp   z_scene_proc.cpp   SceneGraph.cpp   ObjectBankArchive.cpp   Package.cpp
    Project.cpp  graph.cpp          LayoutDrawManager.cpp   imageHelper.cpp   WaterSurface.cpp
    z_play.cpp   z_actor.cpp        z_player.cpp     z_kankyo.cpp      z_lights.cpp

Resolved anchors:

| assert string VA | source | function |
|---|---|---|
| `0x006465C0` | `z_room.cpp(453)` | `FUN_004dd3f0` |
| `0x00646608` | `z_scene_proc.cpp(1848)` | `FUN_004938d8` |
| `0x006414FC` | `SceneGraph.cpp(41)` | `FUN_0011f074`, `FUN_001111b8` |
| `0x00640E14` | `ObjectBankArchive.cpp(200)` | `FUN_001d4844` |
| `0x006412D4` | `ObjectBankArchive.cpp(787)` | `FUN_001f5c00` |
| `0x00641450` | `ObjectBankArchive.cpp(979)` | `FUN_001fe9e8` |

## FUN_001d4844 — `ObjectBankArchive` init = the GAR2 archive parser

Confirms our ported GAR reader against the real engine. With `param_3` = archive base:

```
*(param_1+0x0C) = *(param_3+0x0C) + base    // typesOff
*(param_1+0x10) = *(param_3+0x10) + base    // filesOff
*(param_1+0x14) = *(param_3+0x14) + base    // dataHdrOff
if (*(s16*)(param_3+8) != 0) ...            // nTypes @ 0x08
```

It then initialises **16** slots at `+0x1C..+0x58` to `0xFFFFFFFF` and strcmp's (`FUN_00302e3c`) each
archive type name against a 16-entry table at `DAT_001d54ec`, caching the matched type index per slot —
i.e. a fixed set of 16 known member types (cmb/csab/cmab/ctxb/...), looked up once at load.

This matches `Shipwright/cmb3d/asset/gar.{h,cpp}` — the header layout our port uses is CORRECT.

## Engine shape — C++ scene graph, not the N64 C path

`FUN_004dd3f0` (z_room.cpp) allocates a 0x4c-byte object, dispatches through its **vtable**
(`(**(code**)*obj)(obj, arg)`), stores it into a 0x44-stride table at `play+0xC260` indexed by a counter
at `play+0xC267`, then attaches it via `FUN_001fd904`. Together with `SceneGraph.cpp`, this says MM3D
renders through a **C++ scene graph of polymorphic nodes**, not a direct display-list/CMB blit.

Consequence for the port: reproducing MM3D room rendering by parsing a room CMB as a self-contained
mesh is modelling a different architecture. Combined with the split asset layout (per-scene `.ctxb`
textures, per-scene `.gar` holding only a CMAB), the room CMB is one input to a scene-graph node, not a
standalone drawable.

## Open question this was opened for

Why MM3D room CMB vertex indices overrun every VATR buffer (see
`debug_journal/2026-07-21-mm-scene-room-pipeline.md`). NOT yet answered. Next step: walk from
`FUN_004dd3f0` / `FUN_004938d8` to the node type that consumes room geometry, and read how it computes
the vertex fetch.
