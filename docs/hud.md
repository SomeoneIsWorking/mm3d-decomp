# HUD

What each piece of the game's HUD reads, for a HUD drawn from the game's state, and what draws the
game's own. Addresses are the USA 1.0 layout under Project Restoration; `SaveData` is at 0x7751E0
(`gCommonData` + 8). Runs are z3d-mods harness runs (`scratch/runs/<name>/`), South Clock Town's
owl statue room, a fresh file; "live" means the value was written and the game's HUD looked at in
the frame.

## What each element reads

| Element | Reads | Proven |
|---|---|---|
| Heart containers | `SaveData.healthCapacity` (+0x132), 0x10 a heart | live: 0xA0 draws ten hearts (mmre-save1, max10) |
| Filled hearts | `SaveData.health` (+0x134), 0x10 a heart | live: 0x10 leaves one of three red (mmre-save1, health1); 0x80 of 0xA0, eight of ten |
| Magic meter shown | `SaveData.magicAcquired` (+0x13E) | live: 1 draws the meter; the capacity word and +0x136 alone do not (mmre-hud3, m_cap, m_acq, m_lvl) |
| Magic meter length | `SaveData.doubleMagicAcquired` (+0x13F) | live: 1 draws the meter twice as long (mmre-hud4, dbl) |
| Magic fill | `SaveData.magic` (+0x137) | live: 0x30 fills the single meter, 0x18 half of it (mmre-hud2, magic1, ammo) |
| Rupee count | `SaveData.rupees` (+0x138) | live: 123, 999 (mmre-save1, rupees123; mmre-hud2, r999) |
| Wallet | `SaveData.upgrades` (+0x1EC) bits 12 and 13 | live: wallet 0 draws a green gem, 99 in green (full); wallet 1 a blue gem, 99 and 199 in white, 200 in green (mmre-hud3, r99w0, r99w1, r199w1, r200w1) |
| Item on a button | `SaveData.equipment.buttonItems[0]` (+0x14A): B, Y, X, I, II | live, docs/items.md |
| Item icon | `sItemIconFrames[item id]` (0x6562F0), below | live: ids 1, 2, 6, 7, 8, 9, 0xA, 0xC, 0xD, 0x13 on I and II draw the bow, fire arrow, bomb, bombchu, stick, nut, beans, powder keg, pictograph box and red potion (mmre-hud2 ammo, mmre-hud3 ammo_*) |
| Ammo count | `SaveData.ammo[item id]` (+0x1B0 + id) | live: +0x1A4.. filled with 1..24; the bow draws 14, bomb 19, bombchu 20, stick 21, nut 22, beans 23 (mmre-hud2 ammo, mmre-hud3 ammo_7_8, ammo_9_a). The fire arrow draws the bow's count. A count at its capacity is green |
| Button dimmed | `gCommonData.buttonStatus[button]` (+0x13740), 0 enabled, 0xFF disabled | seen once: the powder keg on I indoors is drawn grey and `buttonStatus[3]` reads 0xFF, the bomb on II is not and reads 0 (mmre-hud4, talk). The game writes entries 0 to 4, 6 and 7 every frame, so a write does not hold |
| Small keys | `SaveData.dungeonKeys[dungeon]` (+0x1FE, s8, -1 none), by `DUNGEON_INDEX_*`; the dungeon by `PlayState.sceneNum`, Stone Tower by both its scenes | live: 3, 5, 7, 9 written in Woodfall Temple; its Map screen shows 3 keys, Great Bay Temple's 7 (mmkeys5). The scenes read 0x1B, 0x21, 0x49, 0x16, 0x18 after warps 0x3000, 0x3C00, 0x8C00, 0x2600, 0x2A00 (mmkeys2) |
| Clock digits, marker | `SaveData.time` (+0x18) | live: 0x8000 reads 12:02 with the marker mid-day (mmre-hud2, noon) |
| Clock's day | `SaveData.day` (+0xC) | live: 2 moves the marker to the second third of the bar (mmre-hud2, day2) |
| A button label | `PlayState.aButtonDoAction` (+0x864A, u16), below | live: `PlayActionIcon.textNum`, its copy, against the game's own word in the frame (hud-mm-words) |

The HUD reads health, rupees and the button items as it draws: no counter animates between the
write and the next frame. A fresh file reads `healthCapacity` 0x30, `health` 0x30, `magic` 0x30,
`rupees` 0, `upgrades` 0x00120000.

Not found: the magic capacity (the word at `gCommonData` + 0x368A reads 0x30 and is written back by
the game; the fill of a double meter was not measured), `SaveData` + 0x136 (no effect seen), the
powder keg's count (not in `ammo`).

## Writing a button's item by hand
`equipment.buttonItems[0]` is what the HUD and a button's use read, and `buttonSlots[0]` the
inventory slot behind each. A byte written to `buttonItems` alone draws at once, but nothing knows
its slot: z3d-mods' chord trade moves slots, so after one press and release of the chord the
button is empty (hud-mmlook3: X and Y empty after the release). Write both, or assign in the
Items screen: Select opens it with the cursor on the first item, and Y or X puts the item under
the cursor on that button (hud-mmlive3).

