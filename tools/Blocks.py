# -*- coding: utf-8 -*-
memory = currentProgram.getMemory()
blocks = list(memory.getBlocks())
print("blocks: %d" % len(blocks))
for b in blocks:
    print("  %s  [0x%x..0x%x]  size=0x%x  init=%s  exec=%s" %
          (b.getName(), b.getStart().getOffset(), b.getEnd().getOffset(),
           b.getSize(), b.isInitialized(), b.isExecute()))
