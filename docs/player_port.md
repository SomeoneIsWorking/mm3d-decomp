# Porting MM3D Link's player code — plan & journal

Sibling of `oot3d-decomp/docs/player_port.md`. Goal: recover MM3D's `Player_Update` /
`Player_Draw` (and the surrounding action-func machinery) as ground truth so soh3d can port MM
Link into the shared OoT/MM Link behavior module — *not* graft the N64 MM (2S2H) logic onto 3DS
assets.

## Status (2026-07-02, later3): **`Player_Update` = VA `0x00204640`**, **`Player_Init` = VA `0x001f5e88`**. Handler-pointer table read directly from the Player_Init body. See "Player_Update pinned via handler-install table" section.

## Status (2026-07-02, later): anchor `0x001f5e88` = **`Player_Init`** — pinned by structural alignment against MM N64 `z_player.c` (`Player_Init` @ line 11257). See "Role pinned" section below.

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

## Role pinned (2026-07-02): `FUN_001f5e88` = `Player_Init`

Structural diff of `build/decomp/fn_0x001f5e88.c` against MM N64
`Shipwright/mm/src/overlays/actors/ovl_player_actor/z_player.c` `Player_Init` (line 11257)
yields a **multi-point, unambiguous match**. Every distinctive shape lines up. Evidence:

1. **Play-struct handler install block (smoking gun).** The very first thing MM's `Player_Init`
   does is install 13 function pointers into the `PlayState` at consecutive offsets
   (`play->playerInit`, `play->playerUpdate`, `play->unk_18770`, `play->startPlayerFishing`,
   `play->grabPlayer`, `play->tryPlayerCsAction`, `play->func_18780`, `play->damagePlayer`,
   `play->talkWithPlayer`, `play->unk_1878C`, `play->unk_18790`, `play->unk_18794`,
   `play->setPlayerTalkAnim`). The decomp opens with **exactly** this — 13 consecutive
   `*(undefined4 *)(param_2 + 0xc42c..0xc45c) = DAT_...` writes, each `DAT_` being a code
   pointer literal. No other Player TU function does this; only `Player_Init` installs the
   play-level handlers.
2. **`gActorOverlayTable[ACTOR_PLAYER].profile->objectId = GAMEPLAY_KEEP;`.** Decomp:
   `*(undefined2 *)(*(int *)(DAT_001f62c0 + 0x14) + 8) = 1;` — indirect through
   `gActorOverlayTable` (`DAT_001f62c0`), `+0x14` = `.profile`, `+8` = `objectId`, value `1`
   = `GAMEPLAY_KEEP`. Matches exactly.
3. **`this->actor.room = -1; this->csId = CS_ID_NONE;`.** Decomp:
   `*(undefined *)((int)param_1 + 3) = 0xff; *(undefined *)(param_1 + 0x8ee7) = 0xff;` —
   both are `-1` writes to Player struct.
4. **Effect_Add trio (3 blures + 1 tire mark).** MM `Player_Init` calls:
   ```c
   Effect_Add(play, &this->meleeWeaponEffectIndex[0], EFFECT_BLURE2, 0, 0, &D_8085D30C);
   Effect_Add(play, &this->meleeWeaponEffectIndex[1], EFFECT_BLURE2, 0, 0, &D_8085D30C);
   Effect_Add(play, &this->meleeWeaponEffectIndex[2], EFFECT_TIRE_MARK, 0, 0, &D_8085D330);
   ```
   Decomp has three back-to-back calls with signature
   `FUN_00238138(param_2, param_1+0x704/0x706/0x708, 2/2/4, 0, 0, initPtr)` — the first two
   `kind=2` = `EFFECT_BLURE2`, last `kind=4` = `EFFECT_TIRE_MARK`, and effectIndex slots at
   `+0x704/+0x706/+0x708` are three consecutive `s16` — matches `meleeWeaponEffectIndex[3]`.
