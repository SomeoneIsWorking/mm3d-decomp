# MM3D source-file attribution

How many of MM3D's 12054 recovered functions can be tied to the original C++ source file they were
compiled from, on the engine's own evidence rather than on a guess.

## Headline

| | |
|---|---|
| Functions in the image | 12054 |
| **Functions attributed** | **135** (1.12%) |
| Rows in `function_source_map.csv` | 137 (2 functions carry 2 source files each) |
| Confidence `direct` | 137 |
| Confidence `pooled` | 0 |
| Distinct source files attributed | 93 of the 104 the image names |
| Assert strings in the image | 281 |
| Strings that attributed a function | 250 |
| Strings left unattributed | 31 (30 with a pointer nobody references, 1 with no pointer) |

Produced by `mm3d-decomp/tools/FunctionSourceAttribution.py`; run it through
`mm3d-decomp/tools/run_source_attribution.py`, which enforces the control and returns a real
process exit status.

## The bug that made this look impossible

`SourceFileMap.py` reported `n_refs=0` for all 281 strings, and the natural conclusion was "the
strings are unreferenced, attribution is off the table". That conclusion was wrong, for two
independent reasons.

**1. It asked Ghidra about the wrong address.** An assert string is never addressed directly by
code. The code executes `LDR r2, [pc, #imm]` and reads a *word* from a literal pool; that word
contains the string's address. Ghidra's reference manager records the reference to the **pool slot**,
not to the string. So `getReferencesTo(string_va)` returns zero *by construction*, no matter how many
real references exist. Asking about the slot instead: 258 real code references.

**2. It computed the wrong string address.** The assert strings are preceded by `0xFF` padding when
they share a slot with a neighbour. The original walk-back stopped only at bytes below 0x20, so it
swallowed the padding and placed the "string start" inside it. No pointer can match an address
inside the padding. Fixing the walk-back to treat `0xFF` as a terminator took the strings with a
real pointer from **205 to 280 of 281**. This single character class was worth 75 strings.

## How an attribution is established

For each string: find every 4-aligned word in the image equal to the string's address (its pool
slot), then require a *provable* load of that slot:

1. an ARM `LDR Rd,[pc,#imm]` (or Thumb `LDR Rd,[pc,#imm*4]`) at the referencing address,
2. whose PC-relative target recomputes to exactly that slot.

The referencing instruction must lie inside the claimed function's body. This is checked by decoding
the instruction, not by trusting Ghidra's reference type — see "What was rejected" below.

`confidence` is `direct` when that verified load is in the claimed function. `pooled` is reserved for
a slot reached from a *data* cell that is in turn loaded by code. **This run produced 0 `pooled`
rows.** The 4 slots that are referenced from data had their second hop land outside any function, so
they were not attributed. Note the labelling question: a concurrent agent working the same image
chose to label all 257 of its rows `pooled`, on the reading that every reference here goes through a
literal pool. Both readings are defensible; this file's `evidence` column names the mechanism
(`ldrlit@`) so a reader can re-label without re-deriving. The two runs independently agree on 136 of
137 (function, file) pairs.

## Verification

`scratch/mm3d_attr_modules/verify_claims.py` re-derives every claim from the raw image
(`scratch/mm3d_layout/mm3d.code`) with a hand-written decoder, sharing no code with the attribution
script and making no use of Ghidra's reference manager.

    rows=137  evidence claims=258  verified=258  contradicted=0

Each claim must satisfy: the instruction is a PC-relative literal load; its target is the claimed
slot; the slot holds the claimed string address; the bytes there are
`...\source_file(N)`; and the load lies in the claimed function's body.

### A trap for anyone re-checking this

**1303 of the 12054 functions have disjoint bodies** (2 to 10 address ranges each; 14027 ranges for
12054 functions). So `[entry, entry+size)` from the `size` column of `functions.csv` is *not* the
body. A first pass of the verifier used that column and reported 6 confident-looking contradictions
— e.g. `FUN_003c8200` "referencing" a load at `0x4f902c`, 1.2 MB past its entry. All 6 were the
verifier's bug, not the attribution's: the real body of `0x3c8200` has a range at
`0x4f9014..0x4f91cf` that does contain it. `mm3d-decomp/tools/FunctionBodies.py` dumps the true
ranges to `function_bodies.csv` (14027 rows) and confirms each of the 6 individually. **Use
`function_bodies.csv` for any containment question in this image**, not `functions.csv`'s `size`.

## What was rejected, and why that matters

One reference was refused rather than emitted. `z_oceff_storm.cpp(533)`'s string is pointed to from
two slots, `0x43991c` and `0x68d6cc`. Neither is loaded by any PC-relative load in the image, but
Ghidra held a `DATA` reference from `0x204970`, which falls inside `FUN_00204640`'s body. The
instruction at `0x204970` is `e88d0006` = `STMFD sp!, {r1,r2}` — a register save that cannot load
memory at all. Accepting it would have produced a confident, indefensible `direct` row. The
`direct` criterion was therefore tightened from "a reference exists inside this function" to "a
verified literal load of this slot exists inside this function", and the row was dropped: 136
functions became 135. The rejected count is printed on every run as
`REJECTED references_not_a_load_of_the_slot`.

