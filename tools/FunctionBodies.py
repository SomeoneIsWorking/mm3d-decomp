# -*- coding: utf-8 -*-
#@runtime Jython
# Two jobs, both about not trusting a function's single `size`:
#
#  1. Dump every function's REAL body ranges to function_bodies.csv. `functions.csv` records one
#     `size` per function, and this image's functions have DISJOINT bodies (2 to 10 ranges each), so
#     [entry, entry+size) is NOT the body. Any verifier that trusts the CSV's size column invents
#     contradictions, and any reader who checks an attribution against `size` alone will wrongly
#     call a correct attribution wrong. This file is what makes the check possible.
#  2. Settle the 6 claims that a flat size-based check flagged, by asking Ghidra's own model.
#
# The disputed claim set is fixed below: each was flagged by scratch/mm3d_attr/verify_rows.py.
import os

import jarray

prog = currentProgram
fm = prog.getFunctionManager()
af = prog.getAddressFactory().getDefaultAddressSpace()

_root = None
_here = os.path.abspath(os.getcwd())
for _ in range(6):
    if os.path.isdir(os.path.join(_here, "mm3d-decomp", "build", "decomp")):
        _root = _here
        break
    parent = os.path.dirname(_here)
    if parent == _here:
        break
    _here = parent
if _root is None:
    raise RuntimeError("cannot locate the zelda3d checkout")
out_path = os.environ.get("MM3D_BODIES_OUT") or os.path.join(
    _root, "mm3d-decomp", "build", "decomp", "function_bodies.csv")

# (function entry claimed, address the evidence says references the pool slot)
CLAIMS = [
    (0x00138ec4, 0x001582d4, "EnemyBasicEffectContainer.cpp"),
    (0x0014eeac, 0x00168224, "z_effect_soft_sprite.cpp/FragmentEffectContainer.cpp"),
    (0x0014eeac, 0x0016824c, "z_effect_soft_sprite.cpp/FragmentEffectContainer.cpp"),
    (0x0015141c, 0x0012cf4c, "Package.cpp"),
    (0x003c8200, 0x004f902c, "z_eff_blure.cpp"),
    (0x005ef1ac, 0x005ef1c0, "MajoraEffect.cpp"),
    (0x00204640, 0x00204970, "z_oceff_storm.cpp (DATA ref, non-LDR)"),
]

# ---- 1. dump real body ranges -------------------------------------------------
fns = fm.getFunctions(True)
n_ranges = 0
n_multi = 0
rows = []
while fns.hasNext():
    f = fns.next()
    body = f.getBody()
    it = body.getAddressRanges(True)
    ranges = []
    while it.hasNext():
        r = it.next()
        ranges.append((r.getMinAddress().getOffset(), r.getMaxAddress().getOffset()))
    n_ranges += len(ranges)
    if len(ranges) > 1:
        n_multi += 1
    for (a, b) in ranges:
        rows.append((f.getEntryPoint().getOffset(), f.getName(), a, b))
rows.sort()
with open(out_path, "w") as fp:
    fp.write("fn_entry,fn_name,range_start,range_end\n")
    for entry, name, a, b in rows:
        fp.write("0x%08x,%s,0x%08x,0x%08x\n" % (entry, name, a, b))
print("BODIES functions=%d ranges=%d multi_range_functions=%d"
      % (fm.getFunctionCount(), n_ranges, n_multi))
print("BODIES wrote %s" % out_path)

# ---- 2. settle the flagged claims --------------------------------------------

for entry, addr, label in CLAIMS:
    f = fm.getFunctionAt(af.getAddress(entry))
    print("=" * 70)
    print("entry 0x%08x  query 0x%08x  [%s]" % (entry, addr, label))
    if f is None:
        print("  NO FUNCTION at entry")
        continue
    body = f.getBody()
    # AddressSetView -> iterate AddressRange
    it = body.getAddressRanges(True)
    n = 0
    contains = None
    minr = None
    maxr = None
    while it.hasNext():
        r = it.next()
        n += 1
        if minr is None or r.getMinAddress().compareTo(minr) < 0:
            minr = r.getMinAddress()
        if maxr is None or r.getMaxAddress().compareTo(maxr) > 0:
            maxr = r.getMaxAddress()
        if r.getMinAddress().getOffset() <= addr <= r.getMaxAddress().getOffset():
            contains = r
    print("  body ranges=%d  span 0x%08x..0x%08x  (getSize=%d)"
          % (n, minr.getOffset(), maxr.getOffset(), f.getBody().getNumAddresses()))
    if contains is not None:
        print("  VERDICT: 0x%08x IS in the body of 0x%08x (range 0x%08x..0x%08x)"
              % (addr, entry, contains.getMinAddress().getOffset(), contains.getMaxAddress().getOffset()))
    else:
        print("  VERDICT: 0x%08x is NOT in the body of 0x%08x" % (addr, entry))
    # What does Ghidra think contains the query address?
    g = fm.getFunctionContaining(af.getAddress(addr))
    print("  getFunctionContaining(0x%08x) = %s"
          % (addr, ("0x%08x" % g.getEntryPoint().getOffset()) if g else "None"))
