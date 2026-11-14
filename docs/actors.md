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
