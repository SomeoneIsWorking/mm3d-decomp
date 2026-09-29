# -*- coding: utf-8 -*-
#@runtime Jython
# Attribute MM3D functions to their ORIGINAL source file, from the engine's own assert strings.
#
# WHY (see mm3d-decomp/docs/source_file_attribution.md for the measured result):
#   MM3D ships without symbols -- every recovered function is `FUN_<addr>`. But its asserts embed
#   the absolute path the string was compiled from, e.g.
#       C:\Jenkins\workspace\joker\prog\game\sources\original\z_kankyo.cpp(2070)
#   A function that reaches such a string is, by the developers' own construction, defined in that
#   source file. That is ground truth from the build, not a fingerprint match.
#
# WHY `SourceFileMap.py` ATTRIBUTED NOTHING (n_refs == 0 on every row):
#   It asked `getReferencesTo(<string address>)`. On CTR the strings are UNDEFINED bytes, so Ghidra
#   never built a data reference, and even with one the reference would have been to a literal-pool
#   WORD, not to the string. This script therefore does not use the reference manager at all: it
#   locates the 4-byte pointers to each string and then asks, per FUNCTION, which instruction
#   actually READS those pointer words, using a small pcode abstract interpreter.
#
# THE METHOD, and what makes an attribution evidence rather than a guess:
#   1. Scan initialized memory for the assert-path pattern -> a set of STRING BYTE RANGES.
#   2. Index every word-aligned word whose VALUE lands in one of those ranges -> a "pointer slot".
#   3. For every function that can reach a slot (an ARM/Thumb PC-relative load reaches only
#      +/-4095 bytes, so the candidate set is bounded -- this is the scan denominator), interpret
#      the function's pcode instruction by instruction, tracking which registers hold a
#      statically-known address. Every register write is modelled: anything this interpreter does
#      not model KILLS the register. A reference is recorded only when the interpreter can name the
#      effective address of a real LOAD/STORE in that function.
#   4. The register state is discarded at every branch, call and return, so a recorded address is
#      always produced by straight-line code inside the one function it is attributed to.
#
# CONFIDENCE (the only two values emitted):
#   direct  -- the LOAD/STORE effective address is INSIDE the assert string's bytes.
#   pooled  -- the effective address is a word whose VALUE points into the assert string's bytes
#              (a literal pool entry or a pointer table entry).
# Anything that cannot be proven by 1-4 is NOT written. No inference, no nearest-file guessing.
#
# Env:
#   MM3D_FSM_OUT    output CSV (default <repo>/mm3d-decomp/build/decomp/function_source_map.csv)
#   MM3D_FSM_REACH  SPEED ONLY. prefilter radius in bytes for which functions get interpreted;
#                   0 (default) interprets every function. Too small a radius loses references.
#   MM3D_FSM_DEBUG  if 1, dump the first few interpreted memory references (decode self-check)
#   MM3D_FSM_CROSS_BRANCH  DIAGNOSTIC ONLY; 1 carries register state across branches/calls, which
#                   over-approximates at joins. The shipped numbers never use it.
import os
import re
import bisect
import jarray

prog = currentProgram
fm = prog.getFunctionManager()
mem = prog.getMemory()
af = prog.getAddressFactory().getDefaultAddressSpace()
listing = prog.getListing()

BLOCK_LO = min([b.getStart().getOffset() for b in mem.getBlocks() if b.isInitialized()])
BLOCK_HI = max([b.getStart().getOffset() + int(b.getSize())
                for b in mem.getBlocks() if b.isInitialized()])


def _default_out():
    here = os.path.abspath(os.getcwd())
    for _ in range(6):
        if os.path.isdir(os.path.join(here, "mm3d-decomp", "build", "decomp")):
            return os.path.join(here, "mm3d-decomp", "build", "decomp", "function_source_map.csv")
        parent = os.path.dirname(here)
        if parent == here:
            break
        here = parent
    raise RuntimeError("cannot locate the zelda3d checkout; set MM3D_FSM_OUT explicitly")


