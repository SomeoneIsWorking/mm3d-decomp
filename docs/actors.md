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

## The model's place in the draw
`Actor.shape.rot` (+0xC0, three s16) is the model's rotation: the player's yaw there follows
`world.rot`'s (-16117 against -16118 standing in South Clock Town). The draw places each actor's
model by `world.pos` and `shape.rot` as they stand when it runs: a replay of the draw with both
written between two ticks draws Link turned between them (z3d-mods run mm-act-on, crops
`on-vs-off-link-36-47.png`). Actor_Draw itself is not found in this build yet.

## Skeletons
`SkelAnime_DrawOpa` (0x1FEB14, 315 call sites) is OoT3D's: it queues the skeleton's model in a
deferred list through 0x20AB34, called at +0x48 (`SKELANIME_DRAW_OPA_QUEUE_CALL`) with the
`SkelAnime` in r1, its model matrix in r2 and the limb callbacks after. 0x20AB34 has one other
caller, `SkelAnime_DrawOpaEx` (0x3780B0, its call at +0x40), which passes one stack word from its
own caller where `SkelAnime_DrawOpa` passes 0 (one call site, 0x394CD4, with an actor's
`SkelAnime` at +0x1F8). 0x20AB34 reads the model at `SkelAnime` +0x34 (OoT3D's +0x28).

The player's `SkelAnime` is at player + 0x334: `Player_Draw` (0x1F9038) reaches
`SkelAnime_DrawOpa` through 0x201074 with player + 0x334 and the model matrix at player + 0x14C.
In South Clock Town it holds the model at +0x34, the limb count 0x1A at +0x7C, the joint table at
+0x80 (player + 0xE18) and a second table at +0x84. The joint table's entries are 0x34 bytes, a 3x4
matrix relative to the parent limb first, as OoT3D's `SkelJoint`.

The pose is set in the update and read in the draw: in a tick, `Player_Update` (0x1F9E80) writes
the second table (0x1FD3EC, reached from the `SkelAnime` method 0x22D5A8) and 0x23F0FC copies one
table into the other, limb by limb up to the limb count, all before `Player_Draw`. The model's
deferred draw (0x5EDC40) walks the limbs: the player's limb controller (vtable 0x63A798, at
`SkelAnime` +0x2C; +0x4 the actor, +0x10 the override callback) copies each limb's matrix from
the actor's joint table (0x5BF8FC, `player + 0x3B4`, the `SkelAnime`'s +0x80), runs the override,
and 0x5EB6A8 multiplies it onto the parent's. A replay of the draw with the joint table written
between two ticks draws the pose between them (z3d-mods run mm-skel-on).

## The target arrow
The spinning green arrow over South Clock Town's owl statue is the Z-target arrow, not an actor
of its own: `Target_Draw` (0x18F488, the N64 game's) draws it from `func_001707CC` (+0x50) with
`actorCtx` +0x120 (`PlayState` +0x21D0) and the play state. It builds the arrow's matrix in the
draw: a turn about Y of `gameplayFrames` (`PlayState` +0xC4BC, one a tick) times 3000 binary
angles (0x177 * 8 at 0x18FC80), then writes it into each of its two models (+0xAC, +0xB0) and
queues them (0x20AAA8). Moving the owl statue moves it; nothing in the statue's actor or models
steps, and holding the vblank counters only changes it by stalling ticks (z3d-mods runs
mm-rupee-*, mm-rupee-mtx: write watches on the arrow model's matrix stop at 0x18FD0C).
