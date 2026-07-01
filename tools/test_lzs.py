#!/usr/bin/env python3
# Port of Scarlet's GrezzoLZS decoder — reference implementation for the C++ port.
# Validate against a real MM3D archive.
import os, sys, struct

def grezzo_lzs_decompress(compressed: bytes, expected_uncompressed_size: int) -> bytes:
    BUFFER = bytearray(4096)   # ring dictionary, initialized to 0
    writeidx = 0xFEE
    readidx = 0
    fidx = 0
    outdata = bytearray()

    N = len(compressed)
    while fidx < N:
        flags8 = compressed[fidx]; fidx += 1
        for _ in range(8):
            if fidx >= N: break
            if flags8 & 1:
                # literal
                b = compressed[fidx]; fidx += 1
                outdata.append(b)
                BUFFER[writeidx] = b
                writeidx = (writeidx + 1) & 0xFFF
            else:
                # back-ref: 2 bytes
                if fidx + 1 >= N: break
                b1 = compressed[fidx]; fidx += 1
                b2 = compressed[fidx]; fidx += 1
                readidx = b1 | ((b2 & 0xF0) << 4)
                match_len = (b2 & 0x0F) + 3
                for _ in range(match_len):
                    v = BUFFER[readidx]
                    outdata.append(v)
                    BUFFER[writeidx] = v
                    readidx = (readidx + 1) & 0xFFF
                    writeidx = (writeidx + 1) & 0xFFF
            flags8 >>= 1
    if len(outdata) != expected_uncompressed_size:
        raise SystemExit(f"size mismatch: got {len(outdata)}, expected {expected_uncompressed_size}")
    return bytes(outdata)


def decompress_file(path):
    data = open(path, "rb").read()
    if data[:4] != b"LzS\x01":
        raise SystemExit(f"not LzS: magic={data[:4]!r}")
    _, flags1, flags2, dec_size, comp_size = struct.unpack("<4sHHII", data[:16])
    body = data[16:16+comp_size]
    print(f"header: dec_size={dec_size} comp_size={comp_size} flags2=0x{flags2:04x} body_len={len(body)}")
    out = grezzo_lzs_decompress(body, dec_size)
    print(f"decompressed OK, first 32 bytes: {out[:32].hex()}")
    if out[:4] == b"GAR\x02":
        # Header sanity
        _, total, nTypes, nFiles, typesOff, filesOff, dataOff = struct.unpack("<4sIHHIII", out[:24])
        print(f"GAR2: total=0x{total:x} nTypes={nTypes} nFiles={nFiles} typesOff=0x{typesOff:x} filesOff=0x{filesOff:x} dataOff=0x{dataOff:x}")
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: test_lzs.py <path-to-lzs-file>")
        sys.exit(1)
    out = decompress_file(sys.argv[1])
    if len(sys.argv) > 2:
        with open(sys.argv[2], "wb") as f:
            f.write(out)
        print(f"wrote {sys.argv[2]} ({len(out)} bytes)")