5. **`respawnFlag` dispatch.** Late in `Player_Init`:
   ```c
   respawnFlag = gSaveContext.respawnFlag;
   if (respawnFlag != 0) {
     if (respawnFlag == -3) { ... }
     else { if ((respawnFlag == 1) || (respawnFlag == -1)) { ... }
            if (respawnFlag != -7) {
              if ((respawnFlag == -8) || (respawnFlag == -5) || (respawnFlag == -4)) respawnFlag = 1;
              if ((respawnFlag < 0) && (respawnFlag != -1) && (respawnFlag != -6)) ...
   ```
   Decomp reproduces exactly the same case ladder over the same magic constants
   (`iVar16 == -3`, `== 1`, `== -1`, `== -7`, `== -8`, `== -5`, `== -4`, `== -6`),
   with `iVar16 = *(int *)(iVar12 + 0x13624)` = `gSaveContext.respawnFlag`.
6. **Init-time SkelAnime slot table.** The `do { ... FUN_00203c40(param_1, param_2, 1,
   aiStack_120[iVar8*2+1], 1); ... } while (iVar8 < 0x1c);` loop iterates 28 entries of a
   local table copied from `DAT_001f6988` — matches `Player_InitCommon` / init-chain-shape
   preload of the 28-ish PlayerAnim entries (`gPlayerAnim_link_*` table). Called BEFORE the
   respawn dispatch = init-time, not per-frame.
7. **Size and control-flow shape.** 4672 B, dozens of struct field default-value writes at
   the top, single-shot ("no while(1) action-func dispatch"), no per-frame timer decrement
   block — categorically not `Player_Update`/`Player_UpdateCommon`. And no `Matrix_Push` /
   `POLY_OPA_DISP` / `SkelAnime_Draw` calls → not `Player_Draw`.

