# -*- coding: utf-8 -*-
# Tighter LzS hunt: find functions with ALL FOUR magic-byte immediates
# (0x4C 'L', 0x7A 'z', 0x53 'S', 0x01 '\1') as CMP-with-imm within ~48 bytes.
# The LzS decoder starts with a 4-byte magic check via LDRB+CMP per byte
# (ARM has no direct 32-bit-imm CMP). Also look for MOV-imm variants —
# ARM often uses `MOV R?, #imm` before `CMP` when the CMP register is fixed.
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

MAGIC = [0x4C, 0x7A, 0x53, 0x01]

candidates = []
for f in fm.getFunctions(True):
    body = f.getBody()
    imms = []
    for ins in listing.getInstructions(body, True):
        mnem = ins.getMnemonicString()
        if not mnem: continue
        if mnem.startswith("cmp") or mnem.startswith("mov"):
            for op_i in range(ins.getNumOperands()):
                for o in ins.getOpObjects(op_i):
                    try:
                        v = int(o.getValue())
                    except:
                        continue
                    imms.append((int(ins.getAddress().getOffset()), v))
    # Find any window of <=48 bytes containing all 4 magic bytes as immediates.
    for i in range(len(imms)):
        addrs = [imms[i][0]]
        seen = {imms[i][1]: imms[i][0]} if imms[i][1] in MAGIC else {}
        for j in range(i+1, len(imms)):
            if imms[j][0] - imms[i][0] > 48:
                break
            if imms[j][1] in MAGIC:
                seen[imms[j][1]] = imms[j][0]
        if len(seen) >= 3 and 0x4C in seen and 0x7A in seen:
            candidates.append((f.getEntryPoint().getOffset(), f.getName(),
                               len(seen), min(seen.values()), max(seen.values())))
            break

candidates.sort(key=lambda t: -t[2])
print("candidates (fn addr, name, magic_bytes_hit, window):")
for a, n, hit, lo, hi in candidates[:30]:
    print("  0x%08x  %s  hit=%d window=[0x%x..0x%x]" % (a, n, hit, lo, hi))

with open(os.path.join(OUT, "mm3d_lzs_hunt2.txt"), "w") as fp:
    for a, n, hit, lo, hi in candidates:
        fp.write("0x%08x  %s  hit=%d\n" % (a, n, hit))
print("wrote mm3d_lzs_hunt2.txt (%d)" % len(candidates))
