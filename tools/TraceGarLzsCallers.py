# -*- coding: utf-8 -*-
# Trace callers of ".gar.lzs" path literals in the binary. Uses memory.findBytes
# across ALL blocks so we don't miss ones outside block[0]. Then walks references
# TO each string and rolls up seed functions + forward call graph.
import os
from ghidra.util.task import ConsoleTaskMonitor
from ghidra.app.decompiler import DecompInterface
from ghidra.program.model.address import AddressSet

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
DEC_OUT = os.path.join(OUT, "decomp", "trace")
SEED_OUT = os.path.join(OUT, "decomp", "seeds")
for d in (OUT, DEC_OUT, SEED_OUT):
    if not os.path.isdir(d):
        os.makedirs(d)

memory = currentProgram.getMemory()
listing = currentProgram.getListing()
af = currentProgram.getAddressFactory().getDefaultAddressSpace()
fm = currentProgram.getFunctionManager()
rm = currentProgram.getReferenceManager()

needle = ".gar.lzs"
# Jython 2 compat: pass str, findBytes accepts a String
needle_bytes = needle

# 1. findBytes across all memory
starts = []
cur = memory.getMinAddress()
end = memory.getMaxAddress()
mon = ConsoleTaskMonitor()
while cur is not None and cur.compareTo(end) <= 0:
    hit = memory.findBytes(cur, needle_bytes, None, True, mon)
    if hit is None:
        break
    starts.append(int(hit.getOffset()))
    cur = hit.add(1)
print("found %d '.gar.lzs' occurrences" % len(starts))

# For each hit, walk back through raw memory to find the start of the C string
# (previous null byte). Then that's the string-VA we look for xrefs to.
def string_start_va(hit_va):
    a = af.getAddress(hit_va)
    # walk back up to 96 bytes
    for k in range(0, 96):
        try:
            b = memory.getByte(a.subtract(k + 1)) & 0xFF
        except:
            return hit_va - k
        if b == 0 or b < 0x20 or b >= 0x7f:
            return hit_va - k
    return hit_va

string_vas = set()
for h in starts:
    string_vas.add(string_start_va(h))

print("distinct string starts: %d" % len(string_vas))
sample = sorted(string_vas)[:10]
for va in sample:
    # print a sample of the string
    a = af.getAddress(va)
    chars = []
    for k in range(64):
        try:
            b = memory.getByte(a.add(k)) & 0xFF
        except:
            break
        if b == 0:
            break
        chars.append(chr(b))
    print("  0x%08x  %s" % (va, "".join(chars)))

# 2. For each string VA, get references TO it.
seed_funcs = set()
for va in string_vas:
    a = af.getAddress(va)
    for r in rm.getReferencesTo(a):
        f = fm.getFunctionContaining(r.getFromAddress())
        if f:
            seed_funcs.add(f)
print("seed functions (ref a .gar.lzs literal): %d" % len(seed_funcs))
for f in list(seed_funcs)[:10]:
    print("  seed: 0x%x %s" % (f.getEntryPoint().getOffset(), f.getName()))

# If no explicit xrefs (constant analyzer didn't resolve MOVW/MOVT), fallback:
# search for the u32 low-half + high-half MOVW/MOVT sequence.
# But if we DO have seed_funcs, proceed with call-graph walk.

D = 5
reachable = {}
frontier = [(f, 0) for f in seed_funcs]
for f, _ in frontier:
    reachable[f] = 0
head = 0
while head < len(frontier):
    f, depth = frontier[head]; head += 1
    if depth >= D:
        continue
    try:
        callees = list(f.getCalledFunctions(mon))
    except:
        callees = []
    for callee in callees:
        if callee in reachable:
            continue
        reachable[callee] = depth + 1
        frontier.append((callee, depth + 1))
print("reachable functions (depth<=%d): %d" % (D, len(reachable)))

# 3. Score reachable functions with LZ77 body heuristic.
NIBBLE_MASKS = set([0xF, 0xFF, 0xFFF])
BIT_MASKS = set([0x1, 0x80, 0x2, 0x40, 0x4])
SHIFTS_OF_INTEREST = set([4, 8, 12])

