# Touch screen UI

The touch screen shows one screen object at a time. `gUiScreens` (0x656B00) holds eight pointers
to them, set once the game has made its UI, and `gUiScreenContext.activeScreen` (0x72F5BC + 8)
points at the one that is up.

| Index | Screen | Checked |
|---|---|---|
| 0 | Black: the touch screen is blank | live: the opening narration (`legend.jdb`) |
| 1 | Main: hearts, rupees, View, Gear, the item buttons, Masks/Map/Items tabs | live: South Clock Town, in play and during a cutscene |
| 2 | Bombers' Notebook ("Event Notes"): the list is on the top screen, the entry and its Return and Schedule buttons on the touch screen | live: Start with the notebook owned |
| 3 | Gear | live: a touch on Gear |
| 4 | Items | live: Select in South Clock Town |
| 5 | Map: the map itself is on the top screen | live: a touch on Map |
| 6 | Masks | live: a touch on Masks |
| 7 | Ocarina: "Play your instrument" | live: a touch on the ocarina button |

Outside play `activeScreen` points at screens that are not in the table: `gTitleUiScreen`
(0x6F7FB4, vtable 0x63A330) from the opening through PRESS START, and `gFileSelectUiScreen`
(0x6F79D4, vtable 0x63A550) at file select, its list of files and Return on the touch screen under
the top screen's "Select File" bar (z3d-mods run mmprobe). `gTitleUiScreen` is up through the whole
opening, before PRESS START shows: the word at +0x1F0 steps 4, 9, 0, 2, 0xE, 7, 0 through it
(z3d-mods run tstate) and is 0 both with PRESS START up and without it, so it is not the prompt's
state. Project Restoration (GPL,
evidence only) names the table's order Black, Main, Schedule, Gear, Items, Map, Masks, Ocarina, and
the word after `activeScreen` the screen being changed to.

## Title and file select

Each screen's draw (its vtable's tenth entry) queues its layouts with `LayoutDrawManager_Draw`
(0x17EC58: manager, layout, queue, order). `TitleScreen_Draw` (0x5A81EC) queues its touch
backdrop (+0x1C) on queue 4 and PRESS START (+0x08) on 5, the latter a tail call.
`FileSelectScreen_Draw` (0x5BA0DC) queues the top screen's background (+0x28) on 0, the plate of
the file under the cursor (+0x24) and the title bar, "Select File" with the clock (+0x2C), on 2, the
touch backdrop (+0x20) on 4, and on 5 the list (+0x1C: the files, a file's Start, Copy, Erase and
Options, Return) and the prompts (+0x30: "Saving...", the yes and no windows). The list layout
(vtable 0x63C7F4) holds its groups by pointer, Return at +0x6E4; the prompts' (vtable 0x63CA00) its
window at +0x3B4 and the black that dims the touch screen behind it at +0x3F4.

Which screen a queue draws on: `Graph_DrawTopScreen` (0x110A24) draws queues 0 to 3 into the top
screen's target through `LayoutDrawManager_DrawQueue` (0x126810: manager, queue, context), 0 before
the 3D and 1 to 3 after it; `Graph_DrawFrame` draws 4 (0x106CF4) and 5 (0x106E4C). A file select
layout moved to queue 0, 1, 2 or 3 drew on the top screen and to 4 or 5 on the touch screen; 6 and 7
drew nothing there (z3d-mods runs mmmove, the queue argument rewritten live). This does not fit
docs/hud.md's minimap, whose batches show on the top screen from queue 4.

A widget's place is its `translate` (+0x3C, from its parent's origin, y down; a root's from the
screen's top left) and `scale` (+0x48), the head of the 0x50-byte block Project Restoration (GPL,
evidence only) calls the widget's position, which ends with `flags` and `activeFlags`. The game
lays a widget out again only when a field's bit is set in `flags` (`UI_WIDGET_TRANSLATE_X` and the
rest), `activeFlags` holding the same bit while the field is at its default: written alone, a
translate moved nothing; with the bits, the list moved (mmroot). Touches are hit-tested through the
same matrices: with the list moved 40 to the right, a touch at (250, 100) chose the file drawn there
(fs7).

The top screen's target is 480x400, twice the screen's 240 lines: its framebuffer register
(0x11E) reads 0x118F200, and `Graph_DrawTopScreen` sets the viewport to 480 by 400 and the scissor
to (0, 0) to (479, 399), mode 3; the touch screen's pass sets 240 by 320 (the command list read
live, mmcmd). The game writes PICA registers itself as a value and a header at
`gPicaCommandNext` (0x6A3A88, bounded by `gPicaCommandEnd`), as at 0x146F04 and in the GL state
flush at 0x10BD30; a scissor written there around a queue's draw clips it (z3d-mods fs2, fs12).

File select builds its layouts in `FileSelectScreen_Init` (0x5BA3BC, its vtable's eighth entry at
0x63A56C), finding their widgets by name with `UiLayout_FindWidget` (0x13BE78: layout, name).
`FileSelectScreen_Update` (0x5BB448) runs the page that is up; its call at +0x580 runs the Start
page's, `FileSelectScreen_UpdateStart` (0x5B821C). `page` (+0x5BC) is the page shown, 0 the files,
1 the file's Start page, 2 Copy's target list, 3 Erase's prompt; `nextPage` (+0x5BD) changes first
and `page` follows when the slide ends, about 12 frames later (mmpage). On the Start page
`startChoice` (+0x5C8) is the button under the cursor: 0 Start, 1 Copy, 2 Options, 3 Erase, set by
the pad or a touch, and the cursor animation (the player at +0x5AC, its frame the choice plus one)
lights the button's glow in `cursor_g`. Copy and Erase share one, `cursor_copy_del_g`, which the
animation moves 104 to the right for Erase, the distance between the two buttons; its x does not
follow its translate, its y and scale do (mmmove). Each button's group (`btn_start_g` and the rest)
holds its touch rect on screen in its `bb_*` panes at +0x2C (left, top, right, bottom floats),
updated as it is drawn: natively Start 46..274 by 66..110, Copy 66..150 and Erase 170..254 by
118..156, Options 94..226 by 162..200, Return 0..58 by 202..240 in the list's 320 pixels. Moving a
group by its translate and scale moved its touch area with it (z3d-mods fs14, a click on Options).
The slide to the Start page moves the file rows (`plate_x_n`, `plate_y_n`, `plate_z_n` in
`null_plate_g`) by animation from x 14 to -306, and `start_g`'s matrix from 360 to 40; a widget's
matrix (+0xE0) is the one it was last drawn with, so a hidden group's is stale.

