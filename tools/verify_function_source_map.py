#!/usr/bin/env python3
"""Independently re-check mm3d-decomp/build/decomp/function_source_map.csv against the raw image.

FunctionSourceMap.py is a Ghidra script; a Ghidra script grading its own output proves nothing.
This checker shares no code with it. It re-derives every claim from the raw executable bytes with a
hand-written ARM/Thumb decoder and a live dump of Ghidra's function map:

  * the word at `pool=` really is the string address, and the bytes there really contain
    `...\\<source_file>(<line>)`;
  * the instruction at `@` really is inside the function the row names (innermost container);
  * `confidence` agrees with the evidence (`pooled` when the address is a word, `direct` when it is
    the string's own first byte);
  * for every row whose address came from a PC-relative literal -- the majority -- the instruction
    really is that literal load. Rows whose address came from a register chain cannot be re-derived
    by a decoder that models one instruction, and are reported as chain-derived rather than counted
    as verified.

Inputs (override with argv):
  1. the CSV              mm3d-decomp/build/decomp/function_source_map.csv
  2. the raw executable   scratch/mm3d_layout/mm3d.code   (md5 642437817cee4a6ee73c4518fd1fe71f)
  3. Ghidra's function map, dumped by DumpFnMap.py in scratch/mm3d_attr/ghidra

Exit status is 1 if any row fails. Usage:
    python3 mm3d-decomp/tools/verify_function_source_map.py
"""
import bisect
import csv
import hashlib
import os
import re
import struct
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_CSV = os.path.join(REPO, "mm3d-decomp/build/decomp/function_source_map.csv")
DEFAULT_IMAGE = os.path.join(REPO, "scratch/mm3d_layout/mm3d.code")
DEFAULT_FNMAP = os.path.join(REPO, "scratch/mm3d_attr/fnmap.csv")
IMAGE_BASE = 0x00100000
IMAGE_MD5 = "642437817cee4a6ee73c4518fd1fe71f"


def load_functions(path):
    rows = []
    with open(path) as f:
        r = csv.reader(f)
        next(r)
        for entry, lo, hi, name in r:
            rows.append((int(entry, 16), int(lo, 16), int(hi, 16), name))
    rows.sort()
    return rows


class Containing(object):
    """Innermost function containing an address.

    Ghidra bodies overlap here: FUN_003c8200 spans 0x3c8200-0x4f91cf and FUN_004f0324 spans
    0x4f0324-0x50f2cf. Scanning back for the highest entry that still covers the address gives the
    innermost one; `FunctionManager.getFunctionContaining` answers with the outer one for these.
    """

    def __init__(self, rows):
        self.rows = rows
        self.entries = [t[0] for t in rows]
        self.span = max([hi - lo for _, lo, hi, _ in rows] + [1])

    def name_at(self, va):
        i = bisect.bisect_right(self.entries, va) - 1
        while i >= 0 and self.entries[i] >= va - self.span:
            entry, lo, hi, name = self.rows[i]
            if entry <= va <= hi:
                return name
            i -= 1
        return None


def pc_relative_targets(data, insn_va):
    """Addresses a PC-relative word LOAD at insn_va names, decoded straight from the bytes."""
    out = []
    off = insn_va - IMAGE_BASE
    word = struct.unpack_from("<I", data, off)[0]
    if (((word >> 26) & 3) == 1 and ((word >> 25) & 1) == 0 and ((word >> 4) & 1) == 0
            and ((word >> 24) & 1) == 1                       # pre-indexed
            and ((word >> 22) & 1) == 0                       # word, not byte
            and ((word >> 21) & 1) == 0                       # no writeback
            and ((word >> 20) & 1) == 1                       # load
            and ((word >> 16) & 15) == 15 and ((word >> 12) & 15) != 15):
        imm = word & 0xFFF
        out.append(((insn_va + 8) & ~3) + (imm if ((word >> 23) & 1) else -imm))
    half = struct.unpack_from("<H", data, off)[0]             # Thumb LDR Rt,[pc,#imm8*4]
    if (half >> 11) == 0b01001:
        out.append(((insn_va + 4) & ~3) + (half & 0xFF) * 4)
    return out


