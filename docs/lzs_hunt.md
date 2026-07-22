# Grezzo LzS decompressor — hunt log — SOLVED (2026-07-02)

**Resolution**: found via web search. `xdanieldzd/Scarlet.IO.CompressionFormats/GrezzoLZS.cs`
has the exact algorithm. See `docs/formats/lzs.md` for the format, and
`Shipwright/cmb3d/asset/lzs.{h,cpp}` (in the superproject) for the port. Verified against real MM3D
archives (`zelda2_boj` 148907 → 217088 bytes, `zelda2_box` 90642 → 135200 bytes, both
producing valid GAR2 headers).

The key insight we were missing: the 4096-byte ring dictionary is initialized to `0x00`
and `writeidx` starts at `0xFEE`. That's why the second control block's back-references
emit `00 00 00`s — they're copying from the still-zero dictionary region.

## Dead ends (kept for the record)

- **Search u32 literal `0x01537A4C` ("LzS\1" LE)** — 0 hits. Magic isn't stored as u32.
- **Search byte-wise pattern `4C 7A 53 01`** — 0 hits (not stored contiguously).
- **MOVW/MOVT hunt for 0x01537A4C or 0x02524147** — **0 MOVW instructions in the entire
  binary**. Grezzo's compiler emits all 32-bit constants through the ARM literal pool
  (`ldr r0, [pc, ...]`), not MOVW/MOVT — so ARM11 32-bit constant loads look identical
  to a plain load. Since the raw u32 bytes also aren't present, the LzS magic must not
  be compared as a 4-byte word at all — the decoder is called by filename dispatch, not
  header validation.
- **CMP-with-imm hunt for the L/z/S/\1 bytes near each other** — 2 finalists, both were
  printf format-specifier parsers (`%L`/`%z`/`%S`), not header checks.
- **`.gar.lzs` string-caller trace** (Ghidra call-graph BFS depth 5 from the 2 direct
  callers of hardcoded `.gar.lzs` paths) — only 4 candidates surfaced, none were LZ77-shaped.
  The archive-open path (`FUN_0020abec`) just allocates a descriptor and records the
  filename; the actual read + decompress happens later on demand, from code not reachable
  via that call graph.
- **Body-heuristic LZ77 scan** over all 13598 functions — top candidates were 3DS texture
  format converters and CMB attribute unpackers (byte-oriented loops matching the LDRB+STRB
  fingerprint but no LZ77 semantics). Kept CSV at `scratch/mm3d-decomp/build/mm3d_lz77_bodyheur.csv`.

The static-reversing route was viable but slow; the Scarlet lookup made it moot.

## What was already known from samples

Reversed from `/actors/zelda2_box.gar.lzs` and 3 other archives (see `docs/formats/lzs.md`
for the header layout):
- Header 16 bytes: `LzS\1` (4B) + `01 00 XX XX` unknown u16+u16 + decompressed_size (LE u32) +
  compressed_size (LE u32).
- Compressed stream starts at byte 16.
- First control byte is `0xFF` = "8 literal bytes follow" — confirmed by output matching the
  GAR2 header start (`GAR\2` + fileSize).
- Second control byte is `0x5F` = `0101_1111` binary. LSB-first bit reading with `bit=1 =
  literal` matches the second half of the GAR2 header (nTypes/nFiles/typesOff low byte).

The unresolved-until-now piece was the encoding of the two back-refs in the 5F block
(2 stream bytes each producing 3 output bytes of `00 00 00`). The answer: standard 12-bit
displacement / 4-bit (length-3) split, but read against a **zero-initialized** ring buffer
so the copy produces zeros regardless of the exact displacement.

## Tooling in this repo (still useful as templates for other formats)

- `tools/extract_code.py` — decrypt-and-decompress `.code` from a .3ds.
- `tools/DumpFunctions.py` — Ghidra headless: full function inventory CSV.
- `tools/HuntLzS.py`, `HuntLzS2.py` — magic-byte candidates (no hits, kept for reference).
- `tools/HuntArchiveOpener.py` — locate the actor-archive loader.
- `tools/BodyHeuristicLZ77.py` — score every function for LZ77-shaped byte-copy loops.
- `tools/DumpDecomp.py` — decompile specific VAs (comma list in DECOMP_TARGETS env).

All Ghidra scripts run headless via
`/opt/ghidra_11.0.3_PUBLIC/support/analyzeHeadless <project> mm3d -process mm3d.code
  -noanalysis -scriptPath <dir> -postScript <Script>.py`.