File select's Options screen is `gOptionsUiScreen` (0x6F7348, vtable 0x63A11C), built by
`OptionsScreen_Init` (0x5A3614, the vtable's eighth entry). `OptionsScreen_Draw` (0x5A31BC) queues
the top screen's background (+0x1C) on 0, the title bar, "Options" with the clock (+0x20), on 2
(its call at +0x140), the touch backdrop (+0x14) on 4, and on 5 the list (+0x10, its call at +0xA8:
the option plates on two pages of four, their Page 1 and Page 2 tabs, Return) and the cursor
(+0x18, its call at +0x100: the frame on the plate chosen). The hint for the plate chosen is
written into play's message box on the top screen. `choice` (+0x0A) is the plate chosen, 0 to 7
across both pages, and the cursor's root is put at `cursorPlaces[choice]` (+0x14C, a Vec3f each,
the plates' places filled by the build) by the function at 0x5A1E2C, so moving the places moves
the cursor with the plates. The list's widgets: the pages `page1_g` and `page2_g` and the tabs
`btn_page1_g` and `btn_page2_g` under `all`, beside `null_g`; Return is `btn_return_l`, a widget
with its own layout (+0x20) whose root carries it. The page change slides the pages by 320 and
swaps the tab rows between y 0 and 40 by animation, so those fields ignore writes; scaling `all`
and each of its children back by the inverse stretches the slide and keeps the parts' size
(z3d-mods opt5, opt6). Page 1 holds L-Targeting, Circle Pad Pro, Free Camera and Calibrate Circle
Pad Pro; page 2 First-Person Camera, Motion Controls, Swimming Controls and Adjust Volume.

The stylus is read by `Input_ReadTouch` (0x1161B4), whose call at +0x14 of
`TouchPanelReader_ReadLatest` (0x122678) fills a `TouchPanelStatus` (x, y, touched) on the stack
that it keeps in its input at +0x14; every touch the menus test comes from there (a touch's x,
scaled there, chose Options drawn past the touch screen's width; z3d-mods fs14).

`gUiScreenContext.nextScreen` (+0xC) is the screen to change to, null once the change is made.
Leaving the Map screen writes Main there (0x5932BC); Start in play writes the notebook's
(under Project Restoration, from its own code). The same write while the Map screen is up opens
the notebook from it, and B on the notebook then goes back to play (z3d-mods runs `gap-nb3`,
`gap-nb4`, a watch on the word). The Map screen itself does nothing with Start or Select (`gap-nb1`).

The notebook is owned when bit 18 of the quest word at `SaveData` + 0x1F0 is set (the N64 game's
`QUEST_BOMBERS_NOTEBOOK`): set by hand in a fresh file, Start opens the screen.

Live values (USA 1.0 layout under Project Restoration): the table reads 0x656AFC, 0x6F694C,
0x6F6B3C, 0x6F4130, 0x6F42D8, 0x6F45B8, 0x6F660C, 0x6F72F4; `activeScreen` is 0x6F694C in play and
0x6F42D8 with the Items screen open.

## Map screen

`MenuMapState.cpp` (0x594000 to 0x598000): 0x5975AC opens the screen, 0x594400 reads its input.
The screen keeps its touch-screen map at +0x18, the loupe's pane at +0x30 and the loupe's position
at +0x75C/+0x760 (floats), which the Circle Pad moves. The loupe shows only while the current
region's map is owned (+0x78C): bit n of `weekEventReg[0x23]` (`WEEK_EVENT_REGION_MAPS`), n from
the region's entry in the table at 0x620C18 (0x2301 to 0x2320, six regions). Seen: X zooms the top
screen into the player's region ("Zoom In", then "Zoom Out"), A switches the touch-screen map
between the loupe and its panning arrows, B leaves (z3d-mods runs `gap-zm2`, `gap-zm3`). Without the
region's map there is no loupe and X does nothing (`gap-zm1`).

## HUD visibility

`gCommonData.hudVisibility` (+0x1374C) says how much of the HUD shows, with the N64 game's
values: 50 (`HUD_VISIBILITY_ALL`) in play, 1 while the touch screen is blank (the opening
narration) and 2 while the main touch screen is dimmed (an area's title card on arrival and the
cutscene after it, South Clock Town, and all the while the Ocarina screen is up). `nextHudVisibility` (+0x1374A) holds the new value for a
frame when a change is asked for (50 on the frame the cutscene ended) and the word at +0x1374E
counts (11, then 2, then 9 in the same run). Other values have not been seen.

What each value fades and the layouts behind the HUD: docs/hud.md.

## Main screen buttons

Touch targets on the main screen, in its 320x240 pixels (read from frames and pressed live):
View around (27, 25), Gear (30, 121), the ocarina button (25, 212), Masks (95, 228), Map
(160, 228), Items around (230, 228).
