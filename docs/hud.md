# HUD

What each piece of the game's HUD reads, for a HUD drawn from the game's state. Addresses are the
USA 1.0 layout under Project Restoration; `SaveData` is at 0x7751E0 (`gCommonData` + 8).

| Element | Reads | Proven |
|---|---|---|
| Heart containers | `SaveData.healthCapacity` (+0x132, 0x775312), 0x10 a heart | live: 0xA0 written, the touch screen draws ten hearts on the next frame (z3d-mods run mmre-save1, max10) |
| Filled hearts | `SaveData.health` (+0x134, 0x775314), 0x10 a heart | live: 0x10 written, one of three hearts is red (mmre-save1, health1); 0x80 of 0xA0, eight of ten |
| Rupee count | `SaveData.rupees` (+0x138, 0x775318) | live: 123 written, the counter reads 123 on the next frame (mmre-save1, rupees123) |
| Item buttons | `SaveData.equipment.buttonItems[0]` (+0x14A), B, Y, X, I, II | live, docs/items.md |

A fresh file reads `healthCapacity` 0x30, `health` 0x30, `rupees` 0. The HUD reads the three as it
draws: no counter animates between the write and the frame.