## Ammo and its capacity
`Inventory_ChangeAmmo(item, change)` (0x20E894) adds to an item's count
(`Inventory_GetAmmo` 0x224EF8, `Inventory_SetAmmo` 0x21D440: `SaveData.ammo[gItemSlots[item]]`,
`gItemSlots` 0x626CDC, where items 0 to 15 are their own slot) and then clamps it to 0 and to the
capacity of the item's upgrade: the bow's is the quiver (`UPGRADE_QUIVER` 0), bombs' and
bombchus' the bomb bag (1), sticks' 6 and nuts' 7. The capacity is
`gUpgradeCapacities[upgrade][(SaveData.upgrades & gUpgradeMasks[upgrade]) >> gUpgradeShifts[upgrade]]`.
Beans (item 0xA) are not clamped and the powder keg (0xC) is kept at 0 or 1.

| Upgrade | Mask | Shift | Capacities (u16, levels 0 to 3) |
|---|---|---|---|
| 0 quiver | 0x7 | 0 | 0, 30, 40, 50 |
| 1 bomb bag | 0x38 | 3 | 0, 20, 30, 40 |
| 2 | 0x1C0 | 6 | 0, 0, 0, 0 |
| 3 | 0xE00 | 9 | 0, 0, 0, 0 |
| 4 wallet | 0x3000 | 12 | 99, 200, 500, 500 |
| 5 | 0x1C000 | 14 | 0, 30, 40, 50 |
| 6 sticks | 0xE0000 | 17 | 0, 10, 20, 30 |
| 7 nuts | 0x700000 | 20 | 0, 20, 30, 40 |

`gUpgradeMasks` 0x626D3C, `gUpgradeShifts` 0x626C34, `gUpgradeCapacities` 0x626D60; read live.
A count written into a file without the item's bag is therefore 0 after one use. Live (hud-mm-bomb):
bombs written as 10 with no bomb bag, one bomb pulled: a write watch on the count sees 9 from
0x21D440, then 0 from 0x20E9D8. With the bag's field at 1 the same bomb leaves 19 of 20, and an
arrow 29 of 30 with the quiver's at 1 (hud-mmlive3).

## The A button's word
`PlayActionIcon_Update(icon, play)` (0x5F9D04) runs the A button: it copies
`PlayState.aButtonDoAction` into `textNum` when the change's animation has played
(`changeState`), fades the icon toward `PlayState.aButtonAlpha` and shows the word's pane. No word
is shown for `DO_ACTION_NONE` (10) or a number above 0x29 other than 0x30 to 0x33. With the A
button's widget hidden (below) the copy stops: `textNum` stays at its last value, so read
`aButtonDoAction` (hud-mm-hide: 10 in every state).

The number is the word's cell in `hud_patrs00_action_text.ctxb`: cells of 64x18 pixels from
(0, 93), nine to a column, counted down each column. Seen against the game's own word
(hud-mm-words): 3 Return (the bow aimed), 12 Drop (a bomb held), 15 Speak (the shop's counter),
17 Grab (beside a thrown bomb), 19 Put Away (after aiming), 10 nothing. The sheet's cells: 0
Attack, Check, Barrier, Return, Open, Jump, Select, Dive, Faster; 9 Throw, Roll, Climb, Drop,
Down, Save, Speak, Next, Grab; 18 Cancel, Put Away, Reel, Info, Soar, Snap, Explode, Dance,
March; 27 Curl, Surface, Swim, Punch, Pound, Hook, Shoot, Snap, Proceed; 36 Dive, Stop
(`DO_ACTION_WORDS` 38). Numbers 27 to 34 go through a second pane of the icon; what 0x30 to
0x33 draw was not seen.

## Item icons

`layout/Joker.Main.gar/icon_item_menu00.ctxb` is one 512x512 sheet. Frames 0 to 107 are the item
and mask icons, 42x42 pixels, twelve a row from the top left (frame n at column n % 12, row n / 12);
frames 108 to 179 are the notebook's faces, 32x32, sixteen a row below them. `ItemIcon.mfl`'s
`item_icon_ani` steps the icon pane's texture origin once per frame number.

`sItemIconFrames` (0x6562F0, one byte per item id, 0xFF none) gives an item's frame: ids 0 to 4 are
frames 0 to 4, 6 to 0xA frames 5 to 9, 0xC to 0x10 frames 0xA to 0xE, 0x12 on frame 0xF on; ids 5,
0xB and 0x11 have none. The table read live equals the image's (mmre-hud2).

Other HUD art: `layout/Joker.Main.Play.gar/menu_top_parts00.ctxb`, and per language
`layout/<language>/Joker.Main.Play.gar/hud_patrs00_action_text.ctxb` (512x256: the action labels,
hearts, rupee gems, the touch buttons). `Play.mfpk` in `layout/Joker.Main.Play.gar` names that
sheet as the bundle's texture, and `TouchPanel.mfl` in it has the panes `icon_rupy`, `icon_key`,
`num_rupy`, `num_key`, `heart00` to `heart19` and the animation `rupy_color_change_anim`: the
touch screen's rupee, key and hearts are cells of this sheet, and the gem's colour is an
animation's frame. Cells in the sheet's pixels, measured on the decoded sheet (the `.mfl`'s own
cell table was not parsed):

| Art | Cell (x, y, w, h) |
|---|---|
| Rupee: red, blue, green | 456, 23 / 41 / 60, 18, 18 |
| Small key | 456, 96, 22, 22 |
| Heart, plain: full, three quarters, half, a quarter, empty | 483, 3 + 16n, 10, 10 for n = 0 to 4 |
| Heart with a white rim, the same five | 499, 3 + 16n, 10, 10 |

The wallet picks the gem: green with `upgrades`' wallet bits 0 and blue with 1, seen (table
above); red for 2 is the remaining cell and was not run. Henriko's pack replaces the sheet whole
(4096x2048, found by hash).

