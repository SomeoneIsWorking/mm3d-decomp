# MM3D Player draw and mesh visibility

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

## Player model-field alignment

The model-selector fields can be aligned without using host struct offsets.
This local MM3D `Player` window preserves the N64 field order and enum
semantics while widening its display-list pointers. Three independent selector
functions confirm the pointer roles: `FUN_00201074` consumes `+0x210`,
`FUN_00211aa4` consumes `+0x214`, and `FUN_0020cfa4` consumes `+0x218`.

| MM3D `Player` offset | typed 2S2H field | selector evidence |
|---:|---|---|
| `+0x070` | `actor.speed` | right-hand open-to-closed override compares its IEEE-754 bits with `0x40000000` (`2.0f`) |
| `+0x1f8` | `currentShield` | signed byte, indexes the two-entry shield table after subtracting one |
| `+0x1f9` | `currentBoots` | signed byte, compared with `5`, exactly `PLAYER_BOOTS_ZORA_UNDERWATER` |
| `+0x1fb` | `heldItemAction` | bottle-content fallback, accepted only in the exact `0x15..0x2b` bottle-action range |
| `+0x1fe` | `itemAction` | primary bottle-content action and the final Deku-stick test (`7`) |
| `+0x1ff` | `transformation` | indexes all five-form tables in retail enum order |
| `+0x208` | `leftHandType` | indexes `PlayerModelType`; consumed by the left-hand selector |
| `+0x209` | `rightHandType` | compared with `9`, exactly `PLAYER_MODELTYPE_RH_BOW` |
| `+0x20a` | `sheathType` | compared with `12`, `14`, and `15`, the typed sheath variants |
| `+0x20b` | `currentMask` | compared with `0x14`, exactly `PLAYER_MASK_GIANT` |
| `+0x210` | `rightHandDLists` | default per-form right-hand mesh-table pointer |
| `+0x214` | `leftHandDLists` | default per-form left-hand mesh-table pointer |
| `+0x218` | `sheathDLists` | default per-form sheath mesh-table pointer |
| `+0x370` | `skelAnime.animation` identity | both hand selectors compare exact retail animation IDs |
| `+0x37c` | `skelAnime.curFrame` | bottle in/out thresholds `12.0f`/`36.0f` and Zora guitar threshold `6.0f` |
| `+0x380` | `skelAnime.endFrame` | sign selects the direction of the bottle item-change threshold |
| `+0xe14` | `actionFunc` | Bremen-march and ExchangeItem callback identities |
| `+0x11db0` | `stateFlags1` | hand selectors consume typed movement, swim, carry, and Zora-boomerang flags |
| `+0x11db8` | `stateFlags3` | Deku-stick group 27 is hidden while bit `0x04000000` is set |
| `+0x11e20` | `upperActionFunc` | Giant's Mask open hand compares this callback with `FUN_001ef758` |
| `+0x129bc` bit 16 | MM3D-private transient render flag | forces the open left hand; set by mount-transition and two actor-contact functions, with no exact typed 2S2H field yet |

The save value used by the Human sheath override is also aligned. At
`0x0020d18c..0x0020d1c4`, retail reads the equipment halfword at save offset
`+0x7a`, applies the mask at `0x00626d2c` (`0x000f`) and shift at
`0x00626d5c` (`0`). These are exactly 2S2H's
`GET_CUR_EQUIP_VALUE(EQUIP_TYPE_SWORD)` constants.

## Sheath and back-shield selector

The complete sheath-limb stage remains inside `FUN_0020cfa4` after the base
reset. Its control flow is:

