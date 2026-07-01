# Grezzo LzS container (`LzS\1`)

Wraps some (not all) of MM3D's `/actors/zelda2_*.gar.lzs` archives. The `.gar.lzs` extension
is misleading — many files are raw GAR2, but ~40% are LzS-wrapped GAR2. Detection: peek the
first 4 bytes (`GAR\2` vs `LzS\1`).

## Header (16 bytes, verified from 4 sample files)

```
+00  char[4]  magic       "LzS\1"
+04  u16      flags1      = 0x0001 in every sample (compression version?)
+06  u16      flags2      varies wildly (0x762F, 0x4E75, 0xC1AF, ...) — not a size
+08  u32 LE   decompressed_size    matches expected raw GAR2 length
+0C  u32 LE   compressed_size      = file_size - 0x10
+10  ...      compressed stream starts here
```

Samples:

| archive               | file_size | dec_size | cmp_size | flags1 | flags2 |
| --------------------- | --------: | -------: | -------: | -----: | -----: |
| zelda2_box            |    90 658 |  135 200 |   90 642 | 0x0001 | 0x762F |
| zelda2_goroiwa        |   143 982 |  270 548 |  143 966 | 0x0001 | 0x4E75 |
| zelda2_obj_tokeidai   |   192 560 |  269 972 |  192 544 | 0x0001 | 0xC1AF |

## Compressed stream (partially reversed, see `lzs_hunt.md`)

- Byte-based with 8-bit control bytes interleaved with encoded units.
- First control byte in every sample is `0xFF`, followed by 8 raw literal bytes — those
  produce the expected `GAR\2` + fileSize header of the decompressed GAR2. This confirms
  `bit=1 => literal` and that ctrl bits are read LSB-first (any bit order works for the
  all-ones case, but the next block confirms LSB).
- Second control byte in every sample is `0x5F`. LSB-first with `bit=1=literal` produces the
  correct decompressed sequence for byte 8-12 of the GAR2 header (nTypes u16, nFiles u16,
  typesOff low byte).
- What produces the next 3 output bytes (which must be `00 00 00` to complete typesOff u32)
  remains **unresolved**. The stream bytes at that position are `eb f0` — this must be a
  2-byte "back-reference" token in the LZ77 sense, but the standard encodings all fail:
  - `(len_high4, disp_low12)` LE: disp=0x0EB=235, len=0+3=3 — but disp>current_out (13 bytes)
  - `(len_high4, disp_low12)` BE: disp=0xBF0=3056 — way too big
  - `(len_low4, disp_high12)` either endian: same problem
  - LZ11 3-byte extended-length form: `0xEB` high nibble = 0xE, not the 0/1 special codes
- Hypothesis: the "REFs" are a Grezzo-specific "output N zero bytes" token, or the encoding
  splits bits at a boundary that doesn't align with byte edges. Static reversing the actual
  decoder is required to resolve this — see `lzs_hunt.md`.

## Related archive formats
- **GAR2** (raw): sibling `.gar.lzs` files (magic `GAR\2`) — parsed by
  `soh3d/Shipwright/cmb3d/asset/gar.cpp`.
- **ZAR** (OoT3D): older Grezzo archive format used by OoT3D, structurally similar to GAR2
  but with a smaller 0x18 header.
