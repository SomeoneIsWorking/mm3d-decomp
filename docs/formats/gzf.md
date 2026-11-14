# GZFX: the text font

`romfs:/message/ltn16.gzf` (USA rev 1, 87680 bytes), read from the file:

- Header, little-endian: `"GZFX"`, u16 0, u16 4, u16 0x30 (where the sheet table starts), u16 8,
  u32 0xC (a glyph entry's size), u32 3 (sheets), u32 468 (glyphs), u32 0x2A (`*`, taken to be
  the character drawn for one the font lacks), u32 2, then u16s 11, 16, 5, 16 and u32 0x12 (cell
  and line measures, not told apart yet).
- Sheet table at 0x30, 8 bytes a sheet: u32 file offset, u16 width, u16 height: 0x1680 256x256,
  0x9680 256x256, 0x11680 256x128. At 4 bits a pixel they end exactly at the file's end.
- Glyph table at 0x48, 12 bytes a glyph, in code order from 0x20: u32 character code, u32 and u16
  measures (a space 4 and 6, `!` 4 and 7, `#` 10 and 4: taken to be the advance and the left
  edge), u16 the glyph's number in the sheets.
- The sheets drawn as plain row-major nibbles are not readable: they are taken to be in the
  3DS's tiled texture order, not checked.
- In the code: the magic `GZFX` is a literal at 0x133A2C, the path a string at 0x104EA0 and again
  at 0x6001F8 (pointed at from 0x600B34, in ExtraPadCheckDialog.cpp's range); the functions around
  them are not read. The messages are `message/us/use.gmsg`, `usf.gmsg` and `uss.gmsg` (`GMSG`),
  not decoded here.
