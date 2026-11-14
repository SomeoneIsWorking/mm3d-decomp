# Motion: the gyroscope and the first-person look

Addresses are the USA 1.0 layout (Project Restoration's output). Offsets on the player are from
the player actor.

## The path

1. `GyroscopeReader_ReadLocal` (0x121FB0, the SDK's reader) takes up to 32 new HID samples (the
   HID service makes about 100 a second). Per sample and axis `GyroscopeReader_CalculateAxis`
   (0x12E2D8) turns the raw value into a speed, `GyroscopeReader_UpdateDirection` (0x12E10C) turns
   the reader's direction matrix by it, and the angle sums it. Once per call, with the
   accelerometer, `GyroscopeReader_ReviseDirection` (0x12E494) pulls the matrix toward gravity.
2. `Motion_Update` (0x219610), once a game frame from the main loop, reads the latest status
   (`GyroscopeReader_Read`, 0x114518) and takes only the direction matrix: yaw from the matrix's
   first row projected on the horizontal plane, pitch from what is left after that yaw is undone.
   It stores them in degrees in `gMotionState`, unwrapped, minus a reference taken at the last
   reset. Roll is always 0. The speed and angle of the status are not used.
3. `Player_UpdateLook` (0x21C5AC), called from four player action functions (first person and the
   aimed items), first moves `Actor.focus.rot` by the circle pad, then, while the gyro look is
   active, overwrites it: pitch = `lookBase.x` + `gMotionState.pitch` * `pitchScale`, yaw =
   `lookBase.y` + `gMotionState.yaw` * `yawScale`, both clamped to the look's limits.
   `Motion_GetLook` (0x2232F8) does the scaling. A turn on the HID x axis is positive pitch and
   looks down; a turn on y is positive yaw and looks left.

So the view is a function of the 3DS's orientation since the last reset, not of its turn rate.
One degree of yaw of the 3DS is 2.1 degrees of view, one degree of pitch 1.46 (`yawScale`,
`pitchScale`, set once in the main thread's start, 0x103EC8).

## When the gyro look is active

All of:
- `gCommonData.motionOff` (+0x3520) is 0. Written 1 live, the same input leaves the view still.
- `Player_UpdateLook`'s last argument is 0.
- Player +0x129BC bit 0. It is set, with a reset, on the first frame where bit 1 is set, or
  `stateFlags1` (+0x11DB0) has 0x1000000, or the action function (+0x140) is 0x221AD8. In the
  plain first-person view (ZL under Project Restoration, `stateFlags1` 0x100000) the word reads 3.
- `gMotionState.valid`.

`Player_ResetLook` (0x2118C8) copies `focus.rot` to `lookBase` (+0x125B8, three s16) and calls
`Motion_Reset` (0x228E5C), which zeroes the angles and asks `Motion_Update` for a new reference.
It runs when the look becomes active and on every frame where the circle pad is off centre (pad
state at player +0x129CC: its direction bits 0xF0000000, or stick x and y at +0x40 and +0x44 with
a squared length of 5.2 or more). So the pad moves the view, and the gyro carries on from there.

The circle pad's own step is not linear: each frame `focus.rot` moves by (1 - cos(stick * 200
binary angle units)) * 725 (pitch) or 715 (yaw) units, with the stick's sign.

## What the reader does to the rate

`GyroscopeReader_Reset` (0x114898) and the game's start (`Motion_Init`, 0x105670) leave the reader
with (flags read live as 01 01 01 00):

| Offset | Value | Meaning |
|---|---|---|
| +0x854 | 1 | zero play on: a speed within +-`zeroPlay` is 0 |
| +0x858 | 0.005 | `zeroPlay`, 1.8 degrees a second |
| +0x855 | 1 | zero drift on |
| +0x85C, +0x860, +0x864 | 0.01, 100, 0.02 | drift radius (3.6 degrees a second), sample count, power (mode 1) |
| +0x856 | 1 | the accelerometer revises the direction |
| +0x868, +0x86C | 0.03, 0.4 | revise power, and the range around 1 G where it applies |
| +0x857 | 0 | no axis rotation |
| +0x844, +0x850 | 1.0, 2 pi / 100 | direction: radians per sample for a speed of 1 |
| +0x848 | 0.01 | angle: turns per sample for a speed of 1 |

