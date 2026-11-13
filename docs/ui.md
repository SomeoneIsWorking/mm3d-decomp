# Touch screen UI

The touch screen shows one screen object at a time. `gUiScreens` (0x656B00) holds eight pointers
to them, set once the game has made its UI, and `gUiScreenContext.activeScreen` (0x72F5BC + 8)
points at the one that is up.

| Index | Screen | Checked |
|---|---|---|
| 0 | Black: the touch screen is blank | live: the opening narration (`legend.jdb`) |
| 1 | Main: hearts, rupees, View, Gear, the item buttons, Masks/Map/Items tabs | live: South Clock Town, in play and during a cutscene |
| 3 | Gear | live: a touch on Gear |
| 4 | Items | live: Select in South Clock Town |
| 5 | Map: the map itself is on the top screen | live: a touch on Map |
| 6 | Masks | live: a touch on Masks |
| 7 | Ocarina: "Play your instrument" | live: a touch on the ocarina button |

On the title screen `activeScreen` is 0x6F7FB4, which is not in the table. Entry 2 is not checked. Project Restoration (GPL, evidence only) names the table's
order Black, Main, Schedule, Gear, Items, Map, Masks, Ocarina, and the word after `activeScreen`
the screen being changed to.

Live values (USA 1.0 layout under Project Restoration): the table reads 0x656AFC, 0x6F694C,
0x6F6B3C, 0x6F4130, 0x6F42D8, 0x6F45B8, 0x6F660C, 0x6F72F4; `activeScreen` is 0x6F694C in play and
0x6F42D8 with the Items screen open.

## HUD visibility

`gCommonData.hudVisibility` (+0x1374C) says how much of the HUD shows, with the N64 game's
values: 50 (`HUD_VISIBILITY_ALL`) in play, 1 while the touch screen is blank (the opening
narration) and 2 while the main touch screen is dimmed (an area's title card on arrival and the
cutscene after it, South Clock Town). `nextHudVisibility` (+0x1374A) holds the new value for a
frame when a change is asked for (50 on the frame the cutscene ended) and the word at +0x1374E
counts (11, then 2, then 9 in the same run). Other values have not been seen.

## Main screen buttons

Touch targets on the main screen, in its 320x240 pixels (read from frames and pressed live):
View around (27, 25), Gear (30, 121), the ocarina button (25, 212), Masks (95, 228), Map
(160, 228), Items around (230, 228).
