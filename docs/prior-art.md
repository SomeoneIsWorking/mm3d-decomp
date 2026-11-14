# Prior art

Build: MM3D USA 1.0 layout (see the README). No public decompilation exists.

| Source | Licence | Build match | What we take |
|---|---|---|---|
| leoetlino/project-restoration v1.5.9 | GPL-2.0 | patches 1.0 and 1.1 (v110 rebuilds 1.1 into the 1.0 layout) | evidence only: struct names (`common_data.h`, `context.h`) |
| tgacquin/mm3d-dekui v1.1.0 | GPL-2.0 | USA 1.1; its minimap anchors match the 1.0 layout under Restoration v110 (0x59B344, 0x175C30, 0x36E294, 0x2A3290 read live) | evidence only: where the minimap's quads and draw queues are (docs/hud.md "Minimap") |
| Volpe34/MM3D-PC | GPL-3.0 | not checked | evidence only |
| Z3DR/mm3dr (MM3D Randomizer) | MIT, with permission for its Project Restoration code | not checked | names |
| yellows8/mm3d_re | none stated | not checked | save data notes, evidence only |
| zeldaret/mm (N64) | CC0-1.0 | engine ancestor | names (`CutsceneHandler_*`), checked against this build |
