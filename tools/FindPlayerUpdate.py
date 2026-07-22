# -*- coding: utf-8 -*-
# Ghidra headless: decompile targeted VAs; force-create functions Ghidra missed.
# Env vars:
#   MM3D_TARGETS  = comma-separated hex VAs to decompile
#   MM3D_FORCE    = "1" to force-create missing functions (ARM mode, TMode=0)
import os, java.math.BigInteger as BigInteger
from ghidra.app.decompiler import DecompInterface
from ghidra.util.task import ConsoleTaskMonitor
from ghidra.app.cmd.function import CreateFunctionCmd
from ghidra.app.cmd.disassemble import ArmDisassembleCommand

# Output dir: $MM3D_DECOMP_OUT, else <repo>/build/decomp via $ZELDA3D_REPO.
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

OUT = _out_dir('/decomp')

fm = currentProgram.getFunctionManager()
af = currentProgram.getAddressFactory().getDefaultAddressSpace()
di = DecompInterface()
di.openProgram(currentProgram)
mon = ConsoleTaskMonitor()
FORCE = os.environ.get("MM3D_FORCE", "0") == "1"


def set_arm_mode(addr):
    tmode = currentProgram.getProgramContext().getRegister("TMode")
    if tmode is not None:
        try:
            currentProgram.getProgramContext().setValue(tmode, addr, addr, BigInteger.ZERO)
        except:
            pass


def force_create(addr):
    set_arm_mode(addr)
    cmd = ArmDisassembleCommand(addr, None, False)
    cmd.applyTo(currentProgram, mon)
    cmd2 = CreateFunctionCmd(addr)
    cmd2.applyTo(currentProgram, mon)


def decomp_va(va):
    addr = af.getAddress(va)
    f = fm.getFunctionContaining(addr)
    if not f and FORCE:
        print("force-creating fn at 0x%x" % va)
        force_create(addr)
        f = fm.getFunctionContaining(addr)
    if not f:
        return None, "no function at 0x%x" % va
    dres = di.decompileFunction(f, 60, mon)
    if not (dres and dres.decompileCompleted()):
        return f, "decompile failed"
    c = dres.getDecompiledFunction().getC()
    path = os.path.join(OUT, "fn_0x%08x.c" % f.getEntryPoint().getOffset())
    with open(path, "w") as fp:
        fp.write("// Function at VA 0x%08x - %s (size=%d)\n" % (
            f.getEntryPoint().getOffset(), f.getName(),
            f.getBody().getNumAddresses()))
        fp.write(c)
    return f, path


env = os.environ.get("MM3D_TARGETS", "").strip()
if not env:
    print("no MM3D_TARGETS supplied"); exit()
for tok in env.split(","):
    tok = tok.strip()
    if not tok: continue
    va = int(tok, 16)
    f, res = decomp_va(va)
    print("0x%x -> %s" % (va, res))
