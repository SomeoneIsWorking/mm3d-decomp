# Cutscenes and the textbox

Findings from z3d-mods (its Start cutscene skip), checked in Azahar on Project Restoration v110's
1.0-layout code.

## Running a script
- `Cutscene_ProcessCommands(play, csCtx, script)` (0x1846B4) runs one frame of a script. It is
  called from `Cutscene_BeginScript` (0x17419C, `bl` at +0x1D8) on a script's first frame, from
  `CutsceneHandler_StartScript` (0x4CF9C4, `bl` at +0x2C, state 1), and from
  `CutsceneHandler_RunScript` (0x3F1A4C, tail `b` at +0x28, states 2 and 4). Ghidra's inventory
  misses the last one: it starts after the two `bx lr` at 0x3F1A44.
- `CutsceneContext` (`play + 0x2428`): `frames` +0x20 is the current frame, `state` +0x264 is 2
  while a script runs. The end frame stays in the script header (u16 at +0x34, read a byte at a
  time because scripts may be unaligned).

## Script format (.jdb)
Scripts sit in their scene's `scenes/<scene>_info.zsi`, each starting with `"\0BDJ"`; the scene
header's command 0x17 lists them (script offset, next entrance, spawn, spawn flags; 8 bytes each).
`CutsceneScript` in `include/z3D.h`: name at +0x0C, command count (s32) at +0x30, end frame (u16)
at +0x34, commands from +0x38. Walking all 334 scripts of the USA dump with the sizes below lands
on the next script's magic every time.

A command is `CsCmdHeader` (u32 id, s32 count) and `count` entries:
- actor cues (ids 100..149, 200, 201, 450..599): 0x30 bytes each, start and end frame at +2, +4;
- 10 (text), 155, 156, 157, 400, 601, 604: 12 bytes each;
- 90 (camera): `count` is the byte length of the data that follows;
- everything else, known to the interpreter or not: 8 bytes each.

## Text inside a cutscene
- `CsCmdText`: text id, start frame, end frame, type, two alternate text ids (0xFFFF: none). The
  box opens after the start frame; at the end frame the interpreter steps `frames` back by one
  every frame until the box has closed.
- `Message_GetState(play + 0x8020)` (0x1C5018) returns 4 while a choice waits for the player, only
  after its text has printed. On an answer the interpreter continues with `altTextId1` (first
  answer) or `altTextId2` (any other), or closes the box where that id is 0xFFFF. Type 3 then
  shows the question again after `altTextId1`'s text.
- Types 4 (the four remains) and 5 (all masks) show `altTextId1` instead of the text when the
  player has them; type 2 is an ocarina prompt. The script has no other mark of a question.
- One script in the game asks: `climia_raiders.jdb` (Gorman Track, `z2_koeponarace`), text 0x33BD
  "Do you understand? No/Yes", frames 657-663, type 3, `altTextId1` 0x33BE.
- `Message_CloseTextbox()` (0x1EF228) closes the open box.

## Play state
- `PlayState.buttonsPressed` (+0x34) holds the buttons pressed this frame; bit 3 is Start.
- `PlayState.transitionTrigger` (+0xC529) is 20 when a scene transition is requested.
- `gCommonData` (0x7751D8): `setup` (+0x1361C) is 1 on the title screen, whose demo is a play-state
  cutscene, and 0 in play (Project Restoration's `common_data.h` name).

## Save data
- `SaveData` (`gCommonData + 8`): `isNight` +4, `day` +0xC, `totalDay` +0x10, `time` +0x18,
  `weekEventReg` +0x1248 (flag n: byte n / 8, bit n % 8, as a scene's spawn flags index it; the
  first visit to Gorman Track sets flag 4 at 0x14D670).

## Checking it
New file from boot: ending the opening narration (`legend.jdb`) and the Lost Woods script
(`lw_meetstk.jdb`) by stepping `Cutscene_ProcessCommands` to the end frame leaves CommonData's
`start`, `scene` and SaveData (0x1A90 bytes) byte-identical to watching them, compared at frame
100 of the next script.

The milk run's raid cutscene: with `weekEventReg[22] |= 1` (the ranch was defended),
`weekEventReg[31] |= 0x80` (riding with Cremia), `day` 2, `time` 0xC800 and `isNight` 1, entrance
0x3E50 plays `climia_trap.jdb` on Milk Road and 0xCE20 plays `climia_raiders.jdb`.
