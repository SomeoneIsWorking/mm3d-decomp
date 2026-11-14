# Messages: parsing and printing

USA 1.0 layout. Read from the disassembly and live memory (z3d-mods harness, runs mm-q0 to mm-q3).

## The message file
`romfs:/message/us/use.gmsg` (`GMSG`, version 1.0): a 16 byte header (magic, u16 major, u16
minor, u32 message count, u32 language bits), then one entry a message: u16 id, u16, u32, u32
flags, and an offset and length of the text per language. `MessageData_Init` is 0x15A240.
- Flag bit 0 marks a message that prints at once (1053 of the 6152 US English messages; the owl
  statue's "Save your progress up to this point?" is one).
- Text is bytes. 0x7F starts a control code: pad to an even address, a u16 code, its argument
  (none, a u16, a u32 at a multiple of four, or strings, by the table at 0x63DCCC), pad to even.

Codes seen in the US text, by what the printer does with them:

| Code | Does |
|---|---|
| 0x00 | ends the message |
| 0x01 | new line |
| 0x02 | new box (follows a 0x31) |
| 0x27 | instant text on |
| 0x28 | instant text off |
| 0x29 n | delay |
| 0x2B n | the last box waits for A |
| 0x2D n | printing speed, an index of the table at 0x61FA8C (4, 2, 1.5, 1, 0.75, 0.5, 0.25) |
| 0x2F n | a choice of n answers |
| 0x31 n | wait for A |
| 0x3A n | text colour |

0x27 and 0x28 come in pairs around a phrase (704 and 703 uses).

## Parsing
- `MessageMgr_Get` (0x1C51D0) returns the manager at 0x6B36F8; `gMessageObject` (+0x2C) is its
  message window, and its message set is at +0x38.
- `MessageSet_Parse(set, id, language, mgr)` (0x1B8BDC) looks the message up and runs
  `Message_ParseText(state, text, parser)` (0x17EC80) over it. The parser (set +4, vtable
  0x63D31C) gets each run of plain characters and, through
  `Message_DispatchControlCode` (0x1963C8), one call per control code. Most codes append an
  element to the set; the name, number and time codes append characters.
- `MessageSet_Parse` also copies the entry's flags into the manager: bit 0 to mgr +0x80.
- An element's method at vtable +0x10 takes a visitor and calls the visitor's method for its
  code. Two visitors walk the set: the text state's layout (window +0x364, visitor at +0xC,
  vtable 0x63C8D8), which places glyphs and lines, and the printer.

## Printing
`MessagePrinter` (window +0x368, vtable 0x63D180) reveals the laid-out text.
- `MessageWindow_StartPrinter(window)` (0x1D1D9C) starts a message: `MessagePrinter_Start`
  (0x1D885C) clears the counters and flags and sets the state to printing, then `instant` is
  set from mgr +0x80.
- `MessagePrinter_Update(printer, seconds)` (0x1D85B8) runs once a frame. While printing it adds
  `speed` x the speed table's entry x seconds to `printed` and visits elements until `shown`
  catches up with 30 x `printed`. With `instant` set, or while the input object says a button
  is held, it adds 99999 instead, and each element visited raises the count again, so
  everything up to the next state change prints in that update.
- A code changes the state through its method: 0x29 to delay (the time in `delay`), 0x31 to
  wait for A, 0x2B to the last wait, 0x2F to a choice. The visiting loop stops as soon as the
  state is no longer printing, so a delay still pauses instant text.
- `MessagePrinter_InstantOn` (0x607604, vtable +0x14) and `MessagePrinter_InstantOff`
  (0x607584, +0x18) set and clear `instant`.
- Each box is printed from the start: after the A of a 0x31 the printer starts again with its
  counters at zero.

Live, the carpenter in South Clock Town (message 0x61B, 67 characters, no codes but the last
wait): the state is printing for 46 frames, `shown` rising to 67, then the last wait.

## Checking it
z3d-mods' Quick Text calls the printer's `instantOn` before every update in which the state is
printing (its `patch/mm3d/quick_text.cpp`). The carpenter's 67 characters are then all shown
two frames after the printer starts instead of 46 (mm-qt-on against mm-qt-off). With the
guard's message 0x516 in the carpenter's entry (three boxes, a 0x27 and 0x28 pair, a 0x29 of
ten), each box is whole in its first update and the third stops after "..." for half a second
(state 3, 32 frames) before "A sword?" (mm-qt-box).
