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
- `SaveFile_StartWrite(writer)` (0x18DA50), called right after it with `PlayState` + 0x3BEC, queues
  the job that writes the buffer; `SaveFile_UpdateWrite` (0x18AD44) returns 1 once it is done.
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