def is_ldrb(m):  return m in ("ldrb", "ldrb.w", "ldrbt")
def is_strb(m):  return m in ("strb", "strb.w", "strbt")
def is_shift(m): return m in ("lsr", "lsl", "asr", "lsrs", "lsls", "asrs")
def is_mask(m):  return m in ("and", "ands", "bic", "bics", "tst")

scored = []
for f, depth in reachable.items():
    body = f.getBody()
    ins_list = list(listing.getInstructions(body, True))
    L = len(ins_list)
    if L < 40 or L > 1200:
        continue
    mnems = [(ins.getMnemonicString() or "").lower() for ins in ins_list]
    ldrb_strb = postinc = bit_mask = nibble = shift4 = back = 0
    for i in range(L - 1):
        if is_ldrb(mnems[i]):
            for j in range(i + 1, min(i + 6, L)):
                if is_strb(mnems[j]):
                    ldrb_strb += 1
                    break
    for i, ins in enumerate(ins_list):
        m = mnems[i]
        if is_strb(m):
            s = ins.toString().lower()
            if "]!" in s or ("], #" in s and "strb" in s):
                postinc += 1
        if is_mask(m) or is_shift(m):
            for op_i in range(ins.getNumOperands()):
                for o in ins.getOpObjects(op_i):
                    try: v = int(o.getValue())
                    except: continue
                    if is_mask(m) and v in NIBBLE_MASKS: nibble += 1
                    if is_mask(m) and v in BIT_MASKS: bit_mask += 1
                    if is_shift(m) and v in SHIFTS_OF_INTEREST: shift4 += 1
        if m and m.startswith("b") and not m.startswith("bl") and not m.startswith("bx") and m not in ("bic","bics"):
            for r in ins.getReferencesFrom():
                to = r.getToAddress()
                if to and int(to.getOffset()) < int(ins.getAddress().getOffset()):
                    back += 1
                    break
    if ldrb_strb == 0:
        continue
    score = 3*min(ldrb_strb,6) + 2*min(postinc,6) + 2*min(bit_mask,4) + 2*min(nibble,4) + 2*min(shift4,4) + min(back,8)
    if 60 <= L <= 350: score += 5
    elif L > 800: score -= 3
    scored.append((score, depth, int(f.getEntryPoint().getOffset()), f.getName(), L,
                   ldrb_strb, postinc, bit_mask, nibble, shift4, back))

scored.sort(reverse=True)
csv_path = os.path.join(OUT, "mm3d_lz77_from_garlzs.csv")
with open(csv_path, "w") as fp:
    fp.write("score,depth,addr,name,size,ldrb_strb,postinc,bit_mask,nibble,shift4,back\n")
    for r in scored:
        fp.write("%d,%d,0x%08x,%s,%d,%d,%d,%d,%d,%d,%d\n" % r)
print("wrote %s (%d candidates)" % (csv_path, len(scored)))

# 4. Decompile top 20 candidates + a couple of seeds.
di = DecompInterface()
di.openProgram(currentProgram)
for r in scored[:20]:
    score, depth, va = r[0], r[1], r[2]
    addr = af.getAddress(va)
    f = fm.getFunctionContaining(addr)
    if not f: continue
    dres = di.decompileFunction(f, 60, mon)
    if not (dres and dres.decompileCompleted()): continue
    c = dres.getDecompiledFunction().getC()
    path = os.path.join(DEC_OUT, "s%03d_d%d_fn_0x%08x.c" % (score, depth, va))
    with open(path, "w") as fp:
        fp.write("// score=%d depth=%d va=0x%08x name=%s size=%d\n" % (score, depth, va, r[3], r[4]))
        fp.write("// ldrb_strb=%d postinc=%d bit_mask=%d nibble=%d shift4=%d back=%d\n" %
                 (r[5], r[6], r[7], r[8], r[9], r[10]))
        fp.write(c)
    print("wrote %s" % path)

for f in list(seed_funcs)[:8]:
    dres = di.decompileFunction(f, 60, mon)
    if not (dres and dres.decompileCompleted()): continue
    c = dres.getDecompiledFunction().getC()
    va = int(f.getEntryPoint().getOffset())
    path = os.path.join(SEED_OUT, "seed_fn_0x%08x.c" % va)
    with open(path, "w") as fp:
        fp.write("// SEED va=0x%08x name=%s\n" % (va, f.getName()))
        fp.write(c)
    print("wrote %s" % path)

print("done.")
