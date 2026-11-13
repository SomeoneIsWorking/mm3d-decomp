# Item buttons and the inventory

`SaveData.equipment` (+0x14A, `gCommonData` + 0x152) holds the item buttons: `buttonItems[4][5]`,
then `buttonSlots[4][5]`, then the sword and shield halfword. A row's five bytes are B, Y, X, I
and II; 0xFF is empty.

Live (USA 1.0 layout under Project Restoration, South Clock Town, human Link):
- A fresh file reads `4D FF FF FF FF` in rows 0 to 2 (the Kokiri Sword on B), `FD FF FF FF FF` in
  row 3, and `00 FF FF FF FF` then 0xFF in the slots.
- With an item of id 1 in `items[1]`, X pressed on it in the Items screen writes 1 to
  `buttonItems[0][2]` and 1 to `buttonSlots[0][2]`: the item id, and the slot it sits in.
- A byte written to `buttonItems[0][3]` or `[0][4]` shows on the touch screen's I or II button on
  the next frame: the HUD reads the row as it draws. The same write to rows 1 to 3 shows nothing
  while Link is human.
- The item stays in the Items screen's grid when it is assigned.

Not checked: which row the other forms read for Y, X, I and II. The N64 game keeps one item page
for every form and a B item per form.

`SaveData.items` (+0x174) and `SaveData.masks` (+0x18C) are 24 bytes each, by slot.

`PlayState.buttonsHeld` (+0x30) is the pad's held buttons and `buttonsPressed` (+0x34) the ones
pressed this frame. Bit 12, which no 3DS button sets, arrives there unchanged.

`Actor_UpdateAll` (0x174640) walks the twelve actor categories of the actor context
(`PlayState` + 0x20B0) once a frame, called from the play update at 0x15F644.
