# -*- coding: utf-8 -*-
#@runtime Jython
# Attribute MM3D functions to their ORIGINAL source files, from the engine's own assert strings.
#
# WHY THIS EXISTS: MM3D ships without symbols, and every recovered function is `FUN_<addr>`, which
# is not readable C++. But the engine's asserts embed absolute paths built by the original build:
#
#     C:\Jenkins\workspace\joker\prog\game\sources\original\z_kankyo.cpp(2070)
#
# A function that references such a string is, by the developers' own construction, defined in
# that source file. That is ground truth -- it is not a guess and not a fingerprint match -- and it
# is how the "well organized" module structure of the image can be recovered at all.
#
# TWO BUGS THIS FILE EXISTS TO NOT REINTRODUCE, both of which made the first version report a
# clean, confident, and completely vacuous ZERO hits on strings that are provably in the image:
#
#  1. `mem.getBytes(addr, bytearray(n))` does NOT fill the caller's Python bytearray. Jython
#     coerces it into a Java byte[] COPY, Ghidra fills the copy, and the caller's buffer stays
#     zeroed -- so every subsequent `.find()` returns -1 forever. The correct idiom is
#     `jarray.zeros(n, "b")`, which allocates a real Java array the fill can land in.
#  2. The program is loaded at image base 0x00100000, so a file offset is NOT a virtual address.
#     A buffer index must be reported as `block_start + index`. Reading a file offset directly
#     lands mid-instruction and returns one meaningless byte.
#
# Env:
#   MM3D_STR_SUBSTR  comma-separated substrings to require (default: none = all .cpp paths)
#   MM3D_STR_OUT     output CSV path (default: <repo>/mm3d-decomp/build/decomp/source_files.csv)
import os
import re
import jarray

prog = currentProgram
fm = prog.getFunctionManager()
rm = prog.getReferenceManager()
mem = prog.getMemory()
af = prog.getAddressFactory().getDefaultAddressSpace()

def _default_out():
    # Walk up from the script looking for the checkout root, rather than guessing at a relative
    # path from the CWD: Ghidra headless runs the script with the CWD somewhere else entirely, and
    # the first version of this resolved to a path OUTSIDE the repository and wrote there.
    here = os.path.abspath(os.getcwd())
    for _ in range(6):
        if os.path.isdir(os.path.join(here, "mm3d-decomp", "build", "decomp")):
            return os.path.join(here, "mm3d-decomp", "build", "decomp", "source_files.csv")
        parent = os.path.dirname(here)
        if parent == here:
            break
        here = parent
    raise RuntimeError("cannot locate the zelda3d checkout; set MM3D_STR_OUT explicitly")


out_path = os.environ.get("MM3D_STR_OUT") or _default_out()

blocks = [b for b in mem.getBlocks() if b.isInitialized()]
print("blocks: %d" % len(blocks))
if not blocks:
    print("NO INITIALIZED MEMORY -- refusing to report zero matches")
    raise SystemExit(1)

# `...original\z_kankyo.cpp(2070)` -- capture the file name and the line.
PATTERN = re.compile(r"([A-Za-z_][A-Za-z_0-9]*\.cpp)\((\d+)\)")

required = [s.strip().lower() for s in os.environ.get("MM3D_STR_SUBSTR", "").split(",") if s.strip()]

rows = []
scanned = 0
for blk in blocks:
    start = blk.getStart().getOffset()
    n = int(blk.getSize())
    buf = jarray.zeros(n, "b")
    mem.getBytes(blk.getStart(), buf)
    # Searching bytes-as-text: a Python str of the whole image is the reliable way to do a
    # substring search, because jarray itself is not str-indexable.
    text = "".join([chr(buf[i] & 0xFF) for i in range(n)])
    scanned += len(text)
    print("BLOCK %s 0x%08x size=%d" % (blk.getName(), start, n))

    # A path is contiguous, so scan for the first component and walk forward over the run.
    for m in re.finditer(r"([A-Za-z_][A-Za-z_0-9]*\.cpp)\((\d+)\)", text):
        whole = m.group(0)
        name = m.group(1)
        line = int(m.group(2))
        # Extend backwards to recover the full original path for provenance.
        back = m.start()
        while back > 0 and text[back - 1] not in ("\x00", "\n") and ord(text[back - 1]) >= 32:
            back -= 1
        path = text[back:m.end()].strip()
        # The walk-back can pick up non-ASCII bytes from adjacent image data, which makes the CSV
        # unreadable as UTF-8. Keep printable ASCII only; the filename and line are what matter and
        # they are already captured separately.
        path = "".join([c if 32 <= ord(c) < 127 else " " for c in path]).strip()
        if required and not any(s in whole.lower() for s in required):
            continue
        # index in the block -> VIRTUAL address, which is what functions.csv uses.
        va = start + m.start()
        refs = []
        try:
            a = af.getAddress(va)
        except Exception:
            a = None
        if a is not None:
            for r in rm.getReferencesTo(a):
                f = fm.getFunctionContaining(r.getFromAddress())
                refs.append((r.getFromAddress().getOffset(), f.getName() if f else "?",
                             f.getEntryPoint().getOffset() if f else 0))
        rows.append((va, name, line, path, refs))

directory = os.path.dirname(out_path)
if not os.path.isdir(directory):
    os.makedirs(directory)
with open(out_path, "w") as fp:
    fp.write("string_va,source_file,line,full_path,n_refs,ref_function,ref_fn_entry\n")
    for va, name, line, path, refs in rows:
        for (rva, rname, entry) in refs:
            fp.write("0x%08x,%s,%d,%s,%d,%s,0x%08x\n"
                     % (va, name, line, path.replace(",", ";"), len(refs), rname, entry))
        if not refs:
            # A string with no code reference is real evidence but attributes no function; it is
            # still written out, marked with n_refs 0, rather than silently dropped.
            fp.write("0x%08x,%s,%d,%s,0,,\n" % (va, name, line, path.replace(",", ";")))

print("scanned %d chars, matched %d source-path strings" % (scanned, len(rows)))
print("wrote %s" % out_path)

# CONTROL: the tool must be able to find a string it was just shown exists. Report the distinct
# file count so a silent regression to zero is obvious rather than plausible.
distinct = sorted(set(r[1] for r in rows))
print("distinct source files: %d" % len(distinct))
if not rows:
    print("CONTROL FAILED: no source-path strings found in a %d-char image" % scanned)
else:
    print("CONTROL OK: %d distinct files, e.g. %s" % (len(distinct), ", ".join(distinct[:5])))