## Per-source-file counts (top 15)

    6  ActorMultiEffect.cpp            2  LayoutClass.cpp
    4  EnemyBasicEffectContainer.cpp   2  Luminary.cpp
    4  MoviePlayer.cpp                 2  MajoraEffect.cpp
    4  Package.cpp                     2  MenuFileSelecterState.cpp
    4  fileUtility.cpp                 2  MenuScheduleState.cpp
    3  MenuMapState.cpp                2  MessageManager.cpp
    3  ObjectBankArchive.cpp
    3  actor_util.cpp

64 of the 93 files have exactly one attributed function.

These counts are a property of **assert coverage, not file size**. A function with no `ZASSERT` in
it cannot be attributed by this method however large it is, so a count of 4 says "4 of Package.cpp's
functions contain an assert", not "Package.cpp is small".

As a sanity check that the method produces structure rather than noise, functions attributed to the
same file cluster: `LayoutClass.cpp`'s two are 0xc0 apart, `MultiTorchModelContainer.cpp`'s 0x158,
`MenuFileSelecterState.cpp`'s 0x2c0, `MajoraEffect.cpp`'s 0x480 — contiguous code, as a compiler
emitting one file's functions together must produce. Larger spreads are real too: `TextSprite.cpp`
has functions at `0x1693f8` and `0x5fd95c`, and both were verified by hand against the raw bytes.

## What remains unattributed, and why

**31 of 281 strings, all listed with their reason in `function_source_map.summary.txt`.**

- **1 string, `main.cpp(344)` at `0x10425c`, has no pointer to it anywhere in the image.** It sits
  in a general `.rodata` blob next to `rom:/shaders/GzwShader.shbin` and other path strings, rather
  than in a pool of its own. No attribution is derivable.
- **30 strings have a pointer but no code reference to their slot** (`refs=0 refs_from_data=0`).
  These sit in *data descriptor tables*, not in code: the word is typically followed by the constant
  `0x0072f7f0` and the float `0x3f800000` (e.g. slot `0x5a45e0`, pool `0x5a45d8`). Three resolution
  routes were tried and all came up empty: PC-relative literal load (only 3 such loads exist for any
  slot in the whole image), a base register loaded from a literal **in the same function** and then
  indexed (0 of 31), and a one-hop data→code walk (4 slots referenced from data, none with the second
  hop landing in a function). The remaining route — a base register set up once by a startup routine
  and then used by every function, so the `LDR [rBase,#imm]` cannot be resolved without whole-program
  dataflow — is exactly the kind of inference that produces a plausible wrong answer, so these 30
  are reported unattributed.

The 4 slots referenced from data are counted (`slots_with_data_refs=4`) so it is visible that the
`pooled` path was exercised and produced nothing, rather than never running.

## Reproducing

    cd <zelda3d checkout>
    python3 mm3d-decomp/tools/run_source_attribution.py              # must exit 0
    python3 mm3d-decomp/tools/run_source_attribution.py \
        --require definitely_not_a_real_file.cpp                      # must exit 1
    python3 scratch/mm3d_attr_modules/verify_claims.py                # must exit 0

The Ghidra project used is a **copy** at `mm3d-decomp/build/ghidra-mm3d-attrib`, because running
analysis against the pristine project would modify it. The raw command, if the runner is bypassed:

    MM3D_ATTR_REQUIRE=z_kankyo.cpp timeout 1800 analyzeHeadless \
        mm3d-decomp/build/ghidra-mm3d-attrib mm3d -process -noanalysis \
        -scriptPath mm3d-decomp/tools -postScript FunctionSourceAttribution.py

### On the control

`SystemExit(1)` from a Jython postScript does **not** make `analyzeHeadless` exit non-zero —
verified on ghidra_12.0.4, the script printed its failure and the process still returned 0. A
control that cannot fail the build is decoration, so the enforcement lives in
`run_source_attribution.py`, which checks the captured output and returns the real status. Both
directions have been run: with `--require z_kankyo.cpp` it exits 0, and with a deliberately bogus
require it exits 1.

## Known conflict

Another agent working this image concurrently writes its own version of
`mm3d-decomp/build/decomp/function_source_map.csv` (257 rows, all `pooled`, a different `evidence`
grammar) and extended `mm3d-decomp/tools/SourceFileMap.py`. The two runs independently agree on
**136 of 137** (function, file) pairs. They differ on one: this file says `Package.cpp` belongs to
`FUN_0015141c`; the other says `FUN_0012cee4`. `0x12cee4` is the *start of a body range* of the
function whose entry point is `0x15141c` (see `function_bodies.csv`), so this file's key is the
canonical entry point that matches `functions.csv`'s `vaddr` convention. Whichever version is in
that path when you read it, regenerate before trusting it.
