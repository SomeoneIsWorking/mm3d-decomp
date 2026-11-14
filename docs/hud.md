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
| Clock digits, marker | `SaveData.time` (+0x18) | live: 0x8000 reads 12:02 with the marker mid-day (mmre-hud2, noon) |
| Clock's day | `SaveData.day` (+0xC) | live: 2 moves the marker to the second third of the bar (mmre-hud2, day2) |
| A button label | `PlayActionIcon.textNum` (+0x190) of `PlayHud.aActionIcon` | read only: 0x0A standing, 0x13 after an A press. The mapping to a label is not done |

The HUD reads health, rupees and the button items as it draws: no counter animates between the
write and the next frame. A fresh file reads `healthCapacity` 0x30, `health` 0x30, `magic` 0x30,
`rupees` 0, `upgrades` 0x00120000.

Not found: the magic capacity (the word at `gCommonData` + 0x368A reads 0x30 and is written back by
the game; the fill of a double meter was not measured), `SaveData` + 0x136 (no effect seen), the
powder keg's count (not in `ammo`), what decides the minimap.

## Item icons

`layout/Joker.Main.gar/icon_item_menu00.ctxb` is one 512x512 sheet. Frames 0 to 107 are the item
and mask icons, 42x42 pixels, twelve a row from the top left (frame n at column n % 12, row n / 12);
frames 108 to 179 are the notebook's faces, 32x32, sixteen a row below them. `ItemIcon.mfl`'s
`item_icon_ani` steps the icon pane's texture origin once per frame number.

`sItemIconFrames` (0x6562F0, one byte per item id, 0xFF none) gives an item's frame: ids 0 to 4 are
frames 0 to 4, 6 to 0xA frames 5 to 9, 0xC to 0x10 frames 0xA to 0xE, 0x12 on frame 0xF on; ids 5,
0xB and 0x11 have none. The table read live equals the image's (mmre-hud2).

Other HUD art: `layout/Joker.Main.Play.gar/menu_top_parts00.ctxb`, and per language
`layout/<language>/Joker.Main.Play.gar/hud_patrs00_action_text.ctxb` (the action labels, hearts,
rupee gems, the touch buttons).

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
