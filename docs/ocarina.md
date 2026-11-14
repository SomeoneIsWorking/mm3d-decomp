# The ocarina: its screen, its notes and its songs

USA 1.0 layout under Project Restoration. "Live" is the z3d-mods harness on a new file at South
Clock Town's owl statue with the ocarina and every song's quest bit written into the save; the
rest is read from the disassembly and marked so.

## The screen
`gUiScreens[UI_SCREEN_OCARINA]` (`OcarinaScreen`, 0x6F72F4): `playPage` (+0x40) reads 1 on "Play
your instrument" and 0 on the song list; `songCursor` (+0x44) is the list's entry, five to a
row (live, run ctl-mm4: 5 after a move down, 6 after a move right, the Goron Lullaby). A touch on
the staff button (290, 215) opens the list; B closes the ocarina from either page.

The list's fourteen entries are Time, Healing, Epona's, Soaring, Storms; the Sonata, the Goron
Lullaby, its intro, the New Wave, the Elegy; the Oath, the Inverted Song of Time, the Song of
Double Time and the scarecrow's. `gOcarinaListSongs` (0x620D64) holds each entry's row of the
song table plus `OCARINA_LIST_SONG_BASE` (live dump: 18 19 1A 1B 1C 12 13 20 14 15 16 1E 1F 21).

Learned songs are bits of `SaveData.questItems` from `QUEST_SONG_FIRST` (6) in the song table's
order; the Goron Lullaby's intro is bit 24, and the two other ways to play the Song of Time come
with its bit (read from 0x1E145C).

## Notes
The message object (`gMessageObject`, a pointer at 0x6B3724) holds the ocarina mode at
`MESSAGE_OCARINA_MODE` (+0x42C): 0xD in free play (live, ctl-mm4).

The pad update (0x116658) ORs `gPadInjected` (0x72A0DC) into the pad's held word and clears it,
then maps the held word to notes (read). Live (ctl-mm7): a note's pad button written there once a
frame from `Play_Update` sounds that note. Low to high the notes are L, R, Y, X, A, numbered 0 to
4 in the song table.

## Songs
`gOcarinaSongButtons` (0x6A2AF6, 9 bytes a row): a count, then the notes. Rows 0 to 11 are the
Sonata, the Goron Lullaby, the New Wave, the Elegy, the Oath, Saria's, Time, Healing, Epona's,
Soaring, Storms and the Sun's (the names from the N64 game's order; the bytes are a live dump);
12 the Inverted Song of Time, 13 Double Time, 14 the Lullaby's intro.

Live: the Song of Time's six notes, each held four frames with four empty ones between, are
recognised ("You played the Song of Time!") and the game returns to the first day (ctl-mm8). The
same song played by hand on the buttons in the same file does the same, with no question asked
first (ctl-mm9).

## Not done
- No other song was played this way.
- The Song of Time's question was not seen in this file, played either way.