```c
if (player->currentMask != PLAYER_MASK_GIANT) {
    if (player->transformation == PLAYER_FORM_HUMAN &&
        player->currentShield != PLAYER_SHIELD_NONE &&
        (player->sheathType == PLAYER_MODELTYPE_SHEATH_14 ||
         player->sheathType == PLAYER_MODELTYPE_SHEATH_15)) {
        enable(kBackShield[player->currentShield - 1]);
    }

    if (player->transformation == PLAYER_FORM_HUMAN) {
        sword = GET_CUR_EQUIP_VALUE(EQUIP_TYPE_SWORD);
        enable((player->sheathType == PLAYER_MODELTYPE_SHEATH_12 ||
                player->sheathType == PLAYER_MODELTYPE_SHEATH_14)
                   ? kSheathedSword[sword]
                   : kEmptySheath[sword]);
    } else {
        enable(player->sheathDLists[lod]);
    }
}
```

`enable(-1)` is the absent-slot case. Both retail LOD entries are identical in
every recovered table, so the port can collapse each pair without losing a
selector distinction.

The exact table data is:

| table VA | index | mesh IDs |
|---:|---|---|
| `0x0069144c` | `SHEATH_12`, forms FD/Goron/Zora/Deku/Human | `-1, -1, -1, 8, 5` |
| `0x00691474` | `SHEATH_13`, forms FD/Goron/Zora/Deku/Human | `-1, -1, -1, 8, 5` |
| `0x0069149c` | `SHEATH_14` and `SHEATH_15` | all `-1` |
| `0x006914c4` | Hero Shield, Mirror Shield | `3, 4` |
| `0x006914d4` | sword equip None/Kokiri/Razor/Gilded | `-1, 5, 6, 7` |
| `0x006914f4` | sword equip None/Kokiri/Razor/Gilded | `-1, 13, 15, 17` |

The exact Human CMB inventory independently identifies these groups: mesh 3
uses only `p_shield_h_00`, mesh 4 only `p_shield_m_00`; meshes 5/6/7 contain
the corresponding `p_sword_*` and `p_saya_*` textures, while 13/15/17 are the
three sheath variants. This is an asset corroboration of the binary table, not
the source of the mesh mapping.

The typed port lives in `mm3d_player_sheath_policy.{cpp,h}` with a narrow
2S2H adapter in `mm3d_player_sheath.{cpp,h}`. Its result is additive to the
base mask. Hand/held-weapon selection is a separate selector below.

## Right-hand and held-equipment selector

`FUN_00201074` tail-shares its complete right-hand stage at `0x00211fd4` after
calling the left-hand stage `FUN_00211aa4`. The branch terminates at
`0x00212124`; its literal pool is:

| literal VA | value | role |
|---:|---:|---|
| `0x00212128` | `0x00000402` | `PLAYER_STATE1_2 | PLAYER_STATE1_400` |
| `0x0021212c` | `0x006919bc` | live Player draw state (`+0x78` LOD, `+0x84` right-hand type) |
| `0x00212130` | `0x006913ac` | form-indexed closed-hand table |
| `0x00212134` | `0x00691514` | Human held-shield table |
| `0x00212138` | `0x00691a64` | animation right-hand override pointer table |
| `0x0021213c` | `0x001ef758` | Giant's Mask open-hand upper-action callback |
| `0x00212140` | `0x00691384` | animation-open table |

In exact retail branch order, with `defaultRightHand` initialized from
`Player + 0x210`, the selector is:

