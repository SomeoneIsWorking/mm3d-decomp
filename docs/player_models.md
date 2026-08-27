# MM3D Player body-model ownership

Ground truth: retail Majora's Mask 3D `CTR-P-AJRE` RomFS, enumerated through the repository's `CtrRom` and GAR2/LzS
parsers. Native Player draw and base mesh visibility evidence now lives in `player_draw.md`; animation
dispatch remains only partially recovered.

## Per-form body CMBs

| Player form | actor archive | body CMB member |
|---|---|---|
| Fierce Deity | `/actors/zelda2_link_boy_new.gar.lzs` | `boy/model/link_demon.cmb` (`link_demon`) |
| Goron | `/actors/zelda2_link_goron_new.gar.lzs` | `goron/model/link_goron.cmb` (`link_goron`) |
| Zora | `/actors/zelda2_link_zora_new.gar.lzs` | `zora/model/link_zora.cmb` (`link_zora`) |
| Deku | `/actors/zelda2_link_nuts_new.gar.lzs` | `nuts/model/link_deknuts.cmb` (`link_deknuts`) |
| Human | `/actors/zelda2_link_child_new.gar.lzs` | `child/model/link_child.cmb` (`link_child`) |

These identities explain why the generic MM object substitution cannot select Player correctly. The
runtime object's loaded object slot is not a stable form-model identity, and the catalog's ordinary
`/actors/zelda2_<object-short-name>.gar.lzs` rule does not name these `_new` archives. Selection must
come from `Player::transformation`.

## Animation ownership is separate

The body archives do not own the normal Player animation corpus:

- `zelda2_link_boy_new`: 1 CMB, 0 CSAB;
- `zelda2_link_child_new`: 3 CMB, 0 CSAB;
- `zelda2_link_goron_new`: 7 CMB, 1 special-purpose CSAB;
- `zelda2_link_zora_new`: 3 CMB, 0 CSAB;
- `zelda2_link_nuts_new`: 5 CMB, 3 special-purpose CSAB;
- `/actors/zelda2_link_new.gar.lzs`: 0 CMB, 847 CSAB and 847 `linkb` tracks.

Therefore a form-model port that samples only the selected body archive will correctly select
geometry but will leave ordinary movement in bind pose. The next Player-render step must resolve
CSABs from `zelda2_link_new` with the correct form-directory identity; it must not silently pick the
first same-basename clip from that shared archive.

## Animation member identity

The shared archive's 847 CSAB members divide into six top-level directories: `boy` 455, `goron`
105, `child` 95, `nuts` 93, `zora` 83, and `kafai` 16. Short names are not identities: 113 short
names occur in more than one directory, with some occurring in all five Player-form directories.
For example, `ca_wait_free` exists under `boy`, `goron`, `nuts`, and `zora`.

Named N64 Player animation resources provide an exact member leaf: stripping only the literal
`__OTR__objects/gameplay_keep/gPlayerAnim_` prefix yields the retail CSAB basename. Selection then
uses the live form's directory and requires an exact full member path. Human Link is the one
documented two-directory case: Human-specific clips under `child/anim` take priority, then the
shared `boy/anim` corpus is consulted. Retail evidence distinguishes the order:

- `link_normal_walk.csab` exists under both `child/anim` and `boy/anim`, so Human selects `child`;
- `link_normal_wait_free.csab` is absent under `child/anim` but exists under `boy/anim`, matching
  the existing parser finding that child Link reuses the boy corpus for most/common clips;
- form-specific `pg_wait.csab` and `pz_wait.csab` exist only under `goron/anim` and `zora/anim`.

No other form borrows another form's directory. Unnamed `gameplay_keep_Linkanim_*` resources and
non-`gPlayerAnim_` animation resources remain unmapped until their identity is recovered; selecting
a same-basename member or inventing a default would be a heuristic.

Across the 675 named `gPlayerAnim_*` resources in the N64 `gameplay_keep` XML, exact retail members
exist for 383 Fierce-Deity routes, 85 Goron routes, 54 Zora routes, 70 Deku routes, and 431 Human
routes. Human's 431 divide into 77 `child` members and 354 `boy` fallbacks after child precedence.
These are candidate-corpus counts, not a claim that each form's runtime can select every N64
resource or that the resulting pose has been visually verified.
