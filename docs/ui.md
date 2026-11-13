# Touch screen UI

The touch screen shows one screen object at a time. `gUiScreens` (0x656B00) holds eight pointers
to them, set once the game has made its UI, and `gUiScreenContext.activeScreen` (0x72F5BC + 8)
points at the one that is up.

| Index | Screen | Checked |
|---|---|---|
| 1 | Main: hearts, rupees, View, Gear, the item buttons, Masks/Map/Items tabs | live: South Clock Town, in play and during a cutscene |
| 4 | Items | live: Select in South Clock Town |

On the title screen `activeScreen` is 0x6F7FB4, which is not in the table. The other entries are
not checked. Project Restoration (GPL, evidence only) names the table's
order Black, Main, Schedule, Gear, Items, Map, Masks, Ocarina, and the word after `activeScreen`
the screen being changed to.

Live values (USA 1.0 layout under Project Restoration): the table reads 0x656AFC, 0x6F694C,
0x6F6B3C, 0x6F4130, 0x6F42D8, 0x6F45B8, 0x6F660C, 0x6F72F4; `activeScreen` is 0x6F694C in play and
0x6F42D8 with the Items screen open.
