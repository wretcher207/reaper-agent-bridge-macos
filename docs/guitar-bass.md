# Guitar and bass

`skills/guitar-apparatus/` is the guitar side of the drum engine. It renders
humanized guitar and bass MIDI and inserts it through the same bridge write
path the drum groove uses (`insert_midi_file`). Ships in the cloned repo,
not via ReaPack.

## Commands

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

MCP clients get the same write path as `insert_riff` (one part), `cut_band`
(the four-track jam), and `humanize_take`.

## Riff notation

A riff is a text file, one bar per line, 16 steps per bar. Spaces inside a
bar are visual only.

| Token | Meaning |
| --- | --- |
| `.` | rest |
| `x` | muted chug |
| `X` | accented root |
| `o` | let-ring root |
| `g` | ghost |
| `_` | tie the previous note through this step |
| `~` | slide into the next note |
| `E F G A B C D` | chord cells, uppercase, key of E. Each fires Power Chord Sustain. |
| `s 3 a 5 6 7 h` | lead scale tones, single ringing notes over the chords |
| `m n v f k` | palm-muted melody notes that walk between the low-E anchors |
| `r 2 t 9 j` | dissonant palm-muted ring clusters against the root |

Ties and slides are what stop a riff sounding stabby. Chugs also carry under
the palm for up to two steps instead of being cut short. Case matters: `B`
is a chord, `b` is a tritone. The full token table, with the reasoning
behind each one, is in `skills/guitar-apparatus/SKILL.md`.

## Dynamics

Velocity comes from the drum humanizer's taste model. A deterministic
musical contour drives the four-bar phrase, random spread is only garnish,
and the no-repeat golden rule keeps consecutive chugs off one velocity.
Double tracking is two performances, not a copy: same riff, different
`--seed` on the left and right guitar.

## Instrument maps

Tuning and keyswitch maps live in `skills/guitar-apparatus/guitargen/maps.py`
and are checked against the instruments' own manuals.

| Map | Instrument |
| --- | --- |
| `argent_e`, `argent_csharp` | Shreddage 3.5 Argent, 9-string |
| `nolly_e`, `nolly_csharp` | GGD Nolly bass |

Another library is a new entry in that file.
