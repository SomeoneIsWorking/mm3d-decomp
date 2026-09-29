# -*- coding: utf-8 -*-
#@runtime Jython
# Diagnostic for the MM3D source-attribution task: is `getReferencesTo()` empty because the
# BINARY has no references, or because the PROGRAM was imported with `-noanalysis` and therefore
# never had any reference created in the first place?
#
# This distinction decides the whole approach. SourceFileMap.py reported n_refs=0 for all 281
# strings; if the reference manager is empty overall, that is a tool-state artifact and the fix is
# to run analysis, not to hunt for pointer tables.
#
# Prints what it scanned and what it matched. Exits non-zero if the image cannot be read.
import struct

import jarray

prog = currentProgram
fm = prog.getFunctionManager()
rm = prog.getReferenceManager()
mem = prog.getMemory()
af = prog.getAddressFactory().getDefaultAddressSpace()

blocks = [b for b in mem.getBlocks() if b.isInitialized()]
print("SCAN blocks=%d" % len(blocks))
if not blocks:
    print("CONTROL FAILED: no initialized memory")
    raise SystemExit(1)

scanned = 0
blobs = {}
for blk in blocks:
    n = int(blk.getSize())
    buf = jarray.zeros(n, "b")
    mem.getBytes(blk.getStart(), buf)
    blobs[blk.getStart().getOffset()] = buf
    scanned += n
    print("  BLOCK %s 0x%08x size=%d" % (blk.getName(), blk.getStart().getOffset(), n))
print("SCAN total_bytes=%d" % scanned)

listing = prog.getListing()
n_insn = 0
it = listing.getInstructions(True)
while it.hasNext():
    it.next()
    n_insn += 1
print("STATE instructions=%d functions=%d" % (n_insn, fm.getFunctionCount()))

# Total references in the whole program: the decisive number.
n_ref = 0
rit = rm.getReferenceIterator(prog.getMinAddress())
while rit.hasNext():
    rit.next()
    n_ref += 1
print("STATE total_references=%d" % n_ref)

# Rebuild the assert-string set and its pointer slots, then report refs to each slot.
text_parts = []
for start, buf in blobs.items():
    text_parts.append((start, "".join([chr(buf[i] & 0xFF) for i in range(len(buf))])))


def find_slots():
    """Map string-start VA -> list of slot VAs holding a pointer to it."""
    out = {}
    for start, text in text_parts:
        for m in __import__("re").finditer(r"([A-Za-z_][A-Za-z_0-9]*\.cpp)\((\d+)\)", text):
            back = m.start()
            while back > 0 and text[back - 1] not in ("\x00", "\n") and ord(text[back - 1]) >= 32:
                back -= 1
            sva = start + back
            hits = []
            packed = struct.pack("<I", sva)
            i = 0
            while True:
                i = text.find(packed, i)
                if i < 0:
                    break
                if i % 4 == 0:
                    hits.append(start + i)
                i += 1
            if hits:
                out[sva] = (m.group(1), int(m.group(2)), hits)
    return out


slots = find_slots()
print("SCAN strings_with_pointer_slots=%d slots_total=%d"
      % (len(slots), sum(len(v[2]) for v in slots.values())))

ref_slots = 0
ref_total = 0
examples = []
for sva in sorted(slots):
    for slot in slots[sva][2]:
        try:
            a = af.getAddress(slot)
        except Exception:
            continue
        if a is None:
            continue
        rs = list(rm.getReferencesTo(a))
        if rs:
            ref_slots += 1
            ref_total += len(rs)
            if len(examples) < 8:
                for r in rs:
                    f = fm.getFunctionContaining(r.getFromAddress())
                    examples.append("0x%08x <- 0x%08x %s %s"
                                    % (slot, r.getFromAddress().getOffset(),
                                       r.getReferenceType(), f.getName() if f else "?"))
print("MATCH slots_with_code_refs=%d refs=%d" % (ref_slots, ref_total))
for e in examples:
    print("  " + e)

# CONTROL: a known-good string must be present in the image. The rest of the attribution work is
# meaningless if this fails, and a tool that reports "matched 0" here is repeating the exact bug
# that was just fixed.
kankyo = [s for s in slots.values() if s[0] == "z_kankyo.cpp"]
print("CONTROL z_kankyo.cpp strings_with_slots=%d" % len(kankyo))
if not kankyo:
    print("CONTROL FAILED: z_kankyo.cpp not found in a %d-byte image" % scanned)
    raise SystemExit(1)
print("CONTROL OK")
