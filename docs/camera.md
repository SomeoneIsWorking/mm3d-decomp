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

## The view

- `PlayState.view` (+0x1F8) is the N64 game's `View` as far as it is read: `fovy` +0x18 (45.17 in
  South Clock Town), `zNear` +0x1C (5), `zFar` +0x20 (20000), `scale` +0x24 (1), `eye` +0x28,
  `at` +0x34, `up` +0x40.
- The camera's update ends at 0x181BD0: it writes `view.scale` and `view.fovy`, then calls
  `View_LookAt` (0x184618, OoT3D's 0x2D77DC with the N64 offsets) on `camera->play->view` with
  the eye, at and up it made. Write watches on the view's eye and up stop only there.
- Standing in South Clock Town the view's eye is the main camera's `eye`, and its at the
  camera's `at` within 0.02.
- `PlayState.cameraPtrs` (+0xA68) holds the main camera (play + 0x408) first;
  `PlayState.activeCamera` (+0xA78) is the index the view follows: 0 in play, 1 during South
  Clock Town's arrival cutscene with a second camera in `cameraPtrs[1]` (run mm-cs-cams).
- `PlayState.frames` (+0x138) counts the game state's ticks (0x10676C, from the game thread's
  loop); a warp starts it from 0 again (run mm-frames-warp: 0x20E in the old scene, 0x41 three
  seconds into the new one).