```c
if (form == PLAYER_FORM_ZORA &&
    ((stateFlags1 & (PLAYER_STATE1_2 | PLAYER_STATE1_400)) != 0 ||
     ((stateFlags1 & PLAYER_STATE1_8000000) != 0 &&
      currentBoots < PLAYER_BOOTS_ZORA_UNDERWATER))) {
    enable(4);
} else if (rightHandType == PLAYER_MODELTYPE_RH_SHIELD) {
    if (form == PLAYER_FORM_HUMAN && currentShield != PLAYER_SHIELD_NONE) {
        selected = currentMask == PLAYER_MASK_GIANT
                       ? fierceDeityClosed[lod]
                       : heldShield[currentShield - 1][lod];
    } else {
        selected = defaultRightHand[lod];
    }
    enable(selected);
} else if (rightHandType == PLAYER_MODELTYPE_RH_OPEN && actor.speed > 2.0f &&
           (stateFlags1 & (PLAYER_STATE1_8000000 |
                           PLAYER_STATE1_CARRYING_ACTOR)) == 0) {
    enable(closed[form][lod]);
} else if (animationRightHandOverride >= 0) {
    enable(animationOverride[animationRightHandOverride][form][lod]);
} else if (currentMask == PLAYER_MASK_GIANT) {
    enable(upperActionFunc == Player_UpperAction_CarryActor
               ? fierceDeityAnimationOpen[lod]
               : fierceDeityClosed[lod]);
} else if (form == PLAYER_FORM_DEKU &&
           (animationId == 0x26b || animationId == 0x26c)) {
    enable(4);
} else {
    enable(defaultRightHand[lod]);
}
```

The held-shield table at `0x00691514` contains two duplicate-LOD pairs:
Hero Shield mesh `10`, Mirror Shield mesh `11`. The animation pointer table at
`0x00691a64` is `{ 0x006913ac, 0x00691384 }`, so override `0` is closed and
override `1` is open. The animation-open table has
`{ 5, 5, 4, 4, 23 }` in form order; only Deku differs from the default open
table (`mesh 4` instead of `mesh 3`). Animation overrides precede Giant's Mask,
so they retain the live form index; only the no-animation-override Giant branch
deliberately uses Fierce Deity's hand pair regardless of `transformation`.

The animation input is also structurally aligned. `FUN_00201074` obtains the
current linkb frame record and reads its signed right-hand byte at record `+4`;
`-1` means no override and `0/1` select the pointer table above. The next byte
at record `+5` is passed to `FUN_00211aa4` as the left-hand override. 2S2H's
typed `PlayerAnimationFrame.appearanceInfo` exposes the homologous values
through `GET_RIGHT_HAND_INDEX_FROM_JOINT_TABLE`: zero means no override and
`0x0100/0x0200` decode to closed/open. The N64 Rosetta selector in
`z_player_lib.c` uses that macro with the same `{ closed, open }` table and the
same precedence point. Unexpected encoded indices are not retail states, so the
adapter refuses them rather than indexing outside the grounded table.

`FUN_001ef758` is not an address-only guess. Its decomp checks the typed
`PLAYER_STATE1_CARRYING_ACTOR` bit, handles a null `heldActor`, invokes the held
actor action, contains the Cucco actor-ID `0x11` special case, and writes the
same gravity `-0.5f` and terminal velocity `-2.0f` as typed 2S2H
`Player_UpperAction_CarryActor`. This independently identifies the callback.

The Deku IDs are backed by the retail archive rather than names inferred from
textures. `/actors/zelda2_link_new.gar.lzs` contains 1,694 members: 847 CSABs
followed by 847 paired linkb members. IDs `0x26b` and `0x26c` are respectively
`nuts/anim/pn_drink.csab` and `nuts/anim/pn_drinkend.csab`, with their paired
linkb members at indices `0x26b + 847` and `0x26c + 847`.

The focused port is `mm3d_player_right_hand_policy.{cpp,h}`, with typed field,
table-pointer, joint-appearance, callback, and animation-name adaptation in
`mm3d_player_right_hand.{cpp,h}`. It recognizes the live default table pointer
separately from `rightHandType`; this preserves states such as
`Player_CsAction_19`, which sets `RH_FF` while intentionally retaining the
previous right-hand table. Its single selected mesh is additive to the base and
sheath masks.

## Left-hand, sword, and bottle selector

`FUN_00211aa4(Player*, animationLeftHandOverride)` spans
`0x00211aa4..0x00211f8c`. Its literal pools and the helper it calls identify the
visibility inputs without texture inference:

