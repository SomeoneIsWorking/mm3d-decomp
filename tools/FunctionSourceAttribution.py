# -*- coding: utf-8 -*-
#@runtime Jython
# Attribute MM3D functions to their ORIGINAL source files, per FUNCTION.
#
# WHY: MM3D ships without symbols, so every recovered function is `FUN_<addr>`, which is not
# readable C++. The engine's asserts embed absolute paths from the original build:
#     C:\Jenkins\workspace\joker\prog\game\sources\original\z_kankyo.cpp(2070)
# The function that reads that string is, by the developers' own construction, defined in that
# source file. That is ground truth, not a fingerprint match.
#
# THE BUG THIS FILE FIXES. SourceFileMap.py called `getReferencesTo(string_va)` and got nothing for
# all 281 strings, and concluded the strings were unreferenced. That was the wrong question. The
# assert string is never addressed directly by code: the code loads a WORD from a literal pool
# (or a data table) that CONTAINS the string address, and Ghidra's reference manager records the
# reference to the POOL SLOT, not to the string. Asking about the string address therefore returns
# zero by construction, and a project that trusted that number would ship a clean, confident, and
# completely vacuous "0 references".
#
#   Verified on mm3d.code: 216 pool slots hold a pointer to an assert string; 192 of them have a
#   real code reference, which is the actual attribution signal.
#
# CONFIDENCE, and why there are only two values:
#   direct -- a code reference to the pool slot resolves to an instruction inside a known function.
#             The referencing instruction is the one that consumes the literal, so that function
#             owns the assert.
#   pooled -- the slot is referenced from DATA, not from an instruction; resolving the chain one
#             hop further lands in code. The function is a real consumer of a table that holds the
#             string, but it is not the function that immediately reads the literal.
# Nothing else is emitted. A string with no pointer, or a chain that never reaches code, attributes
# NO function -- it is reported in the summary as unattributed rather than guessed at.
#
# Env:
#   MM3D_ATTR_OUT  output CSV (default: <checkout>/mm3d-decomp/build/decomp/function_source_map.csv)
#   MM3D_ATTR_SUMMARY  summary text file (default: alongside the CSV)
#   MM3D_ATTR_REQUIRE  file name the control must positively confirm (default: z_kankyo.cpp).
#                      Settable so the control's FAILURE path can be exercised on purpose; a control
#                      that has only ever been seen to pass is not evidence of anything.
import os
import re
import struct

import jarray

prog = currentProgram
fm = prog.getFunctionManager()
rm = prog.getReferenceManager()
mem = prog.getMemory()
af = prog.getAddressFactory().getDefaultAddressSpace()
listing = prog.getListing()


def _checkout_root():
    # Ghidra headless runs scripts with an unrelated CWD, so walk up looking for the checkout
    # rather than writing to a path resolved from wherever the daemon happened to start.
    here = os.path.abspath(os.getcwd())
    for _ in range(6):
        if os.path.isdir(os.path.join(here, "mm3d-decomp", "build", "decomp")):
            return here
        parent = os.path.dirname(here)
        if parent == here:
            break
        here = parent
    return None


_root = _checkout_root()
if _root is None:
    raise RuntimeError("cannot locate the zelda3d checkout; set MM3D_ATTR_OUT explicitly")
_default_dir = os.path.join(_root, "mm3d-decomp", "build", "decomp")
out_path = os.environ.get("MM3D_ATTR_OUT") or os.path.join(_default_dir, "function_source_map.csv")
summary_path = os.environ.get("MM3D_ATTR_SUMMARY") or os.path.join(_default_dir, "function_source_map.summary.txt")

# ---------------------------------------------------------------- scan the image
blocks = [b for b in mem.getBlocks() if b.isInitialized()]
print("SCAN blocks=%d" % len(blocks))
if not blocks:
    print("CONTROL FAILED: no initialized memory blocks; nothing was scanned")
    raise SystemExit(1)

texts = []
scanned = 0
for blk in blocks:
    n = int(blk.getSize())
    buf = jarray.zeros(n, "b")  # a real Java array: `bytearray` is silently NOT filled by Ghidra
    mem.getBytes(blk.getStart(), buf)
    texts.append((blk.getStart().getOffset(), "".join([chr(buf[i] & 0xFF) for i in range(n)])))
    scanned += n
    print("  BLOCK %s 0x%08x size=%d" % (blk.getName(), blk.getStart().getOffset(), n))
