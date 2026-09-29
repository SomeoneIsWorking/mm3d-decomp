#@runtime Jython
# Ghidra 12 runs headless scripts under PyGhidra, which this host does not have; without
# this header every script in this directory fails to load with "Python is not available",
# which is why MM3D had a fully built Ghidra project and zero decompiled output.
# -*- coding: utf-8 -*-
memory = currentProgram.getMemory()
blocks = list(memory.getBlocks())
print("blocks: %d" % len(blocks))
for b in blocks:
    print("  %s  [0x%x..0x%x]  size=0x%x  init=%s  exec=%s" %
          (b.getName(), b.getStart().getOffset(), b.getEnd().getOffset(),
           b.getSize(), b.isInitialized(), b.isExecute()))
