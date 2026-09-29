# `mm3d-decomp/src/` — organized decompiled output

One directory per **module**, where a module is the original C++ source file the
developers' own assert strings name. Not one directory per address range: MM3D's
`.text` is not laid out in per-file blocks (see `docs/code_layout.md`), so the module
is a *set* of functions scattered across the image.

Module directories drop the `.cpp` extension (`z_play.cpp` -> `z_play/`); the
authoritative name with the extension is in `build/decomp/modules.json` and
`docs/code_layout.md`.

## File naming

```
<module>_<vaddr8>[_<pinned_symbol>].c     one file per recovered function
<module>/<module>.h                      prototypes for everything in the directory
```

The module prefix is the point: a file says which subsystem it belongs to, so the tree
can be browsed by module and searched by address inside it. A semantic suffix is added
**only** where an existing doc in this repo already pins that function's role, and the
header comment cites that doc. Nothing is named speculatively.

## Placement rule

| tier | rule | files |
|---|---|---|
| `anchored` | the function's own body executes an ARM `LDR rX,[pc,#imm]` whose literal
pool word is the address of an assert path ending `...\<file>.cpp(<line>)` | 14 |
| `helper1` | directly called by an anchored function of exactly one file, and by no
other file's anchor | 15 |

`helper1` is an inference. Both tiers are stated in every file header.

## What is in the tree right now

| module | files | of which anchored | largest recovered function |
|---|---|---|---|
| `MenuMapState/` | 3 | 3 | `005975ac` (6728 B) |
| `ObjectBankArchive/` | 3 | 3 | `001d4844` (3240 B) |
| `SceneGraph/` | 2 | 2 | `0011f074` (200 B) |
| `actor_util/` | 7 | 3 | `00160d64` (412 B) |
| `z_kankyo/` | 1 | 1 | `0018ff04` (1676 B) |
| `z_play/` | 5 | 1 | `0012a7d4` (2432 B) |
| `z_player/` | 8 | 1 | `001f5e88` (4672 B) |

## Full module manifest — the plan, with what is recovered

104 source files are named by assert strings; 7 have at least one function placed in
this tree. The rest are targets.