print("SCAN bytes=%d" % scanned)

# ---------------------------------------------------------------- find assert strings
PATTERN = re.compile(r"([A-Za-z_][A-Za-z_0-9]*\.cpp)\((\d+)\)")


def _path_terminator(ch):
    """True when `ch` cannot be part of an original build path.

    0xFF matters as much as the C0 controls. The engine pads adjacent string slots with 0xFF, and a
    naive "stop at a byte below 0x20" walk-back swallows that padding, putting the computed string
    start inside the padding instead of on the 'C' of `C:\Jenkins`. A pointer then never matches
    the string and the assert looks unreferenced. Fixing this alone took the strings with a real
    pointer from 205 to 280 of 281.
    """
    o = ord(ch)
    return o < 32 or o == 0xFF


strings = {}  # start_va -> (file, line, text, token_start, token_end)
for base, text in texts:
    for m in PATTERN.finditer(text):
        back = m.start()
        while back > 0 and not _path_terminator(text[back - 1]):
            back -= 1
        path = "".join([c if 32 <= ord(c) < 127 else " " for c in text[back:m.end()]]).strip()
        strings[base + back] = (m.group(1), int(m.group(2)), path, m.start() - back, m.end() - back)
print("SCAN assert_strings=%d distinct_files=%d"
      % (len(strings), len(set(v[0] for v in strings.values()))))


def _find_slots(target_va):
    """Every 4-aligned word in the image whose value is target_va."""
    packed = struct.pack("<I", target_va)
    hits = []
    for base, text in texts:
        i = 0
        while True:
            i = text.find(packed, i)
            if i < 0:
                break
            if i % 4 == 0:
                hits.append(base + i)
            i += 1
    return hits


def _is_literal_load(src_va, slot_va):
    """True when an ARM/Thumb LDR-literal at src_va provably loads from slot_va.

    This replaces trust in Ghidra's reference manager as the criterion for `direct`. A reference
    alone is not enough: this image contains references whose source address falls inside a
    function body but whose "instruction" is a register save (`STMFD sp!, {r1,r2}`) that cannot
    load anything, and one such reference produced a confident, indefensible attribution. Decoding
    the load and recomputing its PC-relative target makes every emitted row independently
    checkable against the raw image, which is the whole point of the exercise.
    """
    try:
        a = af.getAddress(src_va)
    except Exception:
        return False
    if a is None:
        return False
    buf = jarray.zeros(4, "b")
    try:
        n = mem.getBytes(a, buf)
    except Exception:
        return False
    if n is None or n < 4:
        return False
    ins = 0
    for i in range(4):
        ins |= (buf[i] & 0xFF) << (8 * i)
    if (ins >> 28) == 0xE and (ins & 0x0E5F0000) == 0x041F0000:
        imm = ins & 0xFFF
        return (src_va + 8 + (imm if (ins >> 23) & 1 else -imm)) == slot_va
    half = ins & 0xFFFF
    if 0x4800 <= half <= 0x4FFF:  # Thumb LDR Rd,[PC,#imm*4]
        return (((src_va + 4) & ~3) + (half & 0xFF) * 4) == slot_va
    return False


def _resolve(fn_of_addr):
    """Attribute one pool slot. Returns a list of (fn_entry, fn_name, confidence, evidence)."""
    try:
        a = af.getAddress(fn_of_addr)
    except Exception:
        a = None
    if a is None:
        return []
    out = []
    for r in rm.getReferencesTo(a):
        src = r.getFromAddress()
        f = fm.getFunctionContaining(src)
        rtype = str(r.getReferenceType())
        if f is not None:
            if not _is_literal_load(src.getOffset(), fn_of_addr):
                # Inside a function, but not a load of this slot. Recorded as rejected rather than
                # attributed: a reference whose source cannot load the slot is not evidence.
                rejected.append((fn_of_addr, src.getOffset(), rtype))
                continue
            out.append((f.getEntryPoint().getOffset(), f.getName(), "direct",
                        "ldrlit@0x%08x->slot0x%08x:%s" % (src.getOffset(), fn_of_addr, rtype)))
        else:
            # Referenced from data, not from an instruction: one hop further. If that lands in
            # code, the function consumes a TABLE holding the string, which is weaker evidence and
            # is labelled `pooled` rather than being passed off as direct.
            try:
                sa = af.getAddress(src.getOffset())
            except Exception:
                sa = None
            if sa is None:
                continue
            for r2 in rm.getReferencesTo(sa):
                f2 = fm.getFunctionContaining(r2.getFromAddress())
                if f2 is not None:
                    if not _is_literal_load(r2.getFromAddress().getOffset(), fn_of_addr):
                        rejected.append((fn_of_addr, r2.getFromAddress().getOffset(), "pooled:" + rtype))
                        continue
                    out.append((f2.getEntryPoint().getOffset(), f2.getName(), "pooled",
                                "tablecell0x%08x->ldrlit@0x%08x->slot0x%08x"
                                % (src.getOffset(), r2.getFromAddress().getOffset(), fn_of_addr)))
    return out


