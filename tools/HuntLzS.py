# -*- coding: utf-8 -*-
# Hunt for the LzS decompressor by looking for calls whose immediate arg near a load
# is the LzS magic. In ARM the 4-byte magic 0x01537A4C is normally loaded from a
# literal pool via LDR PC-relative. So we scan every constant pool entry:
#   - if a u32 word in the analyzed program == 0x01537A4C, note it
#   - report every LDR that loads that address
#
# We also scan for LDR patterns that dereference a magic byte comparison sequence:
#   LDRB Rn, [Rx]  ; CMP Rn, #'L'  ; then further compares with #'z' 'S' 0x01.
import os
from ghidra.util.task import ConsoleTaskMonitor

# Output dir: $MM3D_DECOMP_OUT, else <repo>/build via $ZELDA3D_REPO.
def _out_dir(sub=""):
    o = os.environ.get("MM3D_DECOMP_OUT")
    if not o:
        repo = os.environ.get("ZELDA3D_REPO")
        if not repo:
            raise RuntimeError("set MM3D_DECOMP_OUT, or ZELDA3D_REPO to the zelda3d checkout")
        o = os.path.join(repo, "mm3d-decomp", "build" + sub)
    if not os.path.isdir(o):
        os.makedirs(o)
    return o

OUT = _out_dir('')

listing = currentProgram.getListing()
memory = currentProgram.getMemory()
af = currentProgram.getAddressFactory().getDefaultAddressSpace()
fm = currentProgram.getFunctionManager()

MAGIC = 0x01537A4C

# 1. Sweep all defined 4-byte words for the magic.
magic_words = []
addr = memory.getMinAddress()
end = memory.getMaxAddress()
step = 4
cur = addr.getOffset()
end_off = end.getOffset()
# Only look in the file's actual range (avoid Ghidra reading past mapped data).
# Do a fast byte scan.
data = memory.getBlocks()[0]
buf = None
try:
    # Read the whole block into a byte buffer for a fast scan.
    size = int(data.getSize())
    b = bytearray(size)
    data.getBytes(data.getStart(), b, 0, size)
    base = int(data.getStart().getOffset())
    # Find 0x4C 7A 53 01 aligned to 4 bytes
    for i in range(0, size - 4, 4):
        if b[i] == 0x4C and b[i+1] == 0x7A and b[i+2] == 0x53 and b[i+3] == 0x01:
            magic_words.append(base + i)
    # Also try any alignment
    for i in range(size - 4):
        if b[i] == 0x4C and b[i+1] == 0x7A and b[i+2] == 0x53 and b[i+3] == 0x01:
            if (base + i) not in magic_words:
                magic_words.append(base + i)
except Exception as e:
    print("scan err: %s" % e)

print("magic u32 0x%08x locations: %d" % (MAGIC, len(magic_words)))
for w in magic_words[:20]:
    print("  0x%08x" % w)

# 2. For each magic-word address, find code that references it (would be an LDR).
xref_funcs = set()
for w in magic_words:
    a = af.getAddress(w)
    refs = list(currentProgram.getReferenceManager().getReferencesTo(a))
    for r in refs:
        from_a = r.getFromAddress()
        f = fm.getFunctionContaining(from_a)
        if f:
            xref_funcs.add(f)
            print("  ref from 0x%x in %s @ 0x%x" %
                  (from_a.getOffset(), f.getName(), f.getEntryPoint().getOffset()))

# 3. Additionally: scan every function for the byte-CMP sequence 'L' then 'z':
#    Look for two CMP-with-imm instructions within a 32-byte window where the imms
#    are 0x4C and 0x7A.
byte_cmp_funcs = set()
for f in fm.getFunctions(True):
    if xref_funcs and f in xref_funcs:
        continue
    body = f.getBody()
    ins_list = list(listing.getInstructions(body, True))
    # Extract immediate operands of CMP instructions
    imms = []
    for ins in ins_list:
        mnem = ins.getMnemonicString()
        if mnem and mnem.startswith("cmp"):
            for op_i in range(ins.getNumOperands()):
                for o in ins.getOpObjects(op_i):
                    try:
                        v = int(o.getValue())
                    except:
                        continue
                    imms.append((int(ins.getAddress().getOffset()), v))
    # Check if we ever have 0x4C then 0x7A within 32 bytes
    for i in range(len(imms) - 1):
        a1, v1 = imms[i]
        a2, v2 = imms[i+1] if i+1 < len(imms) else (0, 0)
        if v1 == 0x4C and v2 == 0x7A and abs(a2 - a1) < 32:
            byte_cmp_funcs.add(f)
            break

print("byte-cmp candidate functions: %d" % len(byte_cmp_funcs))
for f in list(byte_cmp_funcs)[:20]:
    print("  %s @ 0x%x" % (f.getName(), f.getEntryPoint().getOffset()))

# 4. Save both sets to a file for follow-up decompilation.
with open(os.path.join(OUT, "mm3d_lzs_hunt.txt"), "w") as fp:
    fp.write("# functions that xref the u32 magic 0x%08x\n" % MAGIC)
    for f in xref_funcs:
        fp.write("0x%08x  %s  (magic-xref)\n" % (f.getEntryPoint().getOffset(), f.getName()))
    fp.write("# functions with byte-CMP 'L' then 'z' immediates\n")
    for f in byte_cmp_funcs:
        fp.write("0x%08x  %s  (byte-cmp)\n" % (f.getEntryPoint().getOffset(), f.getName()))
print("wrote mm3d_lzs_hunt.txt")