out_path = os.environ.get("MM3D_FSM_OUT") or _default_out()
# 0 (the default) means "interpret every function"; a positive value is a prefilter radius in bytes.
reach = int(os.environ.get("MM3D_FSM_REACH", "0"))
debug = os.environ.get("MM3D_FSM_DEBUG") == "1"


def block_text(addr, n):
    """Bytes as a latin-1 str.

    NOTE the idiom: `jarray.zeros(n, "b")` allocates a REAL Java array that Ghidra's getBytes can
    fill. A Python `bytearray` is coerced into a Java COPY, getBytes fills the copy, and every
    search that follows silently returns -1 -- which is exactly how the first version of this
    pipeline reported a clean zero on strings that are provably present.
    """
    buf = jarray.zeros(n, "b")
    mem.getBytes(addr, buf)
    return "".join([chr(buf[i] & 0xFF) for i in range(n)])


def word_at(va):
    """Little-endian 32-bit word at a virtual address, or None if unmapped."""
    if va is None or va < BLOCK_LO or va > BLOCK_HI - 4:
        return None
    try:
        buf = jarray.zeros(4, "b")
        mem.getBytes(af.getAddress(va), buf)
    except java.lang.Throwable:
        return None
    return ((buf[0] & 0xFF) | ((buf[1] & 0xFF) << 8)
            | ((buf[2] & 0xFF) << 16) | ((buf[3] & 0xFF) << 24))


def words_of_block(blk):
    """(base_offset, [little-endian words]) for one block, read in bulk.

    A per-word getBytes() call would be a JNI round trip 1.5 million times; ByteBuffer does the
    whole block in one.
    """
    n = int(blk.getSize())
    buf = jarray.zeros(n, "b")
    mem.getBytes(blk.getStart(), buf)
    from java.nio import ByteBuffer, ByteOrder
    bb = ByteBuffer.wrap(buf)
    bb.order(ByteOrder.LITTLE_ENDIAN)
    count = n // 4
    out = jarray.zeros(count, "i")
    bb.position(0)
    bb.asIntBuffer().get(out, 0, count)
    return blk.getStart().getOffset(), out, count


# ---------------------------------------------------------------- 1. the strings
PATTERN = re.compile(r"([A-Za-z_][A-Za-z_0-9]*\.cpp)\((\d+)\)")
blocks = [b for b in mem.getBlocks() if b.isInitialized()]
print("SCAN: %d initialized blocks" % len(blocks))
if not blocks:
    print("CONTROL FAILED: no initialized memory; refusing to report zero")
    raise SystemExit(1)

scanned = 0
# run_start -> (file, line, full_text) for every run that contains at least one assert path
assert_runs = {}
run_count = 0
RUN_PATTERN = re.compile(r"[\x20-\x7e]+")
for blk in blocks:
    start = blk.getStart().getOffset()
    n = int(blk.getSize())
    text = block_text(blk.getStart(), n)
    scanned += n
    print("SCAN: block %s 0x%08x size=%d" % (blk.getName(), start, n))
    for m in RUN_PATTERN.finditer(text):
        run_count += 1
        run_va = start + m.start()
        run_txt = m.group(0)
        hit = PATTERN.search(run_txt)
        if hit:
            assert_runs[run_va] = (hit.group(1), int(hit.group(2)), run_txt)

print("SCAN: scanned %d bytes, %d printable runs, %d assert-path strings" % (scanned, run_count, len(assert_runs)))
if not assert_runs:
    print("CONTROL FAILED: zero assert-path strings in a %d-byte image" % scanned)
    raise SystemExit(1)
distinct_files = sorted(set(v[0] for v in assert_runs.values()))
print("SCAN: %d distinct source files referenced by asserts" % len(distinct_files))