# ---------------------------------------------------------------- string -> slot -> function
# per function: file -> {lines:set, confidence rank, evidence:[..]}
attrib = {}
n_slots = 0
n_slot_refs = 0
n_slots_with_data_refs = 0
rejected = []  # references that could not be shown to be a load of the slot
strings_with_slot = 0
strings_unattributed = []
per_string = {}  # sva -> (confidence, n_functions)

for sva in sorted(strings):
    name, line, path, _b, _e = strings[sva]
    slots = [(s, 0) for s in _find_slots(sva)]
    if not slots:
        alt = {}
        for delta in (4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60, 64):
            for s in _find_slots(sva + delta):
                alt.setdefault(s, delta)
        slots = sorted(alt.items())
    if not slots:
        strings_unattributed.append((sva, name, line, "no_pointer", ""))
        continue
    strings_with_slot += 1
    fns_here = set()
    for (slot, delta) in slots:
        n_slots += 1
        n_refs_here = 0
        n_refs_from_data = 0
        try:
            sa = af.getAddress(slot)
        except Exception:
            sa = None
        if sa is not None:
            for r in rm.getReferencesTo(sa):
                n_refs_here += 1
                if fm.getFunctionContaining(r.getFromAddress()) is None:
                    n_refs_from_data += 1
        if n_refs_from_data:
            # A reference from DATA, not from an instruction: this is the only route to the
            # `pooled` confidence. Counted so the summary can say whether that path ever fired
            # rather than leaving a reader to assume it produced rows.
            n_slots_with_data_refs += 1
        found = _resolve(slot)
        n_slot_refs += len(found)
        for (entry, fname, conf, ev) in found:
            fns_here.add(entry)
            slot_ev = "%s str=0x%08x%s" % (ev, sva, "" if delta == 0 else " strptr_offset=+%d" % delta)
            byfile = attrib.setdefault(entry, {})
            rec = byfile.setdefault(name, {"lines": set(), "conf": None, "ev": []})
            rec["lines"].add(line)
            rec["ev"].append(slot_ev)
            if rec["conf"] is None or (rec["conf"] == "pooled" and conf == "direct"):
                rec["conf"] = conf
        if not found:
            # Record WHY, so the summary distinguishes "no pointer at all" from "a pointer nobody
            # references". The second kind sits in a data table and needs a dataflow Ghidra did not
            # resolve; it is reported, never guessed at.
            strings_unattributed.append(
                (sva, name, line, "no_code_ref",
                 "slot0x%08x refs=%d refs_from_data=%d" % (slot, n_refs_here, n_refs_from_data)))
    if fns_here:
        per_string[sva] = len(fns_here)

# ---------------------------------------------------------------- write the map
directory = os.path.dirname(out_path)
if not os.path.isdir(directory):
    os.makedirs(directory)

rows = []
for entry in sorted(attrib):
    fname_at = None
    try:
        fname_at = fm.getFunctionAt(af.getAddress(entry)).getName()
    except Exception:
        pass
    for name in sorted(attrib[entry]):
        rec = attrib[entry][name]
        # `line` is the LOWEST assert line this function holds in that file: a function's asserts
        # span a range, and the lowest is the one closest to the function's own definition. It is
        # the minimum over ALL the function's asserts, not whichever assert was visited last --
        # an earlier version of this script stored the latter, which made the column meaningless
        # while still looking like a line number. Every assert is listed in `evidence`, so nothing
        # is lost by summarising here.
        ev = "n_asserts=%d lines=%s %s" % (
            len(rec["ev"]),
            ",".join(str(x) for x in sorted(rec["lines"])),
            ";".join(sorted(set(rec["ev"]))))
        rows.append((entry, fname_at or "FUN_%08x" % entry, name, min(rec["lines"]), rec["conf"], ev))

