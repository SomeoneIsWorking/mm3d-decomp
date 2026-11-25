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

Every form uses row 0 for Y, X, I and II (poked `SaveData.playerForm`, then a scene load, South
Clock Town): as Deku, Goron and Zora the HUD and the Items screen draw row 0's items, X in the Items
screen assigns into row 0, and a write watch on `buttonSlots[1..3]` sees no store from the game
through a scene load, item presses and the Items screen in each form. A slot left in
`buttonSlots[1][1]` stays there and shows nowhere. Rows 1 to 3 hold only a B item per form.

`SaveData.items` (+0x174) and `SaveData.masks` (+0x18C) are 24 bytes each, by slot.

The Hero's Bow is item 1 (`ITEM_BOW`) in slot 1 (`SLOT_BOW`), its arrows `SaveData.ammo[ITEM_BOW]`.
Written there with the slot in `buttonSlots[1][EQUIP_BUTTON_Y]`, the chord page of z3d-mods'
patch, Y draws and aims it in South Clock Town (z3d-mods run `mm-ch20`), and a save at the owl
statue keeps all three.

`PlayState.buttonsHeld` (+0x30) is the pad's held buttons and `buttonsPressed` (+0x34) the ones
pressed this frame. Bit 12, which no 3DS button sets, arrives there unchanged.

`Actor_UpdateAll` (0x174640) walks the twelve actor categories of the actor context
(`PlayState` + 0x20B0) once a frame, called from the play update at 0x15F644.

## The inventory's slots, the Items and Masks screens
`SaveData.items` runs past its 24 bytes as one array of slots: items 0 to 23, masks 24 to 47
(`MASK_SLOTS_FIRST`), then seven bottles from 48 (`INVENTORY_SLOTS` 55). Live (z3d-mods run
ctl-mm6): item 0x12 written to slot 48 shows as an empty bottle in the Items screen's fourth
cell of the third row.

Live (z3d-mods run ctl-mask1): 0x39 (`ITEM_MASK_BUNNY`, the N64's id) written to slot 32
(`SLOT_MASK_BUNNY`) shows the Bunny Hood in the Masks screen's second row, third cell.

`SaveData.itemGrid` (+0x1A28, 20 bytes, five to a row) and `maskGrid` (+0x1A3C, 24 bytes, six to
a row; read from the disassembly, not seen) hold each cell's slot. A new file's item grid reads
1 2 3 4 6, 7 8 9 10 12, 14 15 16 48 49, 50 to 54: the ocarina's slot 0 is not in it.

The Items and Masks screens are one class (`ItemScreen`, `gUiScreens[UI_SCREEN_ITEMS]` and
`[UI_SCREEN_MASKS]`): `cursorColumn` (+0x18) and `cursorRow` (+0x19) are the cell under the
cursor, `buttonColumn` (+0xA3, 5 on Items) the column of the item buttons, `state` (+0x9F) 2
while browsing. Live (ctl-mm1): the cursor reads 0,0 when the screen opens, 1,0 after a move
right and 1,1 after a move down.

### Their draws
`ItemScreen_Draw` (0x59E3E4) and `MaskScreen_Draw` (0x59F5E0) first call `ItemScreen_DrawBase`
(0x5C215C), which calls `ItemScreen_DrawCursor` (0x5A19D8: `touchBackground` on queue 4, then
each of `cursors` whose bit is set in `cursorsShown` on queue 5), then queues `titleBar` on 3 and
`topDim` on 0, `unk_68` and (while `unk_9E` is set) `unk_70` on 5, the four `buttonIcons` on 5
unless held, and each `held` on 5 with order 7. The screen draw then queues `page` on 5 and its
cells (`cells`, 20 on Items, 24 on Masks) on 5. The call offsets are `ITEM_SCREEN_DRAW_*_CALL` and
`MASK_SCREEN_DRAW_*_CALL`.

`page`'s widgets: `all` holds the frames `set_frame0_g` to `set_frame3_g`, the cells' places
`item_set_pos_g`, the tabs `btn_item_omen_g` (`btn_omen_l` Masks and `btn_item_l` Items, each a
widget with its own layout, and their touch areas `bb_item_omen_pane00` and `01`: Masks 61 to 157,
Items 157 to 253, by 206 to 244), Return `btn_return_l` at (0, 202), the grid's panel
`item_panel_g` and the item buttons' column `right_item_set_l` (255 to 320). A cell's and a
cursor's root carries its place, the cell's middle (32, 28 for the first, 48 apart). Return's and
the tabs' translates are animated and keep their values against writes; their scales and their
own layouts' roots take them. The game hit-tests the tabs and Return where they are drawn:
`page` queued on the top screen, placed at 0.75 with each tab and its touch area moved together,
switched to Masks on a touch at the tab's new place and back to play on Return's (z3d-mods
items18 to items21). The item's description is play's message box (`gMessageObject`, a layout
whose root is the box's middle, 200 by 195), queued by `MessageMgr_DrawWindow` (0x17EBD8) on
queue 3 at `MESSAGE_MGR_DRAW_WINDOW_CALL`; placed and scaled by its root while the screen is up, it
drew there, and put back it drew a later message at its own place (items17).

## Pressing an item button for the player
`Play_Update` (0x15F644) runs every frame of a play state, a touch screen up or not;
`Actor_UpdateAll` does not run while the Items screen is up (a hook there saw no frame, ctl-mm5).

Live (ctl-mm6), written at the start of `Play_Update`:
- An item and its slot in `buttonItems[0][n]` and `buttonSlots[0][n]` of I or II, with
  `TOUCH_BUTTON_I` or `TOUCH_BUTTON_II` ORed into `gTouchButtonsHeld` (0x72A0ED) and
  `gTouchButtonsPressed` (0x72A0EE), which the pad update fills from the touch screen, uses the
  item: the Hero's Bow on I was drawn and aimed, a bomb on II taken in hand.
- Y and X read `PAD_Y` and `PAD_X` of `buttonsHeld` and `buttonsPressed` instead (read from the
  item button loop at 0x1DB748, not run this way).
- `TOUCH_BUTTON_OCARINA` in both brings the ocarina out (ctl-mm7).

## Bytes the game leaves alone
z3d-mods keeps its item slots in `buttonSlots[1..3][1..4]`; a save at the owl statue keeps them,
and the file's first row is the game's own (run ctl-mmsave, save0.bin read back).