| module | anchored | helper1 | in tree |
|---|---|---|---|
| `MenuMapState` | 3 | 66 | 3 |
| `MenuFileSelecterState` | 2 | 39 | 0 |
| `z_play` | 1 | 30 | 5 |
| `z_player` | 1 | 18 | 8 |
| `LayoutDrawManager` | 1 | 17 | 0 |
| `MenuScheduleState` | 2 | 16 | 0 |
| `ActorMultiEffect` | 6 | 11 | 0 |
| `graph` | 1 | 14 | 0 |
| `MoviePlayer` | 4 | 11 | 0 |
| `imageHelper` | 2 | 10 | 0 |
| `z_dm_char01` | 1 | 11 | 0 |
| `z_obj_chan` | 1 | 10 | 0 |
| `z_daytelop` | 1 | 9 | 0 |
| `fileEntityContainer` | 1 | 8 | 0 |
| `z_movie` | 1 | 7 | 0 |
| `fileUtility` | 4 | 3 | 0 |
| `MessageManager` | 2 | 5 | 0 |
| `actor_util` | 3 | 4 | 7 |
| `SceneGraph` | 2 | 4 | 2 |
| `z_effect_soft_sprite` | 2 | 4 | 0 |
| `ObjectBankArchive` | 3 | 3 | 3 |
| `z_en_test3` | 1 | 5 | 0 |
| `z_en_honotrap` | 1 | 5 | 0 |
| `WaterSurface` | 1 | 5 | 0 |
| `MenuOptionState` | 1 | 5 | 0 |
| `LayoutMenuHintPlayer` | 1 | 4 | 0 |
| `z_oceff_storm` | 1 | 4 | 0 |
| `LayoutClass` | 2 | 3 | 0 |
| `Package` | 3 | 1 | 0 |
| `LayoutManager` | 1 | 3 | 0 |
| `HintMovieManager` | 2 | 2 | 0 |
| `TextSprite` | 2 | 2 | 0 |
| `EffectMaterialUpdater` | 1 | 3 | 0 |
| `z_en_po_sisters` | 1 | 3 | 0 |
| `z_eff_shield_particle` | 2 | 2 | 0 |
| `z_sram` | 2 | 1 | 0 |
| `z_actor` | 2 | 1 | 0 |
| `EnemyBasicEffectContainer` | 3 | 0 | 0 |
| `z_en_am` | 1 | 2 | 0 |
| `z_en_bb` | 1 | 2 | 0 |
| `z_en_jso2` | 1 | 2 | 0 |
| `z_eff_tire_mark` | 2 | 1 | 0 |
| `fileEntity` | 1 | 2 | 0 |
| `Project` | 2 | 1 | 0 |
| `ScreenCapture` | 2 | 0 | 0 |
| `homeRejectIcon` | 1 | 1 | 0 |
| `z_visfbuf` | 1 | 1 | 0 |
| `Luminary` | 2 | 0 | 0 |
| `MultiTorchModelContainer` | 2 | 0 | 0 |
| `z_en_wiz` | 1 | 1 | 0 |
| `z_eff_spark` | 2 | 0 | 0 |
| `z_en_bbfall` | 1 | 1 | 0 |
| `z_obj_jgame_light` | 1 | 1 | 0 |
| `MajoraEffect` | 2 | 0 | 0 |
| `ExtraPadCheckDialog` | 1 | 1 | 0 |
| `DisplayBoardManager` | 1 | 0 | 0 |
| `TbdRes` | 1 | 0 | 0 |
| `gamealloc` | 1 | 0 | 0 |
| `LayoutBuilder` | 1 | 0 | 0 |
| `SaveDataMaintainer` | 1 | 0 | 0 |
| `LayoutFactory` | 1 | 0 | 0 |
| `z_fbdemo_wipe3` | 1 | 0 | 0 |
| `z_lights` | 1 | 0 | 0 |
| `z_kankyo` | 1 | 0 | 1 |
| `VRBox` | 1 | 0 | 0 |
| `z_eff_footmark` | 1 | 0 | 0 |
| `z_fireobj` | 1 | 0 | 0 |
| `z_boss_06` | 1 | 0 | 0 |
| `z_en_part` | 1 | 0 | 0 |
| `z_eff_ss_dust` | 1 | 0 | 0 |
| `z_eff_ss_blast` | 1 | 0 | 0 |
| `z_eff_ss_bomb2` | 1 | 0 | 0 |
| `z_eff_ss_g_spk` | 1 | 0 | 0 |
| `z_eff_hahen` | 1 | 0 | 0 |
| `z_eff_ss_bubble` | 1 | 0 | 0 |
| `z_eff_ss_g_fire` | 1 | 0 | 0 |
| `z_eff_ss_sibuki` | 1 | 0 | 0 |
| `z_eff_ss_stone1` | 1 | 0 | 0 |
| `z_eff_ss_dead_db` | 1 | 0 | 0 |
| `z_eff_ss_dead_dd` | 1 | 0 | 0 |
| `z_eff_ss_dead_ds` | 1 | 0 | 0 |
| `z_eff_ss_hitmark` | 1 | 0 | 0 |
| `z_eff_ss_g_splash` | 1 | 0 | 0 |
| `z_eff_ss_kirakira` | 1 | 0 | 0 |
| `z_eff_ss_dt_bubble` | 1 | 0 | 0 |
| `z_eff_fhg_flash` | 1 | 0 | 0 |
| `z_eff_ss_ice_smoke` | 1 | 0 | 0 |
| `z_eff_ss_lightning` | 1 | 0 | 0 |
| `z_room` | 1 | 0 | 0 |
| `z_eff_en_ice_block` | 1 | 0 | 0 |
| `z_en_elf` | 1 | 0 | 0 |
| `z_eff_blure` | 1 | 0 | 0 |

Named by an assert string but with no function attributed yet (asserts reached through a
pointer, or the referencing function was not split out by Ghidra): `FragmentEffectContainer.cpp`, `first_game.cpp`, `main.cpp`, `z_boss_01.cpp`, `z_eff_ss_extra.cpp`, `z_eff_ss_g_ripple.cpp`, `z_en_bigpo.cpp`, `z_en_clear_tag.cpp`, `z_en_jso.cpp`, `z_en_light.cpp`, `z_obj_syokudai.cpp`, `z_scene_proc.cpp`.

## Reproducing

```bash
# 1. re-derive the module model (writes build/decomp/modules.json)
uv run --frozen python scratch/mm3d_modules/modules.py
# 2. decompile any function by address
cd <zelda3d checkout>
MM3D_DECOMP_OUT=$PWD/mm3d-decomp/build/decomp DECOMP_TARGETS=0x001f5e88 \
  analyzeHeadless build/ghidra-mm3d mm3d -process -noanalysis \
    -scriptPath mm3d-decomp/tools -postScript DumpDecomp.py
# 3. place it into its module directory
uv run --frozen python scratch/mm3d_modules/treesrc.py
```