## Minimap

`MainScreen_Draw` calls `MainScreen_DrawMinimap` (0x2A326C, from 0x59B348) while the play
state's +0x13D is 4, and it calls `Minimap_Draw` (0x36DEBC). That fills the quad batches
`gMinimapQuads[0]`, `[1]` (the room's layers) and `gMinimapMarkerQuads` (the player's arrow and
the markers) with screen-space quads and queues them on `gLayoutDrawManager`'s
`LAYOUT_DRAW_QUEUE_TOUCH`; the frame draws each queue in ascending priority. A batch moved to
`LAYOUT_DRAW_QUEUE_TOP` after the call, its positions and sizes rescaled, draws on the top screen
A quad's extent is its four `corners` times `sizes[i]`, turned by the first three floats of each
row of `rotations[i]`, plus `positions[i]` (z3d-mods `patch/mm3d/minimap.cpp` fits the rooms' extent to a box; live: South Clock Town, Termina Field and Woodfall Temple, mmmap3, mmmap7).

The map data loads in every scene that has one (the header at `*0x6890F4`, written by 0x4BD4C8 and
0x4BD504 on a scene change, mmmap5); the room index is the state's +0x54. The rooms are drawn only
while `Inventory_IsMapVisible(sceneNum)` (0x5475A8: `SaveData.scenesVisible`, Tingle's maps) or
0x1CF20C (a dungeon) holds: a new file shows nothing in Termina Field until the scene's bit is set
(mmmap4, mmmap7). `WEEK_EVENT_REGION_MAPS` is the Map screen's loupe and does not show it (mmmap3).

## What draws the game's HUD

Layouts are trees of widgets (`UiLayout`, `UiWidget`; the layout matches Project Restoration's
`game/ui.h`, GPL, evidence only, checked here on live memory). `gUiCommonLayouts` (0x6B7B8C) holds
the shared ones: [0] `Joker.Main.Play.TouchPanel`, [1] `BackGround`, [2] `Joker.Main.Play.Hud`
(`PlayHud`). `LayoutDrawManager_Draw(manager, layout, screen, order)` (0x17EC58) queues a layout
for this frame.

| Piece | Owner | Hides it |
|---|---|---|
| Top screen: clock, A and B buttons, chat alert | `PlayHud_Draw` (0x195478), called from 0x1707CC with `PlayState` + 0xCCC4; queues the layout while `PlayHud.opacity` > 0 | live: the root widget hidden (below) leaves the top screen without clock or A (mmre-hud7, play_hidden). `opacity` is written back every frame |
| A button alone | the widget `PlayHud.aActionButton` (+0x180) | live: hidden, the clock stays (mmre-hud5, hideA2) |
| Clock alone | not found: hiding the group at `PlayHud` + 0x208 by flags or alpha changes nothing (mmre-hud5, mmre-hud6) | |
| Touch screen's main HUD | `MainScreen_Draw` (0x59B27C, `gUiScreens[1]`'s vtable slot 9) queues the bottom background, `BackGround` and the touch panel | live: the touch panel's root widget hidden leaves the background alone (mmre-hud6, touchRoot; mmre-hud7) |

Hiding a widget: write `flags` (+0x84) = 0x0FFFFF0E and `activeFlags` (+0x88) = 0x0FFDFF00. For a
layout's root that is the layout + 0x8C and + 0x90. Clearing bit 0 alone does nothing, and writing
the shown values back (0x0000000F, 0x0FFFFF00) does not bring it back. The write holds through a
cutscene and the HUD's own fades.

`hudVisibility` (docs/ui.md) fades the clock and A and dims the touch buttons together; hearts and
rupees stay (1 written: mmre-hud2, hvcur1).

Not proven: a code patch. Returning at once from `PlayHud_Draw` or `MainScreen_Draw` is what the
decompiled functions call for, but bytes written over running code did not change the frame
(mmre-hud6), so neither was seen working. That dialog boxes (`Joker.Main.MessageWindow`, another
layout) stay with these hidden was not seen either: no box was open in a frame.
