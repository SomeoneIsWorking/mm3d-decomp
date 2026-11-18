# The frame

How one 30 Hz tick runs, from the disassembly of the code the USA set runs (`code.bin` of the
installed base mod, loaded at 0x100000). The engine's shape is OoT3D's (decomp/oot3d
`docs/frame.md`); the addresses are MM3D's own.

- `Play_Main` (0x14F698), the play state's main, runs `Play_Update` (0x15F644, at +0x78), the
  tick's logic, then `Play_Draw` (0x15EB34, at +0x160, `PLAY_MAIN_DRAW_CALL`), which records the
  tick's draws. Around the draw it copies the 0x6C bytes at `PlayState + 0x28` aside and back.
  `Play_Draw` sets up the view, draws the scene transition through the function pointer at
  `PlayState + 0xCA94` on the instance at `+0xC860` (when `PlayState + 0xC85A` is 3 or 11, among others), and
  the rest of the scene.
- The game thread's loop (the function that holds 0x104D08 to 0x105164) runs the game state, then
  0x109F40 and 0x1103B0, then `Graph_DrawFrame` (0x10677C) at 0x105154, and loops.
- `Graph_DrawFrame` turns the tick's draws into the PICA command list; its last call, at +0xA04
  (0x107180, `GRAPH_DRAW_FRAME_END_CALL`), is the frame end, `Graph_FrameEnd` (0x124EE8), a direct
  call here where OoT3D's is virtual. The frame end ends with `Graph_RunBoundCmdlist` (0x140B38),
  which runs the bound command list (`nngxRunCmdlist` 0x15BC00, the same 12 words as OoT3D's
  0x311954). Two more calls of the frame end come from 0x1250EC.

The draw section a replay runs again (z3d-mods docs/plans/replay-interpolation.md) is from
`Play_Main` +0x160 to `Graph_DrawFrame` +0xA04. What it touches (its census) is not measured yet.
