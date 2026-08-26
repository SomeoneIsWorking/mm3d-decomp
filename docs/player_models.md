# MM3D Player body-model ownership

Ground truth: retail Majora's Mask 3D `CTR-P-AJRE` RomFS, enumerated through the repository's `CtrRom` and GAR2/LzS
parsers. This records asset identity only; it does not claim that the native Player draw or animation
dispatcher has been fully decompiled.

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
