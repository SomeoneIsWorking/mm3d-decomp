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

### message.printer — control codes, the parser's elements and the printer that reveals them
- status: re-verified
- deps: 
- evidence: z3d-mods Quick Text: the printer's instantOn before each printing update shows a box whole in one update and a delay code still pauses (runs mm-qt-on, mm-qt-off, mm-qt-box); the code table decodes all 6152 US messages to their end code
- where: docs/message.md, include/z3D.h
- gap: the codes that insert names, numbers and times; the sound and colour arguments; the layout visitor's fields
- notes: 

### message.font — the GZFX font file and what draws its glyphs
- status: re-partial
- deps: 
- evidence: ltn16.gzf read and written back byte for byte (z3d-mods tools/z3dmods/gzf.py); sheet 0's bytes hash to the A4 texture Azahar dumps at a dialog (510A49A1A046A54B, run txt-dump2); a font drawn from an outline font prints from a texture pack's copies of its sheets (runs txt-mm-r1, txt-mm-r4)
- where: docs/formats/gzf.md
- gap: the function that draws a glyph; the header's 11 and 5; sheets 1 and 2 were not seen drawn
- notes: 

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
- notes: z3d-mods' item slots are kept in buttonSlots[1..3][1..4]

### items.screens — the Items and Masks screens' cursor and grids, the bottles' slots, and an item button pressed for the player
- status: re-partial
- deps: items.buttons, ui.screen
- evidence: live: the Items screen's cursor column and row, the item grid's slots, a bottle in slot 48 drawn in its cell, the bow used from I and a bomb from II through gTouchButtonsHeld and gTouchButtonsPressed written at Play_Update's entry (z3d-mods runs ctl-mm1, ctl-mm6); the rest read from the disassembly (0x5C1328, 0x1DB1C4, 0x2190FC)
- where: docs/items.md, include/z3D.h
- gap: the Masks screen and its grid were not opened; Y and X were not pressed this way; ItemScreen is named at four fields; the mask-off and put-away checks of the item button routine are read, not run
- notes: 

### items.ocarina — the Ocarina screen, the note input and the song table
- status: re-partial
- deps: items.screens
- evidence: live: the screen's page and song cursor, the list's song bytes and the song table dumped, the message object's ocarina mode in free play, the ocarina brought out by TOUCH_BUTTON_OCARINA and the Song of Time recognised from notes written to gPadInjected (z3d-mods runs ctl-mm3, ctl-mm4, ctl-mm7, ctl-mm8, ctl-mm9)
- where: docs/ocarina.md, include/z3D.h
- gap: the pad update and the song matcher are read, not decompiled; only the Song of Time was played; its question before the return to the first day was not seen in the file used
- notes: 

### save.write — the routine that writes a file
- status: re-verified
- deps: items.buttons
- evidence: Play_SaveAtStatue hooked at its entry; a save at South Clock Town's owl statue writes save0.bin with the equipment as RAM held it, and the file loads in the game without the hook (z3d-mods runs mm-sv-held, mm-sv-rel, mm-ld-plain)
- where: docs/save.md, symbols/functions.csv
- gap: 
- evidence: the writer (PlayState.saveWriter) and CommonData.entrance / statueEntrance / statueSave read live: a statue save made from our patch at each scene's entrance writes save0.bin with statueSave 1 and that entrance, the writer's job is freed after each of 29 writes, and the file loads at that entrance with the saved clock (z3d-mods runs mm-q-as1, mm-q-as3, inputtest autosave-mm3d)
- notes: the cycle save at 0x188270 (statueSave 0) is read, not run; the job's own type is unnamed

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

### hud.state — what the HUD reads
- status: re-partial
- deps: items.buttons
- evidence: health, heart containers, magic, rupees, the wallet bits, ammo by item id, time and day written live and read off the game's HUD; sItemIconFrames read live and matched against icon_item_menu00's sheet through item ids on the I and II buttons (z3d-mods runs mmre-save1, mmre-hud2 to mmre-hud4)
- where: docs/hud.md, include/z3D.h
- gap: magic capacity and the fill of a double meter; buttonStatus seen once, never written; the A label's text number to label; the minimap; the powder keg's count

### hud.draw — what draws the game's HUD
- status: re-partial
- deps: ui.screens
- evidence: PlayHud_Draw (0x195478) and MainScreen_Draw (0x59B27C) decompiled; PlayHud's root widget, its A button widget and the touch panel's root widget hidden live by their flags (mmre-hud5 to mmre-hud7)
- where: docs/hud.md, include/z3D.h, symbols/functions.csv
- gap: the clock's own widget; a code patch seen working; dialog boxes with the HUD hidden

## motion

### motion.look — what the first-person look reads of the gyroscope
- status: re-partial
- deps: actors.player
- evidence: Motion_Update, Player_UpdateLook and the SDK reader decompiled; in first person the reader's angle, gMotionState and focus.rot read live against a fed rate: 2.10 view degrees a degree of yaw, 1.46 of pitch; the accelerometer revise, zero play, zero drift and motionOff each switched live (z3d-mods runs gyro-mm2 to gyro-mm7)
- where: docs/motion.md, include/z3D.h, symbols/functions.csv
- gap: aimed items not run; what sets bit 1 of the look flags; the pad look's invert byte
- notes: 