**Conclusion:** `FUN_001f5e88` at VA `0x001f5e88` is MM3D's `Player_Init(Actor* thisx,
PlayState* play)`. Signature Ghidra inferred (`short *param_1, int param_2`) matches
(`Actor*` first, `PlayState*` second — same as N64).

### Fan-out enabled by this anchor

Callees of `Player_Init` are now candidates for identification:

- `FUN_00203c40(this, play, 1, animId, 1)` — called 28+1 times, all with same
  `(this, play, 1, ..., 1)` shape → very likely `Player_SpawnMagicSparkles` or the anim
  DMA-request wrapper (`Player_InitAnim` / `func_80834140`-shape). Small utility.
- `FUN_00238138(play, s16*, kind, 0, 0, initPtr)` — three-args-then-init shape called with
  `EFFECT_BLURE2` / `EFFECT_TIRE_MARK` literals → this IS `Effect_Add`.
- `FUN_001d30f8(play, this, someTable, 0)` — table-driven per-instance init → strong
  candidate for `Actor_ProcessInitChain`.
- `FUN_00207b60(play)` — no-args-but-play, called from the fresh-init branch → candidate
  for `Player_InitCommon` (called by `Player_Init` on fresh spawn) or `Play_AssignPlayerCsIdsFromScene`.
- `FUN_001f57dc(play + 0x9438, formIdx)` — called with a per-form index from a small table
  → candidate for one of the object-slot lookup helpers (`Object_GetSlot`-shape).
- `FUN_0022a6d8(this)` — tail-called after a negative return → `Actor_Kill(&this->actor)`
  candidate (matches `Player_Init` line 11290 `if (objectSlot <= OBJECT_SLOT_NONE) { Actor_Kill(...); return; }`).

Next session should verify at least `FUN_0022a6d8 = Actor_Kill` (small, distinctive: flips
one flag on the actor and appends to a free list) and `FUN_00238138 = Effect_Add` — both
are low-risk, high-fanout wins that unlock hundreds of downstream calls across the binary.

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

## Player_Update pinned via handler-install table (2026-07-02, later3)

`FUN_001f5e88` (Player_Init) opens with 13 consecutive `*(u32*)(param_2 + N) = DAT_00X`
writes at N = 0xc42c..0xc45c (MM z_player.c installs `play->playerInit`, `playerUpdate`,
`unk_18770`, `startPlayerFishing`, `grabPlayer`, `tryPlayerCsAction`, `func_18780`,
`damagePlayer`, `talkWithPlayer`, `unk_1878C`, `unk_18790`, `unk_18794`, `setPlayerTalkAnim`).
Each `DAT_` in that block is a 32-bit ARM function pointer literal — dereferencing the
binary at those addresses gives the handler VAs directly.

Extracted (thumb bit stripped; all 0 = ARM mode):

| play offset | field                | DAT literal | Function VA    |
|-------------|----------------------|-------------|----------------|
| +0xc42c     | playerInit           | DAT_001f628c | **0x0020447c** |
| +0xc430     | **playerUpdate**     | DAT_001f6290 | **0x00204640** |
| +0xc434     | unk_18770            | DAT_001f6294 | 0x002084fc     |
| +0xc438     | startPlayerFishing   | DAT_001f6298 | 0x0020364c     |
| +0xc43c     | grabPlayer           | DAT_001f629c | 0x00209494     |
| +0xc440     | tryPlayerCsAction    | DAT_001f62a0 | 0x0022b728     |
| +0xc448     | damagePlayer         | DAT_001f62a8 | 0x0020f954     |
| +0xc44c     | talkWithPlayer       | DAT_001f62ac | 0x002209a8     |

### Reconciliation with prior ruled-outs

`FUN_00204640` (12508 B) was previously RULED OUT as `Player_UpdateCommon` because
`ReferenceManager` returned zero refs. That result was a true positive for
"reached only via function pointer" (matching a `play->playerUpdate` slot install)
and a false negative for identity. It is `Player_Update`. Re-verifying its
per-frame timer-decrement / stateFlags-test / actionFunc-dispatch shape is the next
sanity-check but the derivation via handler pointer is direct and unambiguous.

**Note on the two "Init" callbacks.** Actor overlay `.profile.init` (`Player_Init`
proper, the entry point Actor_Init_Player calls) is `FUN_001f5e88`. The
`play->playerInit` callback slot (+0xc42c) is a DIFFERENT function (`FUN_0020447c`)
— MM boots this once and calls it from elsewhere in scene setup (probably
`Player_InitCommon`-shape; N64 `PlayState.playerInit` in z64play.h is a callback,
not `Player_Init`). Do not conflate.

### Extraction one-liner (reproducible)

```bash
python3 -c "
import struct
with open('$SCRATCH/mm3d-decomp/mm3d.code','rb') as f: data=f.read()
def rd(va): off=va-0x100000; return struct.unpack('<I', data[off:off+4])[0]
for name, va in [('playerInit',0x1f628c),('playerUpdate',0x1f6290)]:
    print(f'{name:22s} DAT_{va:08x} -> VA 0x{rd(va) & ~1:08x}')
"
```

### Next-session targets (documented, not verified this run)

- **`Player_Draw` = ?** — Not in the `play->` handler table (Player_Draw is dispatched
  via the actor overlay profile like Player_Init). Recovery: read the `gActorOverlayTable`
  entry for `ACTOR_PLAYER`. Player_Init reads it as `DAT_001f62c0 + 0x14` (profile) —
  the profile struct's `draw` field lives at profile+0x1c on N64 (see soh z64actor.h
  `ActorProfile`). Read that pointer and Player_Draw's VA falls out the same way as
  Player_Update did. Do NOT scan for symbol strings — none survive.
- **Verify `FUN_00204640` shape** — decompile at high effort, confirm the top-of-body
  has the standard Player-Update prologue (state flag test, timer decrement, camera
  update hook), and confirm the actionFunc dispatch appears (probably calls
  `Player_UpdateCommon` which does the real dispatch).
- **Player_Draw's callees will fan out** the `SkelAnime_DrawFlex` + `Matrix_Push` +
  MM-specific `Player_DrawGameplay` variant. Those are the crucial ones for the
  soh3d MM Link render port.
