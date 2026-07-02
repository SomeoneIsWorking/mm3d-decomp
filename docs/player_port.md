# Porting MM3D Link's player code — plan & journal

Sibling of `oot3d-decomp/docs/player_port.md`. Goal: recover MM3D's `Player_Update` /
`Player_Draw` (and the surrounding action-func machinery) as ground truth so soh3d can port MM
Link into the shared OoT/MM Link behavior module — *not* graft the N64 MM (2S2H) logic onto 3DS
assets.

## Status (2026-07-02): BLOCKED at anchor identification — one z_player TU function verified, role TBD

MM3D's `.code` is stripped (no symbols, no RTTI names, no OTF debug tables) and — crucially —
**contains only ONE assert string from `z_player.cpp` in the entire binary**
(`z_player.cpp(28254)` @ file off `0x54656c` / VA `0x64656c`). Unlike OoT3D, we cannot cluster
z_player.cpp functions by grouping `__assert` string references (there is exactly one to group).
That anchor is documented below; further identification requires call-graph / structural work.

## Tooling this run used

- Ghidra 11.0.3 headless project at `scratch/ghidra/mm3d.rep` (pre-existing,
  imported from `scratch/mm3d.code` at base `0x00100000`, ARM LE 32).
- `tools/FindPlayerUpdate.py` (this repo, new): decompile arbitrary VAs; force-create Ghidra
  functions Ghidra missed (ARM mode / TMode=0), write `build/decomp/fn_0x<vaddr>.c`.
- `tools/DumpDecomp.py` (pre-existing): simpler single-list decompile driver.
- Reference: `oot3d-decomp/docs/player_port.md`, `oot3d-decomp/tools/ghidra_scripts/DecompDump.py`
  (the OoT3D-side twin — same conventions).
- N64 Rosetta stone:
  `<engine>/soh/src/overlays/actors/ovl_player_actor/z_player.c` (fully decompiled).

## Verified anchor #1 — the only z_player.cpp assert string ref

- Debug string: `z_player.cpp(28254)`
  - file offset `0x54656c`, virtual address `0x0064656c`.
- ARM `LDR R2, [PC, #1120]` at **VA `0x001f6524`** loads the pointer to that string. (Found by
  scanning `.text` for `LDR (literal)` encodings pointing at `0x0064656c`.)
- That instruction is INSIDE a function Ghidra initially missed. Its start (identified by
  scanning backward for the standard `STMFD sp!, {…, lr}` prologue `E92D 4FF0`) is
  **VA `0x001f5e88`, size ~4672 B**. Force-created + decompiled → `build/decomp/fn_0x001f5e88.c`.
  - Signature (Ghidra-inferred): `void FUN_001f5e88(short *param_1, int param_2)`.
  - Confirmed a z_player.cpp function (only place in the binary that touches the 28254 assert).
  - **Role NOT yet pinned to Update/Draw.** Its size (4672 B, single fn) does not match either an
    OoT3D-style `Player_Update` (small, ~600 B) or a compact `Player_Draw`. It could be
    `Player_UpdateCommon`, `Player_Init`, or a fat action func / draw-with-effects. Structural /
    call-graph alignment against N64 `z_player.c` is required to name it.

## What we tried and ruled out

- **ActorInit-based ID.** Search for the classic `ActorInit { s16 id=0, u8 category=2, u8 pad,
  u32 flags, s16 objectId, u16 pad, u32 instanceSize, init/destroy/update/draw }` pattern with
  Player-sized `instanceSize` returned **zero hits** at any relaxed category. MM3D's Actor init
  descriptor is NOT laid out in that OoT-style struct — likely a C++ class with a vtable or a
  differently packed struct. Follow-up: RE one confirmed actor's init pattern (e.g. via a
  non-player asset that Ghidra HAS resolved) and generalize.
- **Giant-function callers.** `FUN_00204640` (12508 B) and `FUN_0020132c` (7812 B) were the two
  largest fns in the plausible `.text` region and initially looked like `Player_UpdateCommon`
  candidates. Ghidra's `ReferenceManager` returned **zero references** to either — meaning they
  are either indirectly-dispatched (via function pointer stored elsewhere) or not player-related.
  Their decompiled bodies also don't show the characteristic Player_UpdateCommon shape
  (`this->actionFunc(this,play)` dispatch, timer-decrement block, `stateFlags` bit tests).
- **Actor-name / debug-name strings.** `strings` on the binary yields no `Player`, `Link`,
  `プレイヤ`, actor-category, or overlay-filename markers that would seed the search. Total
  distinct source files referenced by asserts = 104 (see
  `scratchpad/mm3d_sources.txt`); only `z_player.cpp` matches player, and it has just one entry.

## What remains for the next session

Two viable paths forward — either unblocks the port:

1. **Structural alignment on `fn_0x001f5e88`.** Diff its call-graph and control-flow against
   N64 `z_player.c` functions in the `Player_Draw` / `Player_UpdateCommon` / `Player_Init`
   band (all large, all late-in-file). Once its role is named, the callers/callees fan out
   `Player_Update` and `Player_Draw` from there.
2. **Recover MM3D's actor init struct layout first.** Pick a small, obvious actor (e.g.
   `En_Firefly`, whose OoT3D binary lays out the classic ActorInit) and locate its 3DS
   counterpart by other means (object-file address, static memory pattern). Once the MM3D
   ActorInit shape is known, the id=0 sweep can be re-run with the right unpacker and Player's
   entry falls out directly — its `update`/`draw` fields ARE the target functions.

Not yet documented (MM-specific quirks to look for once Player_Update is anchored):

- Form/mask dispatch (child / deku / goron / zora / fierce-deity), which likely gates action
  funcs and skeleton selection — a real divergence from OoT3D that WILL surface in Update.
- Two-day cycle / owl-save save-state hooks in Player_Update.
- MM's playtime / clockdown side effects in the update chain.

## Artifacts committed by this session

- `docs/player_port.md` (this file).
- `tools/FindPlayerUpdate.py` — reusable targeted-VA decompiler with force-create for missed
  functions (used to force-create `0x001f5e88`).

The decompiled C for `fn_0x001f5e88.c` lives in `build/decomp/`
(gitignored per repo policy — do NOT check large auto-generated dumps into the repo). Re-produce
with:

```bash
cd <repo>
MM3D_FORCE=1 MM3D_TARGETS=0x1f5e88 \
  /opt/ghidra_11.0.3_PUBLIC/support/analyzeHeadless \
    scratch/ghidra mm3d \
    -process mm3d.code -noanalysis \
    -scriptPath tools -postScript FindPlayerUpdate.py
```