| literal VA | value | role |
|---:|---:|---|
| `0x00211dcc` | `0x006269c4` | 23 bottle-material RGBA records, four floats each |
| `0x00211dd4` | `0x00626b34` | form-indexed bottle hand mesh table |
| `0x00211dd8` | `0x007751d8` | save context used for button-item validation |
| `0x00211ddc` | `0x001ff52c` | ExchangeItem action callback |
| `0x00211de0` | `0x00626b48` | form material indices used by the bottle constant-color call |
| `0x00211de4` | `36.0f` | bottle-out visibility threshold; subtracting `0x00d00000` produces `12.0f` |
| `0x00211de8` | `0x0000026b` | first of the three Deku drink animation IDs |
| `0x00211dec` | `0x00691348` | form-indexed bottle-content mesh table |
| `0x00211fac` | `0x006919bc` | live draw state (`+0x78` LOD, `+0x7c` form, `+0x80` left-hand type) |
| `0x00211fb0` | `0x00691250` | form-indexed open-hand table |
| `0x00211fb8` | `0x00691280` | form-indexed closed-hand table |
| `0x00211fbc` | `0x001eff18` | Bremen-march action callback |
| `0x00211fc0` | `0x00691a5c` | animation left-hand override pointer table |
| `0x00211fc4` | `0x00000402` | `PLAYER_STATE1_2 | PLAYER_STATE1_400` |
| `0x00211fcc` | `0x00691278` | Zora guitar pair, mesh 10 in both LODs |
| `0x00211fd0` | `0x001ef758` | carry upper-action callback |

The exact duplicate-LOD mesh tables, in Fierce Deity/Goron/Zora/Deku/Human
form order, are:

```text
open:            2, 2, 1, 1, 21
closed:          1, 1, 2, 1, 20
one-hand sword:  8, 2, 2, 1, 12
two-hand sword:  8, 2, 2, 1, 18
bottle hand:     6, 8, 8, 6, 0
bottle contents: 7, 9, 9, 7, 24
```

`FUN_00219aa0` at `0x00219aa0..0x00219bf0` filters the selected mesh through
form whitelists at `0x00626950`. Its Human one-hand sword override reads
`0x0068ee50`, which contains duplicate-LOD mesh pairs `12, 14, 16` for
Kokiri/Razor/Gilded. Fierce Deity is the only additive hand case: selecting
mesh 8 also enables mesh 1. The other whitelists are Goron `{1,2,8}`, Zora
`{1,2,8,10}`, Deku `{1,6}`, and Human `{0,12,14,16,18,19,20,21}`.

In exact branch order, the visibility selector is:

1. Use the bottle route when `leftHandType == LH_BOTTLE`, or while retail
   animation `0x107` (`boy/anim/link_normal_free2freeB.csab`) remains on the
   bottle side of marker frame 13. Forward playback uses `curFrame < 13`;
   reverse playback uses `curFrame > 13`.
2. Otherwise force open for live left-hand type 4 plus
   `PLAYER_STATE1_ZORA_BOOMERANG_THROWN`, or MM3D-private render flag
   `Player+0x129bc` bit 16.
3. Convert nominal open to closed above speed `2.0f`, except while swimming,
   carrying an actor, or running `FUN_001eff18`. Decompilation of that callback
   and the N64 Rosetta behavior identify typed `Player_Action_11` (Bremen
   march).
4. Apply the signed linkb override (`-1` none, `0` closed, `1` open).
5. Zora uses open for state mask `0x402`, or while swimming in boots below
   `PLAYER_BOOTS_ZORA_UNDERWATER`. Otherwise guitar-start ID `0x2c1` switches
   to mesh 10 at frame 6, and IDs `0x2c0`, `0x2c2`, and `0x2d3` select mesh 10
   unconditionally.
6. Without an earlier override, Giant's Mask uses Fierce Deity open for the
   carry upper action and Fierce Deity closed otherwise.