# ---------------------------------------------------------------- 2. the pointer slots
slots = {}  # slot_va -> (run_start, file, line)
# A pointer to a string literal addresses the literal's FIRST byte, so only a word whose value
# equals a run start is a slot.
want = {}
for s in assert_runs:
    want[s] = assert_runs[s]
words_scanned = 0
for blk in blocks:
    base, arr, count = words_of_block(blk)
    for idx in range(count):
        w = arr[idx] & 0xFFFFFFFF
        words_scanned += 1
        if w in want:
            slots[base + idx * 4] = (w,) + want[w][:2]
print("SCAN: read %d words, %d word-aligned pointer slots into assert strings" % (words_scanned, len(slots)))
if not slots:
    print("CONTROL FAILED: assert strings found but no pointer slots; nothing could be attributed")
    raise SystemExit(1)

# ---------------------------------------------------------------- 3. candidate functions
funcs = []
for f in fm.getFunctions(True):
    body = f.getBody()
    funcs.append((body.getMinAddress().getOffset(), body.getMaxAddress().getOffset(), f))
print("SCAN: program has %d functions" % len(funcs))

# An ARM/Thumb PC-relative load reaches only +/-4095 bytes and a register-offset load another
# +/-4095, so MOST references are within ~8 KB of the slot. That is a speed knob, NOT a soundness
# bound: a chain of adds can walk a base further, and the interpreter (not this window) is what makes
# an attribution sound. The default therefore scans EVERY function; a smaller reach only loses
# results, never adds wrong ones.
slot_list = sorted(slots.keys())
starts_by_min = [f[0] for f in funcs]
ends_by_min = [f[1] for f in funcs]
candidates = set()
if reach <= 0:
    candidates = set(range(len(funcs)))
else:
    for x in slot_list:
        lo = bisect.bisect_left(starts_by_min, x - reach)
        hi = bisect.bisect_right(ends_by_min, x + reach)
        if hi > len(funcs):
            hi = len(funcs)
        for idx in range(lo, hi):
            candidates.add(idx)
print("SCAN: %d of %d functions interpreted (reach=%s)" % (len(candidates), len(funcs), reach if reach > 0 else "all"))

# ---------------------------------------------------------------- 4. interpret
records = {}          # (fn_entry, fn_name, file, line, confidence) -> (evidence, insn_va)
referenced_strings = {}   # run_start -> (file, line)
instr_scanned = 0
addrs_resolved = 0
loads_seen = 0
nested_refs = 0
debug_left = 5 if debug else 0
# Diagnostic only: carrying register state ACROSS branches/calls is an over-approximation (at a
# join point the state may come from a predecessor that does not run), so it is off by default and
# the shipped CSV never depends on it.
cross_branch = os.environ.get("MM3D_FSM_CROSS_BRANCH") == "1"


def key_of(vn):
    return (vn.getAddress().getAddressSpace().getSpaceID(), vn.getOffset())


# Ghidra function bodies here OVERLAP: FUN_003c8200 spans 0x3c8200-0x4f91cf and FUN_004f0324 spans
# 0x4f0324-0x50f2cf, so an instruction can be inside two "functions" at once. `getFunctionContaining`
# returns the outer one for these bodies, which would pile every assert in a runaway range onto a
# single name, so the INNERMOST container decides instead.
FN_TABLE = sorted([(f.getEntryPoint().getOffset(), b.getMinAddress().getOffset(),
                     b.getMaxAddress().getOffset(), f.getName())
                    for b, f in [(fn.getBody(), fn) for fn in fm.getFunctions(True)]])
FN_ENTRY = [t[0] for t in FN_TABLE]
FN_SPAN = max([hi - lo for _, lo, hi, _ in FN_TABLE] + [1])


def innermost(va):
    i = bisect.bisect_right(FN_ENTRY, va) - 1
    while i >= 0 and FN_ENTRY[i] >= va - FN_SPAN:
        e, lo, hi, n = FN_TABLE[i]
        if e <= va <= hi:
            return (e, n)
        i -= 1
    return None


