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

## Text inside a cutscene
- `Message_GetState(play + 0x8020)` (0x1C5018) returns 4 while a choice waits for the player.
- `Message_CloseTextbox()` (0x1EF228) closes the open box.

## Play state
- `PlayState.buttonsPressed` (+0x34) holds the buttons pressed this frame; bit 3 is Start.
- `PlayState.transitionTrigger` (+0xC529) is 20 when a scene transition is requested.
- `gCommonData` (0x7751D8): `setup` (+0x1361C) is 1 on the title screen, whose demo is a play-state
  cutscene, and 0 in play (Project Restoration's `common_data.h` name).

## Checking it
New file from boot: ending the opening narration (`legend.jdb`) and the Lost Woods script
(`lw_meetstk.jdb`) by stepping `Cutscene_ProcessCommands` to the end frame leaves CommonData's
`start`, `scene` and SaveData (0x1A90 bytes) byte-identical to watching them, compared at frame
100 of the next script.
