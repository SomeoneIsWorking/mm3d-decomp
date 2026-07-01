# -*- coding: utf-8 -*-
# Ghidra headless script: dump function inventory + hunt for the LzS decompressor.
#
# LzS decompressor signature we're looking for:
#   * Function that reads 4 bytes and compares to "LzS\1" (0x01537A4C LE) OR is called
#     by such a function.
#   * Small function body (typically 50-200 instructions for a bit-stream LZ77 decoder).
#   * References the string "LzS\0" at VA 0x00646f84.
#
# Output:
#   - build/decomp/mm3d_functions.csv — every recognized function
#   - build/decomp/mm3d_lzs_candidates.csv — functions that reference "LzS\0" or the magic
#
# Run:
#   analyzeHeadless scratch/mm3d-decomp/ghidra mm3d -process mm3d.code -noanalysis \
#     -scriptPath scratch/mm3d-decomp -postScript DumpFunctions.py
import os
from ghidra.util.task import ConsoleTaskMonitor

OUT = "<SOH3D_REPO>/scratch/mm3d-decomp/build"
if not os.path.isdir(OUT):
    os.makedirs(OUT)

fm = currentProgram.getFunctionManager()
listing = currentProgram.getListing()
af = currentProgram.getAddressFactory().getDefaultAddressSpace()

# 1. Function inventory.
inv = []
for f in fm.getFunctions(True):
    a = f.getEntryPoint()
    sz = 0
    try:
        sz = int(f.getBody().getNumAddresses())
    except:
        pass
    inv.append((int(a.getOffset()), sz, f.getName()))
inv.sort()
with open(os.path.join(OUT, "mm3d_functions.csv"), "w") as fp:
    fp.write("addr,size,name\n")
    for a, sz, n in inv:
        fp.write("0x%08x,%d,%s\n" % (a, sz, n))
print("wrote mm3d_functions.csv (%d funcs)" % len(inv))

# 2. Find xrefs to VA 0x00646f84 (the "LzS\0" label).
tgt = af.getAddress(0x00646f84)
refs = list(currentProgram.getReferenceManager().getReferencesTo(tgt))
print("xrefs to LzS label: %d" % len(refs))
lzs_funcs = set()
for r in refs:
    from_a = r.getFromAddress()
    f = fm.getFunctionContaining(from_a)
    if f:
        lzs_funcs.add(f)
        print("  xref from 0x%x in fn %s @ 0x%x" %
              (from_a.getOffset(), f.getName(), f.getEntryPoint().getOffset()))

# 3. Scan every function for a 4-byte literal-pool entry equal to 0x01537A4C ("LzS\1" LE)
#    OR the byte-wise CMP with 'L' followed by 'z' (0x4C, 0x7A) as immediates. Both signatures
#    identify the LzS header check.
MAGIC_LE = 0x01537A4C
MAGIC_BYTES = [0x4C, 0x7A, 0x53, 0x01]
magic_candidates = []
for f in fm.getFunctions(True):
    body = f.getBody()
    it = listing.getInstructions(body, True)
    saw_L = saw_z = False
    saw_ref = False
    for ins in it:
        # Scan immediate operand of CMP against magic bytes
        for i in range(ins.getNumOperands()):
            for o in ins.getOpObjects(i):
                try:
                    v = int(o.getValue())
                except:
                    continue
                if v == 0x4C: saw_L = True
                if v == 0x7A: saw_z = True
                if v == MAGIC_LE:
                    saw_ref = True
        # LDR from literal pool: check refs to nearby data equal to MAGIC_LE
        for ref in ins.getReferencesFrom():
            to = ref.getToAddress()
            if to and int(to.getOffset()) == MAGIC_LE:
                saw_ref = True
    if saw_ref or (saw_L and saw_z):
        magic_candidates.append((f.getEntryPoint().getOffset(), f.getName(), saw_L, saw_z, saw_ref))

# Also seed with any function that xrefs the "LzS\0" label.
label_funcs = set()
for f in lzs_funcs:
    label_funcs.add((f.getEntryPoint().getOffset(), f.getName()))

with open(os.path.join(OUT, "mm3d_lzs_candidates.csv"), "w") as fp:
    fp.write("addr,name,cmp_L,cmp_z,literal_ref,xref_LzS_label\n")
    seen = set()
    for a, n, l, z, ref in magic_candidates:
        fp.write("0x%08x,%s,%d,%d,%d,%d\n" % (a, n, int(l), int(z), int(ref),
                                              int((a, n) in label_funcs)))
        seen.add((a, n))
    for a, n in label_funcs:
        if (a, n) not in seen:
            fp.write("0x%08x,%s,0,0,0,1\n" % (a, n))
print("wrote mm3d_lzs_candidates.csv (%d)" % (len(magic_candidates) + len(label_funcs - seen)))
