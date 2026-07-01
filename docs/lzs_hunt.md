# Grezzo LzS decompressor — hunt log

Goal: locate MM3D's Grezzo LzS (`LzS\1`) decoder in `.code`, decompile it, port to C++
for `soh3d/Shipwright/cmb3d/`.

## What we know from samples alone
Reversed from `/actors/zelda2_box.gar.lzs` and 3 other archives (see
`docs/formats/lzs.md` for the header layout):
- Header 16 bytes: `LzS\1` (4B) + `01 00 XX XX` unknown u16+u16 + decompressed_size (LE u32) +
  compressed_size (LE u32).
- Compressed stream starts at byte 16.
- First control byte is `0xFF` = "8 literal bytes follow" — confirmed by output matching the
  GAR2 header start (`GAR\2` + fileSize LE).
- Second control byte is `0x5F` = `0101_1111` binary. LSB-first bit reading with `bit=1 =
  literal` matches the second half of the GAR2 header (nTypes/nFiles/typesOff low byte).
- **Blocker:** the two "back-refs" in that same block (2 stream bytes each, producing 3 output
  bytes of `00 00 00` each) don't fit any standard 3DS/NDS LZ variant (LZ11, plain LZ77,
  either bit-1-lit or bit-1-ref). They may be RLE-style zero-tokens, or the encoding uses a
  Grezzo-specific bit split — needs the actual decoder to disambiguate.

## Ghidra hunt (current state)
Decompressed `.code` loaded at VA `0x00100000` (script: `tools/extract_code.py`, base image
`scratch/mm3d.code`, 5.97 MB, 13598 functions). Auto-analysis complete.

**Tried:**
- Search u32 literal `0x01537A4C` ("LzS\1" LE) — 0 hits. Magic is probably compared byte-wise.
- Search byte-wise pattern `4C 7A 53 01` — 0 hits (not stored contiguously).
- Search functions with CMP-immediate against 'L' (0x4C) then 'z' (0x7A) — 33 candidates,
  narrowed by requiring `>=3` of `{L,z,S,\1}` within 48 bytes: 2 finalists (`FUN_00101714`,
  `FUN_002ff7a0`) — decompiled both, both are **printf-family format parsers** (the L/z/S
  bytes are `%L` / `%z` / `%S` format specifiers, not the magic).
- Search u32 literals pointing into the `zelda2_XXX` string table at VA `0x00692818` — 0
  hits. The table is accessed indirectly.
- Search u32 literal `0x00692818` (table base) — 0 hits. Suggests the table pointer is loaded
  via MOVW+MOVT (32-bit constant load, not literal-pool).

**Next candidates:**
- Scan for MOVW+MOVT sequences constructing `0x00692818` (table base) or `0x01537A4C` (magic).
  ARM lets you MOVW low16 + MOVT high16 without a literal pool. Ghidra's "constant analyzer"
  may have resolved these but the u32 doesn't appear as raw bytes.
- Body-heuristic search: LZ77 decoders have very tight loops with byte-copy from output
  buffer indexed by a computed displacement. Search functions with (a) small body (<300
  instructions), (b) a byte-load+byte-store pair whose store address is (`out - imm`), and
  (c) either a shift-by-4 or mask-with-0xFFF (12-bit displacement) or 0xF (nibble length).

## Tooling in this repo
- `tools/extract_code.py` — decrypt-and-decompress `.code` from a .3ds.
- `tools/DumpFunctions.py` — Ghidra headless: full function inventory CSV.
- `tools/HuntLzS.py`, `HuntLzS2.py` — magic-byte candidates.
- `tools/HuntArchiveOpener.py` — locate the actor-archive loader.
- `tools/DumpDecomp.py` — decompile specific VAs (comma list in DECOMP_TARGETS env).
- `tools/Blocks.py` — memory-block sanity check.

All Ghidra scripts run headless via
`/opt/ghidra_11.0.3_PUBLIC/support/analyzeHeadless <project> mm3d -process mm3d.code
  -noanalysis -scriptPath <dir> -postScript <Script>.py`.
