# -*- coding: utf-8 -*-
# Decompile specific functions to C and write to build/decomp/.
#
# Reads DECOMP_TARGETS env var (comma-separated hex VAs) OR falls back to a hardcoded
# list. For each VA, decompiles the containing function.
import os
from ghidra.app.decompiler import DecompInterface
from ghidra.util.task import ConsoleTaskMonitor

OUT = "<SOH3D_REPO>/scratch/mm3d-decomp/build/decomp"
if not os.path.isdir(OUT):
    os.makedirs(OUT)

fm = currentProgram.getFunctionManager()
af = currentProgram.getAddressFactory().getDefaultAddressSpace()
di = DecompInterface()
di.openProgram(currentProgram)
mon = ConsoleTaskMonitor()

env = os.environ.get("DECOMP_TARGETS", "").strip()
if env:
    targets = [int(x, 16) for x in env.split(",") if x.strip()]
else:
    targets = [0x005e2868]  # LzS-label xref anchor

for va in targets:
    addr = af.getAddress(va)
    f = fm.getFunctionContaining(addr)
    if not f:
        print("NO FUNCTION at 0x%x" % va)
        continue
    dres = di.decompileFunction(f, 60, mon)
    if dres and dres.decompileCompleted():
        c = dres.getDecompiledFunction().getC()
        path = os.path.join(OUT, "fn_0x%08x.c" % f.getEntryPoint().getOffset())
        with open(path, "w") as fp:
            fp.write("// Function at VA 0x%08x - %s\n" % (f.getEntryPoint().getOffset(), f.getName()))
            fp.write(c)
        print("wrote %s" % path)
    else:
        err = dres.getErrorMessage() if dres else "(no result)"
        print("FAIL 0x%x: %s" % (va, err))