Speeds are in units of 360 degrees a second. Other fields: +0x7E0 speed x, y, z; +0x7EC angle
(turns); +0x7F8 the direction matrix, rows are the 3DS's axes; +0x81C the accelerometer reader;
+0x8A0 the drift bias per axis, in raw units; +0x8AC the history index and +0x8B0, +0xCB0,
+0x10B0 256 raw samples per axis.

- Zero drift: the reader counts how many of the last `count` raw samples lie within the radius of
  the newest. With n of them, f = ((n - 1) / (count - 1))^32; the sample moves toward their mean
  by f and the bias moves toward that by `power` * f. The bias is subtracted from every sample. A
  rate that holds within 3.6 degrees a second for one second becomes the bias within about another
  second, and the view then drifts the other way for as long again once the turn stops.
- Zero play: anything slower than 1.8 degrees a second is dropped.
- Revise: once a `ReadLocal`, when the acceleration's length is within 0.4 of 1 G, the matrix
  moves 3% of the way to putting gravity on its second row. With an accelerometer that never
  changes, pitch decays back to level at that rate; yaw around gravity is untouched.
- The matrix turns around the 3DS's own axes. A yaw rate on y alone, after a pitch, tilts the
  first row out of the horizontal plane and the game reads a different pitch. A yaw around world
  up is the rate vector (0, cos p, -sin p) for a 3DS pitched by p on x.

## Seen in the running game

South Clock Town, first person, the app's harness. The emulator scales the rate it is given by
the host's last frame time over 1/60 s (Azahar `hid.cpp`, `UpdateGyroscopeCallback`), so an
unthrottled run feeds roughly a tenth of the rate asked for, and unevenly; the degrees below are
the reader's own angle, which is what reached the game.

- `gyro-mm2`: 480 degrees a second for 0.5 s on y turns the view left, on x tilts it down, on z
  changes both. The same 40 degrees a second that an earlier run (`mm-gyro3`) called no turn is
  1.7 degrees after the scaling (`gyro-mm1`).
- `gyro-mm4`: 7.939 degrees of yaw reach the reader, `gMotionState.yaw` reads 7.939 and
  `focus.rot.y` moves 16.67 degrees: 2.10 a degree. With the revise and the drift off, 17.068
  degrees of pitch read 17.067 and move `focus.rot.x` 24.91 degrees: 1.46 a degree.
- `gyro-mm3`: with the reader as the game leaves it, 13.0 degrees of pitch are 5.5 one second
  later and 0.9 after three. With +0x856 written 0 the pitch stays (18.355 for three seconds).
- `gyro-mm3`: a yaw of 55 degrees on y alone, at 18.4 degrees of pitch, brings the pitch to 9.9.
  `gyro-mm4`: the same yaw as (0, cos p, -sin p) leaves it at 17.07 and yaws 42.57 degrees for a
  rate vector 42.58 long.
- `gyro-mm6`, zero drift off: a rate under 1.8 degrees a second for 3 s gives 0.000 degrees; with
  +0x854 written 0 it gives 1.608. Zero drift back on, the same rate gives 0.894 degrees in the
  first 3 s and 0.009 in the next 3 (bias 7.5 raw units), and the view comes back 0.26 degrees
  after the turn stops while the bias falls to 0.
- `gyro-mm7`: `motionOff` written 1, the input that had turned the view leaves it still.

## Not known

- The aimed items (bow, hookshot) were not run: `Player_UpdateLook` is their shared function by
  its call sites only.
- What sets bit 1 of player +0x129BC, and the +0x3524 byte the pad's look reads (1 and 3 flip the
  pitch stick, 2 and 3 the yaw stick, by the code).
- `GyroscopeReader_ReadLocal`'s raw-to-speed scale was not checked against a real console's
  calibration, only against the emulator's.