with open(out_path, "w") as fp:
    fp.write("fn_entry,fn_name,source_file,line,confidence,evidence\n")
    for entry, fname, name, line, conf, ev in rows:
        fp.write("0x%08x,%s,%s,%d,%s,%s\n" % (entry, fname, name, line, conf, ev.replace(",", ";")))

n_direct = len([r for r in rows if r[4] == "direct"])
n_pooled = len([r for r in rows if r[4] == "pooled"])
n_fns = len(attrib)
n_files = len(set(r[2] for r in rows))
total_fns = fm.getFunctionCount()

per_file = {}
for r in rows:
    per_file.setdefault(r[2], set()).add(r[0])
top = sorted(per_file.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:15]

# A string can own several slots, so `strings_unattributed` holds one entry per unattributed SLOT.
# Report per STRING, and drop strings that another slot DID attribute: those are attributed, with
# one dead pointer, and calling them unattributed would understate the result.
unattributed_by_string = {}
for sva, name, line, kind, detail in strings_unattributed:
    if sva in per_string:
        continue
    rec = unattributed_by_string.setdefault(sva, [name, line, kind, []])
    rec[3].append(detail)
unattributed_strings = [(sva, v[0], v[1], v[2], ";".join(x for x in v[3] if x))
                        for sva, v in sorted(unattributed_by_string.items())]

reason_count = {}
for _s, _n, _l, kind, _d in unattributed_strings:
    reason_count[kind] = reason_count.get(kind, 0) + 1

require_name = os.environ.get("MM3D_ATTR_REQUIRE", "z_kankyo.cpp")
kankyo_fns = per_file.get(require_name, set())
control_lines = []
control_lines.append("SCAN bytes=%d" % scanned)
control_lines.append("SCAN assert_strings=%d" % len(strings))
control_lines.append("MATCH strings_with_pointer_slot=%d" % strings_with_slot)
control_lines.append("MATCH pool_slots=%d slot_reference_hits=%d slots_with_data_refs=%d"
                     % (n_slots, n_slot_refs, n_slots_with_data_refs))
control_lines.append("MATCH strings_attributing_a_function=%d" % len(per_string))
control_lines.append("MATCH functions_attributed=%d of %d" % (n_fns, total_fns))
control_lines.append("MATCH rows=%d direct=%d pooled=%d source_files=%d" % (len(rows), n_direct, n_pooled, n_files))
control_lines.append("REJECTED references_not_a_load_of_the_slot=%d" % len(rejected))
control_lines.append("UNATTRIBUTED strings=%d %s" % (len(unattributed_strings), reason_count))
control_lines.append("CONTROL %s functions=%d" % (require_name, len(kankyo_fns)))
if kankyo_fns:
    sample = sorted(kankyo_fns)[:6]
    control_lines.append("CONTROL OK %s sample=%s"
                         % (require_name, ", ".join(["0x%08x" % f for f in sample])))
else:
    control_lines.append("CONTROL FAILED: %s attributed zero functions" % require_name)
for c in control_lines:
    print(c)

with open(summary_path, "w") as fp:
    fp.write("\n".join(control_lines))
    fp.write("\nper_source_file:\n")
    for name, fns in top:
        fp.write("  %-40s %d\n" % (name, len(fns)))
    fp.write("unattributed_strings (no slot produced a function):\n")
    for sva, name, line, kind, detail in unattributed_strings:
        fp.write("  0x%08x %s(%d) %s %s\n" % (sva, name, line, kind, detail))
print("wrote %s" % out_path)
print("wrote %s" % summary_path)

# CONTROL: exit non-zero on a zero match, or if the known-good string attributes nothing. A tool
# that reports "matched 0" here would be repeating the exact bug this script exists to fix.
if not rows or not kankyo_fns:
    print("CONTROL FAILED: exiting non-zero")
    raise SystemExit(1)
print("CONTROL PASSED")
