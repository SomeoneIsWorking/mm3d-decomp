# Camera: the player's camera and the C-stick

Addresses are the USA 1.0 layout (Project Restoration's output).

## Where it lives

- `PlayState.mainCamera` (play + 0x408) is the player's camera, a `Camera` of 0x198 bytes.
- `Camera.at` (+0x50) is the point looked at, `Camera.eye` (+0x5C) the eye after collision,
  `Camera.eyeNext` (+0x74) the eye before it.
- `Camera.yawRate` and `pitchRate` (+0x14, +0x16) hold the C-stick's eased turn in
  `Camera_Follow`.
- +0x148 holds the camera's direction as two s16 (pitch, yaw); +0x158 holds the mode.

## Which camera runs

- Standing or walking with the C-stick neutral, the player's camera runs the default follow
  function at 0x447FE8.
- `Input_CStickNeutral` (0x2185C8) takes play + 0x14 and tests the two floats at its +0x58 and
  +0x5C. When it returns false, the player's camera switches to mode 0x1F, whose function is
  `Camera_Follow` (0x46FAD4).
- `Camera_Follow` reads the floats at play + 0x80 and + 0x84 as the stick's turn. Read from the
  disassembly only; not checked live.

## How Camera_Follow places the eye

- Each update it measures eyeNext from at with `OLib_Vec3fDiffToVecGeo` (0x1BF070), adds the
  stick's turn, and writes eyeNext back with `OLib_AddVecGeoToVec3f` (0x1B049C). It then derives
  eye from eyeNext through its own distance limits and collision.
- `VecGeo` is { float r; s16 pitch; s16 yaw }. Pitch is the elevation, so positive puts the eye
  above at.
- So a turn written into eyeNext around at before `Camera_Follow` runs is kept, and the camera
  limits and collides it like a stick turn. Lowering yaw turns the view right, the same way as
  the C-stick's right.

## Checking it

z3d-mods' mouse camera (`patch/mm3d/mouse_camera.cpp`) does this. At South Clock Town's owl
statue the patch makes `Input_CStickNeutral` read as not neutral while a turn is pending, then
turns eyeNext at the start of `Camera_Follow`. Runs `mm-q-mouse7` and `mm-q-mouse8` measured
this. A turn of 3641 binary angles right moved the direction at +0x148 by -3626 in yaw, and
the same turn back moved it by +3642. A turn of 1820 up moved its pitch by +1789.
