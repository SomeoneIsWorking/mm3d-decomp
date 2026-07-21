#!/usr/bin/env python3
"""extract_code.py — pull the executable .code out of a decrypted MM3D .3ds and
decompress it to a flat, load-address-correct binary for static disassembly.

Same algorithm oot3d-decomp uses (Nintendo backward-LZSS "BLZ", CUE's decoder ported
line-for-line). The 3DS NCCH ExeFS holds a ".code" file; MM3D's ExHeader SCI compress
flag is set, so we unpack it here.

Output: mm3d.code = the full code image (text+rodata+data) as it sits in memory. First
byte maps to the .text load address (0x00100000 for MM3D — verified).

Verify: `objdump -b binary -m arm --adjust-vma=0x00100000 mm3d.code` should show
sane ARM disassembly at the entry point.

No crypto here — decrypted dumps only.
"""
import argparse, os, struct, sys

# Reuse the soh3d NCCH/ExeFS parser (locates exefs/exheader offsets).
# Resolve the engine tools dir (ctr_romfs.py) WITHOUT a machine-specific path: mm3d-decomp is
# vendored as a submodule of the zelda3d engine repo, so tools/ sits two levels up. ZELDA3D_TOOLS
# overrides for a standalone checkout.
SOH3D_TOOLS = os.environ.get(
    "ZELDA3D_TOOLS",
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "tools"))
if not os.path.isdir(SOH3D_TOOLS):
    sys.exit("engine tools dir not found: %s (set ZELDA3D_TOOLS)" % SOH3D_TOOLS)
sys.path.insert(0, SOH3D_TOOLS)
import ctr_romfs as C


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def blz_decompress(data: bytes) -> bytes:
    """Nintendo backward-LZSS (BLZ) used for 3DS ExeFS .code. Port of CUE's BLZ_Decode.

    Footer (last 8 bytes):
      u24 enc_len   size of the compressed region (low 24 bits of u32 @ end-8)
      u8  hdr_len   bytes of footer to skip (@ end-5)
      u32 inc_len   extra length to add for the decompressed size (@ end-4)

    Decoding runs from the end backward. Each flag bit: set => (len, disp) backref;
    clear => literal.
    """
    pak_len = len(data)
    inc_len = u32(data, pak_len - 4)
    if inc_len == 0:
        # not actually compressed; strip footer and return
        enc_len = u32(data, pak_len - 8)
        return bytes(data[: pak_len - enc_len])
    hdr_len = data[pak_len - 5]
    enc_len = u32(data, pak_len - 8) & 0x00FFFFFF
    dec_len = pak_len + inc_len

    buf = bytearray(data) + bytearray(inc_len)
    raw_len = pak_len - enc_len
    pak = raw_len + enc_len - hdr_len
    out = dec_len
    raw_end = raw_len

    mask = 0
    flags = 0
    while out > raw_end:
        mask >>= 1
        if mask == 0:
            pak -= 1
            flags = buf[pak]
            mask = 0x80
        if flags & mask:
            pak -= 1
            b1 = buf[pak]
            pak -= 1
            b2 = buf[pak]
            length = (b1 >> 4) + 3
            disp = (((b1 & 0x0F) << 8) | b2) + 3
            for _ in range(length):
                out -= 1
                buf[out] = buf[out + disp]
        else:
            pak -= 1
            out -= 1
            buf[out] = buf[pak]
    return bytes(buf[:dec_len])


def get_code(rom_path: str):
    rom = C.CtrRom(rom_path)
    f = rom.fp
    # ExHeader -> .text load address + compress flag
    f.seek(rom.ncch_off + 0x200)
    exh = f.read(0x400)
    text_addr = u32(exh, 0x10)
    sci_flag = exh[0x0D]
    # ExeFS header: 10 entries of {name[8], off u32, size u32}; data at exefs_off+0x200
    f.seek(rom.exefs_off)
    ex = f.read(0x200)
    code_off = code_size = None
    for i in range(10):
        nm = ex[i * 16:i * 16 + 8].split(b"\x00")[0].decode("latin1")
        if nm == ".code":
            code_off = u32(ex, i * 16 + 8)
            code_size = u32(ex, i * 16 + 12)
            break
    if code_off is None:
        raise SystemExit(".code not found in ExeFS")
    f.seek(rom.exefs_off + 0x200 + code_off)
    raw = f.read(code_size)
    if sci_flag & 1:
        code = blz_decompress(raw)
    else:
        code = raw
    return text_addr, code, len(raw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", help="decrypted MM3D .3ds")
    ap.add_argument("out", nargs="?", default="mm3d.code")
    args = ap.parse_args()
    text_addr, code, raw_sz = get_code(args.rom)
    with open(args.out, "wb") as f:
        f.write(code)
    text_size = (u32(code, 0) if False else len(code))  # simple; text_size not needed for disasm
    print(f".text load addr 0x{text_addr:08x}  decompressed code 0x{len(code):x} bytes  (raw 0x{raw_sz:x})")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
