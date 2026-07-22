# -*- coding: utf-8 -*-
# Body-heuristic search for the Grezzo LzS decoder.
#
# Structural fingerprints of a byte-oriented LZ77-family decoder (ARM):
#   (a) A byte copy from the OUTPUT buffer to the OUTPUT buffer — LDRB/STRB pair
#       where the load address is (out - disp) and the store address is (out).
#       Compilers usually emit these very close together (<= ~6 instructions apart).
#   (b) Post-increment byte streaming store: STRB Rt, [Rn], #1  (writeback form).
#   (c) A control-bit test: TST/ANDS with #1 or #0x80 (single-bit mask).
#   (d) A length/displacement split: AND/BIC/MOV with 0xF, 0xFF, or 0xFFF,
#       or an LSR/ASR/LSL by #4 (nibble split typical of LZ77/LZ11).
#   (e) A loop back-edge (branch to an earlier address in the function).
#   (f) Body between ~80 and ~2000 instructions (very small = leaf; huge = not this).
#
# We score every function, sort, and write the top candidates to CSV, then
# also decompile the top-N straight to .c files under build/decomp/lz77/.
#
# Run:
#   analyzeHeadless scratch/mm3d-decomp/ghidra mm3d -process mm3d.code -noanalysis \
#     -scriptPath scratch/mm3d-decomp -postScript BodyHeuristicLZ77.py
import os
from ghidra.app.decompiler import DecompInterface
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
DEC_OUT = os.path.join(OUT, "decomp", "lz77")
for d in (OUT, DEC_OUT):
    if not os.path.isdir(d):
        os.makedirs(d)

fm = currentProgram.getFunctionManager()
listing = currentProgram.getListing()
af = currentProgram.getAddressFactory().getDefaultAddressSpace()

TOP_N_DECOMP = 25
MIN_BODY = 60
MAX_BODY = 2500

NIBBLE_MASKS = set([0xF, 0xFF, 0xFFF, 0xFFFF, 0x80, 0x7F, 0xFE])
BIT_MASKS = set([0x1, 0x80, 0x2, 0x40, 0x4])
SHIFTS_OF_INTEREST = set([4, 8, 12, 3, 5])

def is_ldrb(m):  return m in ("ldrb", "ldrb.w", "ldrbt")
def is_strb(m):  return m in ("strb", "strb.w", "strbt")
def is_shift(m): return m in ("lsr", "lsl", "asr", "lsrs", "lsls", "asrs")
def is_mask(m):  return m in ("and", "ands", "bic", "bics", "tst")
def is_branch(m):
    return m.startswith("b") and not m.startswith("bl") and not m.startswith("bx") and m not in ("bic", "bics")

results = []
n = 0
for f in fm.getFunctions(True):
    n += 1
    body = f.getBody()
    ins_list = list(listing.getInstructions(body, True))
    L = len(ins_list)
    if L < MIN_BODY or L > MAX_BODY:
        continue

    entry_off = int(f.getEntryPoint().getOffset())

    # Precompute per-ins summary
    mnems = []
    for ins in ins_list:
        m = ins.getMnemonicString()
        if m is None: m = ""
        mnems.append(m.lower())

    # (a) LDRB immediately followed by STRB (within window)
    ldrb_strb_pairs = 0
    for i in range(L - 1):
        if is_ldrb(mnems[i]):
            for j in range(i + 1, min(i + 6, L)):
                if is_strb(mnems[j]):
                    ldrb_strb_pairs += 1
                    break

    if ldrb_strb_pairs == 0:
        continue  # every LZ77 decoder has these

    # (b) post-increment byte store: look at operand string
    postinc_strb = 0
    for i, ins in enumerate(ins_list):
        if not is_strb(mnems[i]):
            continue
        # Operand representation as text — cheap way to detect writeback / post-inc
        s = ins.toString().lower()
        if "]!" in s or ("]," in s and "#1" in s and "strb" in s):
            postinc_strb += 1

    # (c) bit test / mask / (d) nibble mask / shift by 4 / (e) branch back-edge
    bit_mask_hits = 0
    nibble_hits = 0
    shift4_hits = 0
    backedges = 0
    for i, ins in enumerate(ins_list):
        m = mnems[i]
        # scan immediate operand values
        if is_mask(m) or is_shift(m):
            for op_i in range(ins.getNumOperands()):
                for o in ins.getOpObjects(op_i):
                    try:
                        v = int(o.getValue())
                    except:
                        continue
                    if is_mask(m) and v in NIBBLE_MASKS:
                        nibble_hits += 1
                    if is_mask(m) and v in BIT_MASKS:
                        bit_mask_hits += 1
                    if is_shift(m) and v in SHIFTS_OF_INTEREST:
                        shift4_hits += 1
        if is_branch(m):
            # See if the flow reference points earlier than the branch site
            for r in ins.getReferencesFrom():
                to = r.getToAddress()
                if to is None:
                    continue
                if int(to.getOffset()) < int(ins.getAddress().getOffset()):
                    backedges += 1
                    break

    score = 0
    score += 3 * min(ldrb_strb_pairs, 6)
    score += 2 * min(postinc_strb, 6)
    score += 2 * min(bit_mask_hits, 4)
    score += 2 * min(nibble_hits, 4)
    score += 2 * min(shift4_hits, 4)
    score += 1 * min(backedges, 8)
    # Prefer medium bodies
    if 100 <= L <= 800:
        score += 3
    elif L > 1500:
        score -= 2

    results.append((score, entry_off, f.getName(), L,
                    ldrb_strb_pairs, postinc_strb, bit_mask_hits,
                    nibble_hits, shift4_hits, backedges))

print("scanned %d functions, %d candidates" % (n, len(results)))
results.sort(reverse=True)

csv_path = os.path.join(OUT, "mm3d_lz77_bodyheur.csv")
with open(csv_path, "w") as fp:
    fp.write("score,addr,name,size,ldrb_strb,postinc_strb,bit_mask,nibble_mask,shift4,backedges\n")
    for r in results:
        fp.write("%d,0x%08x,%s,%d,%d,%d,%d,%d,%d,%d\n" % r)
print("wrote %s" % csv_path)

# Decompile top N
di = DecompInterface()
di.openProgram(currentProgram)
mon = ConsoleTaskMonitor()

for r in results[:TOP_N_DECOMP]:
    score, va, name, L = r[0], r[1], r[2], r[3]
    addr = af.getAddress(va)
    f = fm.getFunctionContaining(addr)
    if not f:
        continue
    dres = di.decompileFunction(f, 60, mon)
    if not (dres and dres.decompileCompleted()):
        continue
    c = dres.getDecompiledFunction().getC()
    path = os.path.join(DEC_OUT, "s%03d_fn_0x%08x.c" % (score, va))
    with open(path, "w") as fp:
        fp.write("// score=%d va=0x%08x name=%s size=%d\n" % (score, va, name, L))
        fp.write("// ldrb_strb=%d postinc=%d bit_mask=%d nibble=%d shift4=%d back=%d\n" %
                 (r[4], r[5], r[6], r[7], r[8], r[9]))
        fp.write(c)
    print("wrote %s" % path)

print("done.")
