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
- evidence: gUiScreenContext.activeScreen equals gUiScreens[1] in play and gUiScreens[4] with Items open, [0] in the opening narration, [3] [5] [6] [7] opened by touch (live reads)
- where: docs/ui.md
- gap: entry 2 and the word after activeScreen are not checked
- notes: 

### ui.hud_visibility — how much of the HUD shows
- status: re-partial
- deps: 
- evidence: CommonData.hudVisibility reads 50 in play, 1 in the opening narration, 2 on South Clock Town's title card and cutscene (live reads)
- where: docs/ui.md
- gap: only those three values seen; the writer is not decompiled
- notes: 

### items.buttons — item buttons and their inventory slots
- status: re-partial
- deps: 
- evidence: X on an item in the Items screen writes its id to buttonItems[0][2] and its slot to buttonSlots[0][2]; a byte written to row 0 shows on the HUD the next frame, rows 1 to 3 show nothing as human (live reads and frames, South Clock Town)
- where: docs/items.md, include/z3D.h
- gap: which row Deku, Goron and Zora read for Y, X, I and II; whether rows 1 to 3 are read at all beyond their B byte
- notes: z3d-mods' second item page keeps four slots in buttonSlots[1][1..4] on that assumption

### save.write — the routine that writes a file
- status: hack
- deps: items.buttons
- evidence: none live; no save has been made on the harness (the South Clock Town owl statue gives no prompt after warp 0xD890)
- where: docs/items.md
- gap: the writer is not found. Leads from the code: 0x60415C is a state handler that calls 0x1AF034, 0x1C48AC, 0x1C92A8 and 0x1C9F20 and then copies SaveData (0x1A88 bytes) to gCommonData + 0x1A90; 0x1AFCC0 copies it back; 0x15E870 fills a new file's player, equipment and inventory from defaults
- notes: z3d-mods puts the first item page back when a text box opens instead of hooking the writer