EVIDENCE = re.compile(r"(.+?) @(0x?[0-9a-f]+) (direct|pooled) pool=(0x[0-9a-f]+) str=(0x[0-9a-f]+) "
                      r"(pool-in-fn|pool-outside-fn)$")


def main(argv):
    csv_path = argv[1] if len(argv) > 1 else DEFAULT_CSV
    image_path = argv[2] if len(argv) > 2 else DEFAULT_IMAGE
    fnmap_path = argv[3] if len(argv) > 3 else DEFAULT_FNMAP
    for path, what in ((csv_path, "attribution CSV"), (image_path, "executable image"),
                       (fnmap_path, "Ghidra function map")):
        if not os.path.isfile(path):
            print("MISSING INPUT: the %s (%s). Refusing to report a vacuous pass." % (what, path))
            return 2
    with open(image_path, "rb") as f:
        data = f.read()
    digest = hashlib.md5(data).hexdigest()
    if digest != IMAGE_MD5:
        print("WRONG IMAGE: %s is %s, expected %s" % (image_path, digest, IMAGE_MD5))
        return 2
    print("image %s md5 %s, %d bytes, base 0x%08x" % (image_path, digest, len(data), IMAGE_BASE))
    containing = Containing(load_functions(fnmap_path))
    print("function map: %d functions" % len(containing.rows))

    literal_ok = chain_rows = bad = total = 0
    failures = []
    with open(csv_path) as f:
        r = csv.reader(f)
        next(r)
        for row in r:
            total += 1
            problems = []
            literal = False
            if len(row) != 6:
                problems.append("row has %d columns, expected 6" % len(row))
                bad += 1
                failures.append((row[0] if row else "?", problems))
                continue
            entry, name, sfile, line_s, conf, ev = row
            try:
                entry = int(entry, 16)
                line = int(line_s)
            except ValueError:
                problems.append("unparsable entry/line columns %r/%r" % (entry, line_s))
            m = EVIDENCE.match(ev) if not problems else None
            if m is None:
                problems.append("unparsable evidence %r" % ev)
            else:
                insn = int(m.group(2), 16)
                pool = int(m.group(4), 16)
                strva = int(m.group(5), 16)
                if containing.name_at(insn) != name:
                    problems.append("instruction 0x%08x is inside %s, not %s"
                                    % (insn, containing.name_at(insn), name))
                if struct.unpack_from("<I", data, pool - IMAGE_BASE)[0] != strva:
                    problems.append("the word at pool=0x%08x is not the string address" % pool)
                if not IMAGE_BASE <= strva < IMAGE_BASE + len(data):
                    problems.append("str=0x%08x is outside the image" % strva)
                else:
                    text = data[strva - IMAGE_BASE:strva - IMAGE_BASE + 96]
                    want = (rb"[\x20-\x7e]{0,140}?" + sfile.encode() + rb"\("
                            + str(line).encode() + rb"\)")
                    if not re.match(want, text):
                        problems.append("the string at str= does not contain %s(%d)" % (sfile, line))
                if conf not in ("direct", "pooled"):
                    problems.append("unknown confidence %r" % conf)
                elif (conf == "pooled") != (pool != strva):
                    problems.append("confidence does not match the evidence")
                literal = pool in pc_relative_targets(data, insn)
                chain_rows += 0 if literal else 1
            if problems:
                bad += 1
                failures.append((name, problems))
            elif literal:
                literal_ok += 1
    print("rows: %d | %d re-derived from raw bytes | %d chain-derived (not re-derivable by a "
          "PC-relative decoder) | %d FAILED" % (total, literal_ok, chain_rows, bad))
    for name, problems in failures[:20]:
        print("  FAIL %s: %s" % (name, "; ".join(problems)))
    if total == 0:
        print("CONTROL FAILED: the CSV has no rows; a pass here would be vacuous")
        return 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
