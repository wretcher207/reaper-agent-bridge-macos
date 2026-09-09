# Guitar and bass — `shred` and `band`

`skills/guitar-apparatus/` is the guitar-side counterpart to the drum engine.
It renders humanized guitar and bass MIDI and inserts it through the same
bridge write path the drum groove uses (`insert_midi_file`).

```bash
# the whole four-track jam (2 guitars + bass + drums), replacing what was there
python3 reaperd.py band

# other tracks, a custom riff, a custom drum DSL, an explicit tempo
python3 reaperd.py band --guitar-l argent-l --guitar-r argent-r \
  --bass nolly-bass-library --drums rs-drums-monarch \
  --bars-file riff.txt --dsl beat.dsl --tempo 146

# one part at a time; --replace clears the track from --position first
python3 reaperd.py shred --track argent-l --bars-file riff.txt --seed 101 --replace
python3 reaperd.py shred --track nolly-bass-library --part bass --seed 303
```

A riff is a text file, **one bar per line, 16 steps** (spaces inside a bar are
visual only):

- `.` rest, `x` muted chug, `X` accented root, `o` let-ring root, `g` ghost.
- Connection cells: `_` ties the previous note through this step, `~` slides
  into the next one. These are what stop a riff sounding stabby. Chugs also
  carry under the palm for up to two steps instead of being cut short.
- Chord cells are **uppercase** note names read in the key of E (`E F G A B C
  D`), each firing Power Chord Sustain so the section moves harmonically.
- Lead scale tones are lowercase/digits (`s 3 a 5 6 7 h`) for single ringing
  notes over those chords. Case matters: `B` is a chord, `b` is a tritone.
- Palm-muted melody notes (`m n v f k`) walk between the low-E anchors so a
  riff reads as notes instead of a monotone rake, and the dissonant
  palm-muted ring clusters (`r 2 t 9 j`) strike the root with a clashing
  interval so the clash actually bites.

The full token table, with the reasoning behind each one, is in
`skills/guitar-apparatus/SKILL.md`.

Dynamics come from the drum humanizer's taste model: a deterministic musical
contour drives velocity across a four-bar phrase, RNG is only garnish, and the
no-repeat golden rule keeps consecutive chugs off one velocity. Double tracking
is two *performances*, not a copy — same riff, different `--seed` on the left
and right guitar.

Tuning and keyswitch maps live in `skills/guitar-apparatus/guitargen/maps.py`
and are confirmed against the instruments' own manuals: `argent_e` and
`argent_csharp` (Shreddage 3.5 Argent, 9-string) and `nolly_e` /
`nolly_csharp` (GGD Nolly bass). Another library is a new entry in that file.
Ships in the cloned repo, not via ReaPack. The MCP server exposes the same
write path as `insert_riff` (one part), `cut_band` (the four-track jam), and
`humanize_take` (see below), so an agent without shell access can cut parts
too.

