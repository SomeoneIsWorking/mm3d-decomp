# Grezzo LzS container (`LzS\1`) — SOLVED

Wraps some (not all) of MM3D's `/actors/zelda2_*.gar.lzs` archives. The `.gar.lzs` extension
is misleading — many files are raw GAR2, but ~40% are LzS-wrapped GAR2. Detection: peek the
first 4 bytes (`GAR\2` vs `LzS\1`).

## Header (16 bytes)

```
+00  char[4]  magic        "LzS\1"
+04  u16      flags1       = 0x0001 in every sample (version?)
+06  u16      flags2       varies (0x762F, 0x4E75, 0xC1AF, ...) — unused by the decoder
+08  u32 LE   decompressed_size    matches expected raw GAR2 length
+0C  u32 LE   compressed_size      = file_size - 0x10
+10  ...      compressed stream starts here
```

Samples:

| archive               | file_size | dec_size | cmp_size | flags1 | flags2 |
| --------------------- | --------: | -------: | -------: | -----: | -----: |
| zelda2_box            |    90 658 |  135 200 |   90 642 | 0x0001 | 0x762F |
| zelda2_boj            |   148 923 |  217 088 |  148 907 | 0x0001 | 0xD7DF |
| zelda2_goroiwa        |   143 982 |  270 548 |  143 966 | 0x0001 | 0x4E75 |
| zelda2_obj_tokeidai   |   192 560 |  269 972 |  192 544 | 0x0001 | 0xC1AF |

## Compressed stream — classic LZSS with a 4096-byte ring dictionary

The encoding is standard LZSS in the "Haruhiko Okumura / de-facto Nintendo" shape, wrapped
by Grezzo's 16-byte header. Notes:

- **Ring buffer**: 4096 bytes, preinitialized to `0x00`. Initial `writeidx = 0xFEE`
  (matches the Okumura reference implementation). This is the reason the first back-refs
  in any archive appear to emit `00 00 00` — they're pointing into the still-zeroed
  dictionary region, which was the last piece of the puzzle we needed. (See `lzs_hunt.md`.)
- **Control byte**: 8 flag bits read LSB-first. `bit=1` means a literal byte follows;
  `bit=0` means a 2-byte back-reference follows.
- **Literal**: read 1 stream byte, append to output, write to `buffer[writeidx]`,
  `writeidx = (writeidx + 1) & 0xFFF`.
- **Back-reference**: read 2 stream bytes `b1`, `b2`. Then
  - `readidx  = b1 | ((b2 & 0xF0) << 4)` (12-bit dictionary position)
  - `matchLen = (b2 & 0x0F) + 3`   (3..18 bytes)
  - Copy `matchLen` bytes from `buffer[readidx++ & 0xFFF]` to the output *and* to
    `buffer[writeidx++ & 0xFFF]` (each byte is added to the dictionary as it streams).

## How we finally found it

Static reversing kept missing the decoder — the Grezzo compiler doesn't use
MOVW/MOVT (zero occurrences in `.code`) and the LzS magic `0x01537A4C` never appears
as raw bytes in the code section, so both literal-pool and MOVW/MOVT hunts drew blanks.
Body-heuristic LZ77 scanning across the whole 13598-fn set was too noisy (top hits
were 3DS texture-format converters, not compressors).

The break came from a web search: `xdanieldzd/Scarlet` (Scarlet.IO.CompressionFormats/
GrezzoLZS.cs) already had the exact decoder. Cross-referenced against a Python port
of that algorithm running on real archives (`zelda2_boj`, `zelda2_box`) — both produced
a valid `GAR\2` header at the expected uncompressed size. Ported to
`Shipwright/cmb3d/asset/lzs.{h,cpp}` and wired into the MM3D actor-archive path.

## Related archive formats
- **GAR2** (raw): sibling `.gar.lzs` files (magic `GAR\2`) — parsed by
  `Shipwright/cmb3d/asset/gar.cpp`.
- **ZAR** (OoT3D): older Grezzo archive format used by OoT3D, structurally similar to GAR2
  but with a smaller 0x18 header.

## References
- Scarlet `GrezzoLZS.cs`: <https://github.com/xdanieldzd/Scarlet/blob/master/Scarlet.IO.CompressionFormats/GrezzoLZS.cs>
- ShimmerFairy MM3D `lzs.cpp` (linked from Scarlet, same algorithm)
