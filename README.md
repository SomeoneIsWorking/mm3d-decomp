# mm3d-decomp

Reverse-engineering / decompilation lab for **The Legend of Zelda: Majora's Mask 3D** (Nintendo 3DS,
product code `CTR-P-AJRE`). Sibling of [`oot3d-decomp`](../oot3d-decomp): same tooling shape, same
philosophy — recover MM3D's structures and behavior as ground truth so [`soh3d`](../soh3d)'s Zelda3D
engine can render MM using OoT3D-style assets instead of guessing from N64 MM (2S2H).

MM3D has **no public decompilation or symbols**. Everything here is derived empirically:
- **Static RE** of the decompressed ARM executable (`.code`) and of the RomFS assets (`.gar.lzs`,
  `.zsi`, `.cmb`, `.csab`). See `tools/extract_code.py`, `docs/formats/`.
- **Live RE** by driving MM3D in a modded Azahar (same oracle scaffolding oot3d-decomp uses —
  RAM read/write, screenshot, injected input); tooling migrates from soh3d as it matures.

## Immediate need: **Grezzo LzS (`LzS\x01`) decompressor**

Most of MM3D's `/actors/zelda2_*.gar.lzs` archives are actually raw GAR2 (uncompressed) — but a
significant subset (box, tsubo, obj_tokeidai, tree, milk_bin, ...) are wrapped in Grezzo's own LzS
container. `soh3d`'s Zelda3D_LookupModel currently rejects those at map-time so the caller falls
back to the vanilla N64 draw. First goal here: **find the LzS decompression function in `.code`,
port its exact semantics to C++**, then land the decompressor in `soh3d/Shipwright/cmb3d/`.

Sample-driven reverse fails: the first control byte 0xFF acts as "8 literals" (verified — produces
"GAR\\2" + fileSize) and the second control byte 0x5F reads 6 literals + 2 refs producing an output
window that matches the expected GAR2 header (nTypes / nFiles / typesOff low byte), but the ref
encoding (2 bytes each producing 3 output bytes of `00 00 00`) doesn't fit any standard 3DS LZ
variant (LZ11, plain LZ77 either bit-1-lit or bit-1-ref). The refs must be RLE-style or use a
Grezzo-specific bit split — reversing the function is the tractable route.

## Status
Bootstrap. `scratch/` holds the decompressed `.code`. Next: load into Ghidra headless, find LzS by
scanning for the "LzS\\1" magic constant, decompile the callers, extract the algorithm.

## Relationship to soh3d / oot3d-decomp
Same conventions:
- Copyrighted assets (`.3ds`, `.z64`) NEVER committed — provided via env vars in `soh3d/.env`
  (`ZELDA3D_MM3D_ROM`, `ZELDA3D_MM_ROM`).
- Tooling that's genuinely shared with oot3d-decomp stays there; MM3D-specific work lives here.
