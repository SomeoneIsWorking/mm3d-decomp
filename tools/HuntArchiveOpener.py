# -*- coding: utf-8 -*-
# Find the function that opens .gar.lzs archives. Strategy: find every immediate operand
# equal to a VA in [0x00692818, 0x006A0000) (the zelda2_XXX C-string table), then map
# to the containing function. That function is the actor-archive loader — from there
# we trace forward to LzS detection + decompression.
import os
listing = currentProgram.getListing()
memory = currentProgram.getMemory()
af = currentProgram.getAddressFactory().getDefaultAddressSpace()
fm = currentProgram.getFunctionManager()

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

TABLE_LO = 0x00692818
TABLE_HI = 0x006a0000

# Approach: scan memory (well, the data section) for u32 words in that range,
# treating them as literal pool entries. Then find LDR instructions that reference
# each such literal.
data = memory.getBlocks()[0]
size = int(data.getSize())
b = bytearray(size)
data.getBytes(data.getStart(), b, 0, size)
base = int(data.getStart().getOffset())

lit_pool_entries = []
for i in range(0, size - 4):
    v = b[i] | (b[i+1] << 8) | (b[i+2] << 16) | (b[i+3] << 24)
    if TABLE_LO <= v < TABLE_HI:
        lit_pool_entries.append((base + i, v))

print("literal-pool entries pointing into zelda2 string table: %d" % len(lit_pool_entries))

# For each entry, find the enclosing function.
loader_funcs = {}
for lit_a, tgt in lit_pool_entries:
    lit_addr = af.getAddress(lit_a)
    # The literal is inside a function's constant pool — find the enclosing function.
    f = fm.getFunctionContaining(lit_addr)
    if f is None: continue
    loader_funcs.setdefault(f, []).append((lit_a, tgt))

# Sort by hit count.
by_hits = sorted(loader_funcs.items(), key=lambda kv: -len(kv[1]))
for f, hits in by_hits[:20]:
    print("  %s @ 0x%x hits=%d  sample tgt 0x%x" %
          (f.getName(), f.getEntryPoint().getOffset(), len(hits), hits[0][1]))

with open(os.path.join(OUT, "mm3d_archive_openers.txt"), "w") as fp:
    for f, hits in by_hits:
        fp.write("0x%08x  %s  hits=%d\n" % (f.getEntryPoint().getOffset(), f.getName(), len(hits)))
print("wrote mm3d_archive_openers.txt")
