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
- `Graph_RunBoundCmdlist` takes a pair at the frame end's `this` + 0xAC: an index and two list
  ids. It binds the indexed one (`nngxBindCmdlist` 0x136A1C), runs it, flips the index and binds
  the other: the command lists are double-buffered, as in OoT3D.
- The command-list object is OoT3D's (`GxCmdlist`, `GxRequest` in include/z3D.h; nngxBindCmdlist
  allocates 0x44 bytes for one); the bound one is `gNngxState.boundCmdlist` (0x7B2700 + 0x9C,
  read by nngxRunCmdlist and written by nngxBindCmdlist).

## Requests

A `GxRequest` is nngx's own record, not a GSP command: its first byte is the kind (the GSP
command id it becomes), byte 2 set stops the run after it, and six words follow. The frame end's
dispatcher, 0x1490F4 (from `nngxRunCmdlist`), turns each into GSP commands as follows (`r1` to
`r6` the words):

- 0, DMA: source `r1`, destination `r2`, size `r3`.
- 1, command list: address `r1`, size `r2`; bit 0 of `r3` is the GSP command's flag, and unless
  bit 2 of `r3` is set a cache flush of the list (GSP command 5) goes first.
- 2, memory fill: per buffer a start (`r1`, `r4`), a value (`r2`, `r5`) and a size word (`r3`,
  `r6`): the byte count in bits 0 to 22 (the end is start plus count) and the fill width in bits
  23 and 24 (the GSP control is `(word >> 15 & 0x300) | 1`). A start of 0 is no buffer.
- 3, display transfer: input `r1`, output `r2`, the input and output sizes `r3` and `r4` as the
  GSP takes them (width low, height high), and `r5` in nngx's flag bits: bit 6 the flip, bits 0-2
  the input format, 3-5 the output format, 7-8 the scaling, 9 the 32-pixel blocks, 10 linear input,
  11 no swizzle. The GSP's crop bit (2) is set when the output is narrower or shorter than the
  input.
- 4, texture copy: input `r1`, output `r2`, size `r3`; `r4` and `r5` hold the input's and output's
  width and gap with their halves the other way round from the GSP's; the GSP flags are 8, with 4
  when either gap word's low half is nonzero.

## What the draw section touches

The draw section a replay runs again (z3d-mods docs/plans/replay-interpolation.md) is from
`Play_Main` +0x160 to `Graph_DrawFrame` +0xA04. Measured in z3d-mods with the core's store journal
(`interp census` and `probe`, a new file standing in South Clock Town after its first-visit
cutscene, 2026-11-18), per tick:

- About 195 pages stored to (OoT3D: 65), about 1.2 ms of host time, and about 490k instructions in
  a replay: .data/.bss (0x600000-0x7FFFFF, about 28 pages), the 0x08xxxxxx heaps, the linear
  heap's 0x14xxxxxx command lists and buffers, and its stack.
- The bound list's requests: 23 command lists (GX 1), 2 `RequestDma` (GX 0), 1 memory fill (GX 2)
  and the two screens' display transfers (GX 3).
- SVCs on the section's thread (none of OoT3D's ArbitrateAddress signals):
  - three `SendSyncRequest`s to `gsp::Gpu`, FlushDataCache (header 0x00080082, the wrapper
    0x13F310): one from `Graph_DrawFrame` +0x9EC (0x107168, through 0x12F5EC, the size from
    0x192DBC) just before the frame end, and two from 0x137A0C, a buffer upload (0x1BE090 through
    0x16BB14).
  - two `SleepThread`s (0x10FE54, through `nn::os::Thread::Sleep` 0x151CC4) of 100 us each:
    0x199828 binds a vertex buffer (0x16B0A0, target 0x8892), uploads to it (0x1BE090) and then
    sleeps, unconditionally. Its caller, 0x19733C (reached through a pointer), blends two byte
    arrays by a float into the buffer (the loop at 0x197454) and uploads twice a tick.
- Other threads store while the section runs (the window is preempted): their ArbitrateAddress
  objects at 0x7C8D8C to 0x7C8DAC and in 0x15370000-0x15380000, the heap pages 0x152A0000-
  0x152BA000 and 0x15BA1000-0x15BA3000, DSP memory 0x1FF53000-0x1FF77000, and IPC requests (fs among them) in
  other threads' TLS, 0x1FF82C80 among them.
- Run again from the same start state (t = 1, the replay answering FlushDataCache and SleepThread
  itself), the requests and every PICA list are byte for byte the real ones in 180 of 180 ticks
  (5.66 MB of lists). Memory equals the real run's in 91 of 180; the others differ only in the
  page of 0x153730DC (where other threads' ArbitrateAddress objects sit) and the TLS page at
  0x1FF82C80 (another thread's IPC command buffer, on the page the replay's FlushDataCache reply
  stores to). Both are put down to the other writers above, not proven byte by byte.

## Fades

- A scene's fade is the transition's screen fill, OoT3D's `TransitionFade`. `Play_Draw` calls
  `PlayState.transitionCtx.draw` (+0xC860 + 0x234) on the instance at +0xC860 while
  `transitionMode` (+0xC85A) is 3 or 0xB, then `TransitionFade_Draw` (0x172004) on
  `transitionFadeFlash` (+0xCAAC). `TransitionFade_Draw` skips a fill whose alpha (+4) is 0 and
  draws it in the colour at +4, alpha first.
- A warp to South Clock Town (entrance 0xD800, run mm-fade-peek): the draw is
  `TransitionFade_Draw`, type 1; the fade out raises alpha 0x11, 0x44, 0x90 with the timer at +8
  stepping 4, 0x10, 0x22, to white; after the load the fade in lowers it from 0xEE through 0x6F to
  0 in black, and the mode goes back to 0. The fade flash stays at alpha 0.

## Material animations

- Texture scroll and the other material animations (CMAB files) play through `AnimPlayer`s (0xA4
  bytes, vtable 0x63BF00, include/z3D.h). The scene's are stepped in the update, not the draw as
  in OoT3D: `Play_Update` calls `Scene_UpdateRoomAnims` (0x171DA0, from 0x15FC3C), which for the
  current room (`PlayState` +0xC260) and the previous one (+0xC2C4), while each is loaded (+7) and
  bit 0 of `PlayState` +0xAAC is clear, runs `AnimPlayerList_Update` (0x194CA8) on the room's
  list at +0x20, then the scene's update handler from the table at 0x69B098 (16-byte entries by
  `PlayState` +0x14A, the function at +4).
- `AnimPlayerList_Update` calls each player's `AnimPlayer_Update` (vtable +0xC, 0x22419C) at
  +0x30 (`ANIM_PLAYER_LIST_UPDATE_CALL`, r0 the player). `AnimPlayer_Update` calls `AnimPlayer_Step`
  (vtable +8, 0x5EC198) when `autoStep` is set, then applies the frame to each target, which
  writes the materials the draw reads. `AnimPlayer_Step` adds `speed` to `frame`, wraps it at the
  animation's frame count when `loop` is set (holds it there otherwise, setting `done`), and does
  nothing while `paused` or the player's group bit (+0x1C) is set in the word at 0x6A3A18. The
  frame count is the CMAB's: `anim->file` (+4 of the `CmabResource` at +0xC), its block at
  `animOffset`, the count at the block's +4.
- Found by a memory scan for a float stepping by the word after it each tick, then write watches
  on it and on the game thread's stack (the step's pushed return addresses): South Clock Town's
  room list holds one player (2400 frames, speed 1, looping), the actors' players are updated
  elsewhere (`AnimPlayer_Update` returning to 0x224148).
