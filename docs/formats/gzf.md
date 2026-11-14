# GZFX: the text font

`romfs:/message/ltn16.gzf` (USA rev 1, 87680 bytes), read from the file and written back byte
for byte by z3d-mods' `tools/z3dmods/gzf.py`:

- Header, little-endian: `"GZFX"`, u16 0, u16 4, u16 0x30 (where the sheet table starts), u16 8
  (a sheet entry's size), u32 0xC (a glyph entry's size), u32 3 (sheets), u32 468 (glyphs), u32
  0x2A (`*`, taken to be the character drawn for one the font lacks), u16 2 (taken to be the
  sheets' format: the loader finds the bits a pixel through it), u16 0, u16s 11, 16
  (the cell's width), 5, 16, and u32 18 (the cell's height). 11 and 5 are taken to be the
  ascent and descent; the capitals stand on row 13 of a cell.
- Sheet table at 0x30, 8 bytes a sheet: u32 file offset, u16 width, u16 height: 0x1680 256x256,
  0x9680 256x256, 0x11680 256x128. They end exactly at the file's end.
- Glyph table at 0x48, 12 bytes a glyph, sorted by character code: u32 code, u16 the advance,
  u16 the sheet, u16 where the advance box starts in the cell, u8 the cell's column, u8 its
  row. A glyph is drawn with its cell's left edge at the pen minus the start, and the pen
  moves on by the advance: a space is 4 and 6, `!` 4 and 7, `W` 13 and 2. Sheet 0 is Latin-1
  from 0x20; sheets 1 and 2 hold Latin Extended-A, Greek, Cyrillic, punctuation and symbols.
- A sheet is a PICA 4-bit alpha texture as the GPU takes it: 8 by 8 tiles, a pixel's nibble
  at its Morton index in the tile, the low nibble of each byte first, rows from the top. Cells
  are 16 by 18, sixteen a row.
- The game hands each sheet to the GPU whole: Azahar's texture dump at a dialog holds sheet 0
  as one 256x256 A4 texture whose name is the hash of the sheet's bytes, 510A49A1A046A54B
  (z3d-mods run `txt-dump2`). So a texture pack can replace a sheet, and a font file with
  other sheets is replaced under the hash of those: a font drawn from an outline font prints
  in a dialog from a pack's 2048x2048 copy (runs `txt-mm-r1`, `txt-mm-r4`).
- In the code (the 1.0 layout): `GzfFont_Init(font, data, size)` (0x133930) checks the magic
  (the literal at 0x133A54), the entry sizes and that every sheet starts on a multiple of
  0x80 and ends inside the file, and keeps the file (+4), its size (+8), the sheet table
  (+0xC) and the glyph table (+0x10). The path is a string at 0x104EA0 and again at 0x6001F8.
  What draws a glyph is not read.
