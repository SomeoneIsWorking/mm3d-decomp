# Save files

A file is the first 0x13618 bytes of `gCommonData` (0x7751D8), written whole to `data:/save<n>.bin`
(the path table at 0x6A09A4, indexed by the file number at 0x7887D8 + 0x18).

## Writing
- `Play_SaveAtStatue(play, entrance)` (0x317000) builds the file in place: the entrance to return
  to at `gCommonData` + 0x351C, a flag at + 0x351E, the clock's date and time at + 0x3526, a counter
  at + 0x3530, then `Save_Checksum` (0x1B4EE8, a CRC-16 over the 0x13618 bytes, seed 0x1017)
  into `gCommonData` + 0x1A88, and last a copy of the 0x13618 bytes into the play state's write
  buffer (`PlayState` + 0x3BF4). Its only callers are the two statue actors' update functions,
  0x43F6DC (owl statue) and 0x4BFAB4, on "Yes" of "Save your progress up to this point?".
- `SaveFile_StartWrite(writer)` (0x18DA50), called right after it with `PlayState.saveWriter`
  (+ 0x3BEC), frees a job the writer still holds, then allocates and queues the job that writes
  the buffer (`SaveWriter.buffer`) and sets `SaveWriter.state` to 2. `SaveFile_UpdateWrite`
  (0x18AD44) returns 1 once the writer is idle: when the job is done it frees it, sets the state
  to 0 and clears `CommonData.statueSave` in RAM (the file keeps its 1). The statues' wait states
  call it every update (the owl statue's is 0x48E9D4), and so does `Play_Update` while the writer
  is busy. A write takes under half a second.
- 0x188270, called from `Cutscene_ProcessCommands`, builds the file the same way with
  `CommonData.statueSave` 0 (read, not run). It also copies `SaveData` to `gCommonData` + 0x1A90.

## Loading: a statue file and a cycle file
`SaveFile_Load` reads `CommonData.statueSave` from the file:
- 1 (a statue's save): the file starts at `statueEntrance`, at the saved day and time. Two
  entrances are swapped by flags (0x84A0 to 0x0CA0, 0x9A80 to another). Nothing on the card is
  changed: the file loads the same way again, so in this game a statue save is permanent, not
  the N64 game's owl save that is deleted once loaded.
- 0 (a new file or a cycle's save): the cycle starts over, at entrance 0x1C00 on a file that has
  not left the opening (`gCommonData` + 9 is 0), else 0xD800 at the dawn of the first day.

`CommonData.entrance` (+ 0x3518) is the scene's entrance in play, the one the last scene change
went through (0xD890 at South Clock Town's owl statue, 0x5400 in Termina Field from the warp).
- `SaveFile_StartWriteSlot(writer, n)` (0x43E818) is the file select's writer (new file, copy,
  erase), fed by 0x5923B0.
- `SaveFile_Load` (0x346AB0) reads the file back over `gCommonData` and picks the entrance.

`SaveFile_StartWrite` has no other direct caller in the image.

## Live (USA 1.0 layout under Project Restoration)
- South Clock Town's owl statue is entrance 0xD890. Its first visit plays `hj_tutorial_save.jdx`;
  after it, A in front of the statue shows "Check", then the prompt, then "Progress saved.", and
  `save0.bin` (79384 bytes) holds `SaveData.equipment` at 0x152 as RAM had it.
- Two files saved from the same steps in two runs differ only in the 20 bytes at 0x1380 (small random digits that differ from run to run), their copy at 0x2E08, the checksum at 0x1A88 and the
  clock's seconds at 0x352B.

## Unplaced fields, seen by filling them
Not laid out yet; each was set to 0xFF throughout in a fresh file, in South Clock Town.
- `SaveData` + 0x124C, 160 bytes: with the notebook owned, its list then holds events ("A Stay
  at Stock Pot Inn", "Anju's Anguish", ...) with their schedule bars, so the notebook's event
  flags are in this range.
- `SaveData` + 0x11B0, 92 bytes: the Map screen then draws Clock Town's map on the touch screen,
  so the owned-map bits are in this range. The Map of Termina on the top screen stays blank.
