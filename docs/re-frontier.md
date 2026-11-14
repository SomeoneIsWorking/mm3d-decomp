# RE Frontier — the ordered RE dependency chain toward a faithful port

Tracked by `tools/re_frontier.py` (consult it FIRST; update it in the SAME commit
that changes a step). This is the fine-grained companion to `docs/codemap.md`:
the codemap says *what subsystem exists*, this says *which ordered RE step is
real reverse-engineering vs a hack that jumped ahead*.

**Hard rule (no hacks / no fallbacks):** a `⛔ hack` status is DEBT, never an
acceptable resting state. It marks a shortcut standing in for absent RE and MUST
be removed as its real mechanism lands. `re_frontier.py hacks` is the debt list;
`re_frontier.py next` tells you the next RE-ready step.

**`re-verified` MEANS FAITHFUL to the real target — not "the mechanism runs."** A
step is `re-verified` only when its OUTPUT matches the real game/binary (look /
sound / behavior) on real data. An internal trace ("bytecode reached the call
site", "N rows attached") is a mechanism check, NOT faithfulness — if it runs but
the result doesn't match the real target, it is `re-partial` with the
faithfulness gap named. The user observes the running system; that observation
overrides any internal trace.

**Fail fast & loud:** a failure must surface loudly, never silently fall back —
unless the fallback IS intended behavior of the real target being reproduced.

Statuses: ✅ re-verified · 🟡 re-partial (honest gap) · 🔬 in-progress ·
⛔ hack (debt, must remove) · ⬜ todo · ➖ skip-by-design · ✍ authored · ⏸ blocked (computed).

<!-- Entries are `## <area>` sections holding `### <id> — <title>` headings, each
     followed by `- <field>: <value>` lines. Prose ANYWHERE in this file — before,
     between or inside entries — is yours: tools/re_frontier.py edits only the
     field lines it is told to change and copies everything else through byte for
     byte, refusing the write if anything else would be lost. -->

## cutscene

### cutscene.interpreter — Cutscene handlers and Cutscene_ProcessCommands
- status: re-verified
- deps: 
- evidence: z3d-mods Start skip: narration and Lost Woods scripts stepped to their end frame leave CommonData start/scene/SaveData identical to watching
- where: docs/cutscene.md
- gap: 
- notes: 

### cutscene.script — .jdb script layout and command sizes
- status: re-verified
- deps: cutscene.interpreter
- evidence: all 334 scripts of the USA dump walk to the next script's magic; z3d-mods reads the held text entry from it in climia_raiders.jdb
- where: docs/cutscene.md, include/z3D.h
- gap: 
- notes: 

### cutscene.textbox — Message_GetState and Message_CloseTextbox in scripts
- status: re-verified
- deps: cutscene.script
- evidence: narration skip closes every box and lands in lw_meetstk.jdb; climia_raiders.jdb stops at "Do you understand?" and Yes and No land as watching does
- where: docs/cutscene.md
- gap: 
- notes: MessageContext is unnamed

### ui.screen — which touch screen is up
- status: re-partial
- deps: 
- evidence: gUiScreenContext.activeScreen equals gUiScreens[1] in play and gUiScreens[4] with Items open, [0] in the opening narration, [2] with the Bombers' Notebook open, [3] [5] [6] [7] opened by touch (live reads)
- where: docs/ui.md
- gap: the word after activeScreen is not checked
- notes: 

### ui.hud_visibility — how much of the HUD shows
- status: re-partial
- deps: 
- evidence: CommonData.hudVisibility reads 50 in play, 1 in the opening narration, 2 on South Clock Town's title card and cutscene (live reads)
- where: docs/ui.md
- gap: only those three values seen; the writer is not decompiled
- notes: 

### items.buttons — item buttons and their inventory slots
- status: re-verified
- deps: 
- evidence: X on an item in the Items screen writes its id to buttonItems[0][2] and its slot to buttonSlots[0][2]; Deku, Goron and Zora draw and assign row 0 too, and the game stores nothing to buttonSlots[1..3] in any form (write watch, z3d-mods run mm-forms2)
- where: docs/items.md, include/z3D.h
- gap: 
- notes: z3d-mods' second item page keeps four slots in buttonSlots[1][1..4]

### save.write — the routine that writes a file
- status: re-verified
- deps: items.buttons
- evidence: Play_SaveAtStatue hooked at its entry; a save at South Clock Town's owl statue writes save0.bin with the equipment as RAM held it, and the file loads in the game without the hook (z3d-mods runs mm-sv-held, mm-sv-rel, mm-ld-plain)
- where: docs/save.md, symbols/functions.csv
- gap: 
- notes: the writer object at PlayState + 0x3BEC and the job it queues are unnamed

### actors.player — the actor lists, the player's position and the view
- status: re-verified
- deps: none
- evidence: Actor_UpdateAll (0x174640) walks ctx + 0x14 + category * 0xC and copies +0x24 to +0x10C; live in South Clock Town the first actor of category 2 has id 0, home and world (-281, 0, -700), and a position written to home, world and prevPos moves Link; z3d-mods' walk step steers him by PlayState's view eye and look-at (+0x220, +0x22C)
- where: docs/actors.md
- gap: the rest of Actor (bgCheckFlags, floor height, shape) and the Player fields past it; the camera structures behind the view

### collision.budget — what BgCheck_Allocate gives a scene
- status: re-partial
- deps: none
- evidence: disassembly of BgCheck_Allocate (0x29B738) from scene command 0x03 (0x48ABD0), its three tables and StaticLookup_AddPolyToSSList (0x43A950); the list length the formula gives is the one read live in South Clock Town (57319 with 1491 triangles); every ROM scene's triangle and cell pairs fit its list (z3d-mods `bgcheck.py`)
- where: docs/formats/scene_files.md, include/z3D.h, symbols/functions.csv
- gap: BgCheck_InitializeStaticLookup's triangle and cell test is not decompiled (z3d-mods counts the pairs that touch); a scene past its list was not run; the moving collision's lists are unread
- notes: 
