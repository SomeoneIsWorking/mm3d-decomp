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
- evidence: gUiScreenContext.activeScreen equals gUiScreens[1] in play and gUiScreens[4] with Items open and gUiScreens[0] in the opening narration (live reads)
- where: docs/ui.md
- gap: entries 2, 3, 5, 6, 7 and the word after activeScreen are not checked
- notes: 
