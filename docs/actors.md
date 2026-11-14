# Actors

USA 1.0 layout. Structures are in `include/z3D.h`.

- The actor context is `PlayState.actorCtx` (+0x20B0). Its twelve category lists start at +0x10,
  12 bytes each: a count, then the first actor. `Actor.next` (+0x134) links a list.
  `Actor_UpdateAll` (0x174640) walks them as `*(ctx + 0x14 + category * 0xC)` and follows +0x134.
- The player is the first actor of category 2: `Actor_UpdateAll` reads it from `PlayState` +0x20DC
  before the walk. Its `id` is 0 and `category` 2.
- `Actor.home` is at +0x08 and `Actor.world` at +0x24 (OoT3D's is +0x28). `Actor_UpdateAll` copies
  `world.pos` to `prevPos` (+0x10C) before each actor's update, then stores the XZ distance to the
  player's `world.pos` at +0x9C and the height difference at +0xA0.
- Seen in memory in South Clock Town (entrance 0xD800): home and world both (-281, 0, -700) on
  arrival; scale 0.01 at +0x58, gravity -1 at +0x74, terminal velocity -24 at +0x78.
- Writing a position into `home.pos`, `world.pos` and `prevPos` together moves the player: written
  200 above the ground, he reads 185.3 twelve frames later and lands.
- `Actor.textId` (+0x11A, u16) is the message A opens when the actor is checked or spoken to, with
  the N64 game's ids: South Clock Town's owl statue (actor id 0x1B2, category 7) holds 0xC01, its
  save prompt. Written to 0x22 before the check, the statue shows "You got the Hero's Bow!".

## The view
`PlayState` +0x220 is the eye the frame is drawn from and +0x22C the point it looks at, three
floats each. Seen in the Astral Observatory (entrance 0x4C10): with Link at (-6, -129, 103) the
look-at is (-6, -97.2, 103), 31.8 above his feet, and the eye (-6, -80, 166.3) behind him; both
follow him as he walks. The same two vectors are also at +0x458/+0x464 and +0x920/+0x92C (camera
structures, not laid out yet). The circle pad moves Link relative to this view: up is away from
the eye.

The ocarina's camera faces Link from the front, and the view picks up from there once he puts
it away: in South Clock Town with Link at (-277, 100, -1630) facing -z the eye is 154 behind him
before, at (-261, 110, -1673) while he plays, and then eases out along that line to
(-229, 114, -1756), 126 in front of him, where it stays until he walks; then it swings behind.
Link's position and yaw do not change. Seen with Project Restoration alone and with our patch
on it; the vanilla 1.1 code was not run (our addresses are for Project Restoration's bake).