def eval_addr(vn, regs, tmp):
    """The statically known effective address of a memory reference, or None."""
    if vn is None:
        return None
    if vn.isConstant():
        v = vn.getOffset()
        if v < 0:
            v += 1 << (8 * vn.getSize())
        return v
    if vn.isUnique():
        return tmp.get(key_of(vn))
    return regs.get(key_of(vn))


def set_out(out, v, regs, tmp):
    """Write a destination varnode. `None` means UNKNOWN, which is not the same as absent.

    Unique (temporary) varnodes live for one instruction only, so they go in `tmp`; registers go
    in `regs`, which is cleared at every branch.
    """
    if out is None:
        return
    if out.isUnique():
        if v is None:
            tmp.pop(key_of(out), None)
        else:
            tmp[key_of(out)] = v
        return
    if not out.isRegister():
        return
    k = key_of(out)
    if v is None:
        regs.pop(k, None)
    else:
        regs[k] = v


def record_ref(addr, instr, entry, name, pool_in_fn):
    """Attribute one provably-named effective address; returns True when it hit an assert string.

    Ghidra function bodies here NEST: a container such as FUN_003c8200 spans 0x3c8200-0x4f91cf and
    contains a separately discovered FUN_004f0324. An instruction in the inner function belongs to
    the INNER function, so the innermost container decides the row -- otherwise a long container
    would collect every assert in the image and be confidently wrong.
    """
    global addrs_resolved, debug_left, nested_refs
    addrs_resolved += 1
    hit = slots.get(addr)
    if hit is None:
        if addr not in assert_runs:
            return False
        hit = (addr,) + assert_runs[addr][:2]
    run_start, sfile, sline = hit
    own = innermost(instr.getAddress().getOffset())
    if own is not None and own[0] != entry:
        nested_refs += 1
        entry, name = own
    # `direct` = the instruction addresses the string's own bytes.
    # `pooled` = it addresses a word that points at them.
    conf = "direct" if addr == run_start else "pooled"
    referenced_strings[run_start] = (sfile, sline)
    ev = "%s @%s %s pool=0x%08x str=0x%08x %s" % (
        instr.toString(), instr.getAddress(), conf, addr, run_start,
        "pool-in-fn" if pool_in_fn else "pool-outside-fn")
    k = (entry, name, sfile, sline, conf)
    if k not in records:
        records[k] = (ev, instr.getAddress().getOffset())
    if debug_left > 0:
        print("DEBUG: %s  %s" % (name, ev))
        debug_left -= 1
    return True


def interpret(f, entry, name, lo, hi):
    """Interpret one function's pcode; record every memory reference with a provable address."""
    global instr_scanned, loads_seen
    regs = {}
    it = listing.getInstructions(f.getBody(), True)
    while it.hasNext():
        instr = it.next()
        instr_scanned += 1
        tmp = {}
        for op in instr.getPcode():
            m = op.getMnemonic()
            out = op.getOutput()
            if m == "LOAD" or m == "STORE":
                loads_seen += 1
                addr = eval_addr(op.getInput(1), regs, tmp)
                if addr is None:
                    set_out(out, None, regs, tmp)
                else:
                    record_ref(addr, instr, entry, name, lo <= addr <= hi)
                    if m == "LOAD":
                        # The loaded word is the register's new value: this is what turns a
                        # literal pool word into a base address for a second, indirect load.
                        set_out(out, word_at(addr), regs, tmp)
                    else:
                        set_out(out, None, regs, tmp)
            elif m == "COPY":
                set_out(out, eval_addr(op.getInput(0), regs, tmp), regs, tmp)
            elif m == "INT_ADD" or m == "INT_SUB" or m == "PIECE":
                a = eval_addr(op.getInput(0), regs, tmp)
                b = eval_addr(op.getInput(1), regs, tmp)
                set_out(out, (a + b) if (a is not None and b is not None) else None, regs, tmp)
            elif m == "INT_2COMP":
                a = eval_addr(op.getInput(0), regs, tmp)
                set_out(out, (-a if a is not None else None), regs, tmp)
            else:
                # Unmodelled side effect on this destination: the value is UNKNOWN from here on.
                # This is what makes the interpreter conservative rather than optimistic.
                set_out(out, None, regs, tmp)
        # A branch, call or return means the fall-through state is no longer provable, so the
        # tracked registers are dropped rather than carried into code that may not run.
        flow = instr.getFlowType()
        if cross_branch:
            if flow.isTerminal():
                regs.clear()
        elif flow.isJump() or flow.isCall() or flow.isTerminal():
            regs.clear()