7. Apply the Human sword table only for Human `LH_ONE_HAND_SWORD`, a nonzero
   sword equip, and no Giant's Mask.

The bottle-content index is `itemAction - 0x15` through `0x2b`. A primary
action is retained only when one of the four live B/C button items maps back to
that action, or the action callback is `FUN_001ff52c`; otherwise the selector
uses `heldItemAction`, then empty index zero. The save checks honor disabled
button status except under HUD visibility `0x10`, exactly 2S2H
`HUD_VISIBILITY_A_B_C`. Bottle content is visible after frame 12 for IDs
`0x5a/0x60` (bug/fish in), before frame 36 for `0x5c/0x62` (bug/fish out),
hidden for `0x5b/0x5d/0x5e/0x5f/0x61` and Deku drink IDs
`0x26b..0x26d`, and otherwise visible for a nonempty content index. Finally,
`itemAction == PLAYER_IA_DEKU_STICK` enables mesh 27 unless stateFlags3 bit
`0x04000000` is set.

The shared retail GAR independently resolves every numeric animation identity:
`0x5a..0x62` are the named `boy/anim/link_bottle_*` clips, `0x107` is
`link_normal_free2freeB`, `0x26b..0x26d` are `nuts/anim/pn_drink{,end,start}`,
and `0x2c0/0x2c1/0x2c2/0x2d3` are
`pz_gakkiplay/gakkistart/gakkiwait/gakki_demo`. Exact CMB inventory checks
also prove that every selected group exists in its form body.

### Bottle material constant

The call at `0x00211c90..0x00211cc8` is not a skeletal joint transform. It
loads one four-float record from `0x006269c4`, selects the form entry from
`0x00626b48`, and calls `FUN_0020ce94(Player+0x334, material, 0, rgba, 0)`.
The wrapper at `0x0020ce94` forwards to `FUN_001ff274`; its mode-zero path
calls `FUN_00223fc8` with all four components. `FUN_00223fc8` writes the
selected runtime material's constant slot `(constantIndex + 5)`, mirrors the
float values to clamped RGBA8, and `FUN_001ff274` marks the corresponding
constant-presence bit. This is the MM3D equivalent of the already-identified
OoT3D `Model_SetMaterialConstantColor` channel.

The exact form material indices, in Fierce Deity/Goron/Zora/Deku/Human order,
are `6, 3, 4, 3, 5`; the constant index is always zero. Static inspection of
all five shipping form CMBs proves that each target material binds texture
`p_bin_00` and has the same four-stage TEV chain sourcing `CONST[0]`. The
separate visible bottle-content groups bind `p_bin_01`; therefore neither a
bone index nor the content mesh's material index is a valid substitute for the
retail target.

The 23 records are indexed by the already-derived content index
`itemAction - 0x15` with the same button/exchange-action and held-action
fallback. Expressed as exact RGBA8 values (the binary floats are each
`component / 255.0f`), they are:

```text
empty             0,   0,   0,   0    fish              0, 127, 255, 255
spring water    136, 192, 255, 255    hot spring      168, 224, 255, 255
zora egg          0, 128, 128, 255    deku princess  128,  64,   0, 255
gold dust       255, 255,   0, 255    bottle 1C        0, 192,   0, 255
seahorse        255, 192,   0, 255    mushroom       255, 100, 255, 255
hylian loach      0,   0,   0, 255    bug              0, 127, 255, 255
poe             255,   0, 255, 255    big poe        255,   0, 255, 255
red potion      255,   0,   0, 255    blue potion      0,   0, 255, 255
green potion      0, 255,   0, 255    milk           255, 230, 191, 255
half milk       255, 230, 191, 255    chateau        255, 230, 191, 255
fairy           255, 100, 255, 255    moon's tear    255, 230, 191, 255
land deed       255, 230, 191, 255
```

