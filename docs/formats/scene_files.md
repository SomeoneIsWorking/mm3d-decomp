# Scene and room files (`scenes/*.zsi`)

USA rev 1. A scene is `scenes/<name>_info.zsi`, its rooms `scenes/<name>_<n>_info.zsi`. Some are
wrapped in LzS (lzs.md), some are not: of the rooms with stairs, `z2_town_0`, `z2_clocktower_0`,
`z2_ichiba_0`, `z2_backtown_0`, `z2_milk_bar_0` and `z2_musichouse_0` are wrapped, the dungeon and
house rooms are plain; every scene file read so far is wrapped. The game loads a plain file in
place of a wrapped one (z3d-mods run mm-st2: East Clock Town from an unwrapped `z2_town_0`).

## Layout
- Header: `ZSI\x09`, a 12-byte name, then the Z64-style header commands at 0x10. Command words
  that are offsets count from 0x10. OoT3D's files are the same with `ZSI\x01`.
- A room's mesh command (0x0A) leads to one mesh entry whose model pointers name CMB models inside
  the file; a room without geometry has a mesh header with no entry (`z2_inisie_r_5`).
- Room CMBs are version 10 and carry their own texture data. Against OoT3D's version 6: one more
  chunk pointer in the header (qtrs, after the skeleton's), a tangent slice in `vatr` and a
  tangent attribute in each `sepd` after the normal, 0x16C bytes per material, 0x0C per mesh
  entry. (Layout from noclip.website's `cmb.ts`, MIT; read and rewritten by z3d-mods'
  `tools/z3dmods/cmb.py`.)

## Collision (scene command 0x03)
The header is OoT3D's (decomp/oot3d `docs/notes/scene_collision.md`) with two more bytes before
the bounds: the vertex count is at +0x0E and the triangle count at +0x10; the vertex list offset
stays at +0x18 and the triangle list at +0x1C. Vertices are three s16, triangles 20 bytes (u16
type, three u16 corners with flags in the top three bits, s16 normal x3, u16 0, f32 distance):
the normal comes before the zero word, where OoT3D has it after. Every triangle of every scene
fits `(vB - vA) x (vC - vA)` and `n.p == -distance` read that way, and none read OoT3D's way.
A triangle written OoT3D's way is not a floor: Link fell through the Astral Observatory's stairs
(z3d-mods run mm-st5-1) and stands on them written this way (mm-st6-1).
`z2_kindan2`: 1851 vertices from 0x220 end at 0x2D82, 2671 triangles from 0x2D84 end at 0xFE30,
where the next list starts.

## Stairs
Ramps drawn with a stair texture, all sloped quads (15 to 45 degrees), none modelled as steps:
`clsouth_step_01` (z2_clocktower 0), `cleast_step_01` (z2_town 0), `clwest_step_01` (z2_ichiba 0),
`clnorth_en_step` (z2_backtown 0), `mil_step_01` (z2_milk_bar 0), `org_step_01` (z2_musichouse 0),
`dkh_step_01`, `dkh_step_suna_0` (z2_danpei 5, 6, 8), `hak_r02_step_01` (z2_hakashita 2),
`kindan2_kaidan` (z2_kindan2 1; `kindan2_kaidanw` is its side walls), `Z2mitu_step_00`,
`Z2mitu_step_01` (z2_miturin 3, 10), `om_step_01` (z2_omoya 1), `tenmon_step_01`, `tenmon_step_02`
(z2_tenmon_dai 0, 1), `yado_step_01` (z2_yadoya 0).

The collision under them is coarser than the drawn ramp in most scenes: in `z2_kindan2` two
triangles cover the flight and reach 14 units past the drawn ramp's side; in `z2_yadoya` no
sloped collision triangle stays within 30 units of the drawn flight. Only `z2_danpei`,
`z2_miturin` and `z2_tenmon_dai` have collision triangles that lie on the drawn ramps.