for idx in sorted(candidates):
    lo, hi, f = funcs[idx]
    interpret(f, lo, f.getName(), lo, hi)

print("SCAN: interpreted %d instructions in %d candidate functions" % (instr_scanned, len(candidates)))
print("SCAN: %d loads/stores seen, %d had a statically known effective address" % (loads_seen, addrs_resolved))
print("SCAN: %d references re-homed to an inner function (nesting)" % nested_refs)

# ---------------------------------------------------------------- output
directory = os.path.dirname(out_path)
if not os.path.isdir(directory):
    os.makedirs(directory)
rows = sorted(records.items(), key=lambda kv: (kv[0][1], kv[0][3], kv[0][2]))
with open(out_path, "w") as fp:
    fp.write("fn_entry,fn_name,source_file,line,confidence,evidence\n")
    for k, (ev, iva) in rows:
        fp.write("0x%08x,%s,%s,%d,%s,%s\n"
                 % (k[0], k[1], k[2], k[3], k[4], ev.replace(",", ";")))
print("WROTE %s (%d rows)" % (out_path, len(rows)))

# ---------------------------------------------------------------- CONTROL
attributed_fns = set(k[0] for k in records)
attributed_files = set(k[2] for k in records)
kankyo = sorted(set(k[0] for k in records if k[2] == "z_kankyo.cpp"))
direct = len([k for k in records if k[4] == "direct"])
pooled = len([k for k in records if k[4] == "pooled"])
print("RESULT: %d/%d functions attributed (%d direct, %d pooled rows) across %d source files"
      % (len(attributed_fns), len(funcs), direct, pooled, len(attributed_files)))
print("RESULT: %d/%d assert strings reached by code (%d unreached)"
      % (len(referenced_strings), len(assert_runs), len(assert_runs) - len(referenced_strings)))
# The CSV keeps ONE witness per row, so it shows fewer distinct strings than were actually reached.
print("RESULT: %d distinct assert strings appear in the CSV evidence column"
      % len(set(re.search(r"str=0x([0-9a-fA-F]{8})", v[0]).group(1) for v in records.values())))

failed = False
if not records:
    print("CONTROL FAILED: scanned %d functions / %d instructions and attributed NOTHING" %
          (len(candidates), instr_scanned))
    failed = True
if addrs_resolved == 0:
    print("CONTROL FAILED: %d loads/stores interpreted, 0 with a resolvable effective address" % loads_seen)
    failed = True
kankyo_strings = len([1 for v in assert_runs.values() if v[0] == "z_kankyo.cpp"])
if not kankyo:
    print("CONTROL FAILED: z_kankyo.cpp is present in the image (%d string(s)) but no z_kankyo.cpp "
          "function was attributed" % kankyo_strings)
    failed = True
else:
    print("CONTROL OK: z_kankyo.cpp attributed: %s" % ", ".join("0x%08x" % a for a in kankyo))
if failed:
    raise SystemExit(1)
print("CONTROL OK: %d attributed functions, %d files, %d strings reached" %
      (len(attributed_fns), len(attributed_files), len(referenced_strings)))