The focused port is `mm3d_player_bottle_material_policy.{cpp,h}`. It consumes
the bottle-route/content index owned by `mm3d_player_left_hand_policy`, and the
typed adapter returns the mesh mask plus material write in one production
result. `mm3d_player.c` submits that write through the existing emit-ordered
`Zelda3D_GL_SetMatConstOverride` channel before the pending draw is captured.

The pure visibility policy is in `mm3d_player_left_hand_policy.{cpp,h}` and
the narrow typed adapter is `mm3d_player_left_hand.{cpp,h}`. The adapter uses
the live display-list table pointer independently of `leftHandType`, rejects
out-of-range linkb indices, and preserves the exact disabled-button rule. The
selected hand, bottle-content, and Deku-stick groups are additive to the base,
sheath, and right-hand masks. MM3D's private bit-16 transient has no exact typed
2S2H homolog and is currently false in the adapter. The N64
`gPlayerAnim_pz_gakkiplay` and
`gakkistart` symbols align the live guitar cases, but retail-only
`pz_gakkiwait` and `pz_gakki_demo` have no independent typed N64 animation
identity.

## PlayerModelType mesh corpus

For later hand-selector work, the pointer array at `0x0069159c` maps the typed
`PlayerModelType` enum to five-form, two-LOD tables. Collapsing duplicate LODs
gives rows in form order Fierce Deity, Goron, Zora, Deku, Human:

| type | table VA | mesh IDs |
|---|---:|---|
| `LH_OPEN` | `0x00691250` | `2, 2, 1, 1, 21` |
| `LH_CLOSED` | `0x00691280` | `1, 1, 2, 1, 20` |
| `LH_ONE_HAND_SWORD` | `0x006912a8` | `8, 2, 2, 1, 12` |
| `LH_TWO_HAND_SWORD` | `0x006912d0` | `8, 2, 2, 1, 18` |
| `LH_4` | `0x00691250` | `2, 2, 1, 1, 21` |
| `LH_BOTTLE` | `0x00691320` | `6, 8, 8, 6, 0` |
| `RH_OPEN` | `0x0069135c` | `5, 5, 4, 3, 23` |
| `RH_CLOSED` | `0x006913ac` | `4, 4, 5, 3, 22` |
| `RH_SHIELD` | `0x006913ac` | `4, 4, 5, 3, 22` |
| `RH_BOW` | `0x006913d4` | `5, 5, 4, 3, 2` |
| `RH_INSTRUMENT` | `0x006913fc` | `5, 5, 4, 3, 25` |
| `RH_HOOKSHOT` | `0x00691424` | `5, 5, 4, 3, 9` |

These are default model-group identities only. The complete right-hand and
left-hand visibility stages are recovered above; the tables are recorded here
as cross-checks rather than used without their selector conditions.

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
the parent zelda3d repository. Add `--require-mids ID...` to turn an expected
selector group set into a failing static asset gate. The tool requires
`ZELDA3D_MM3D_ROM` and never writes extracted asset bytes.

## Remaining draw-policy frontier

The base reset, sheath/back-shield stage, right-hand/held-equipment stage,
left-hand visibility stage, and bottle material-constant stage are ported from
their retail tables and branch order. The next left-hand evidence gaps are the
MM3D-private transient bit, retail-only Zora guitar wait/demo identities, and
an authentic live equipment/bottle capture. Applying another
game's mesh map, defaulting to all groups, or guessing from texture names is
not valid.

## Port integration evidence

The first native-port submission trace reported the renderer default
`0xffffffffffffffff` for every form. The recovered policy was correct, but the
MM draw seam omitted the emit-order snapshot that carries material overrides to
deferred draws. After adding that snapshot centrally, live form submissions
were Human `0x370000000`, Deku `0x2e20`, Goron `0x4c0`, Zora `0xc0`, and Fierce
Deity `0x1600`, exactly matching the recovered table above.
