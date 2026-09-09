# Drums — kits, profiling, humanization

The DSL drum engine (`skills/drum-apparatus/`) ships a few built-in kit maps
(GM Standard, RS Monarch, Odeholm, MDL Tone, Sleep Token II) in
`skills/drum-apparatus/catalog/maps.json`. For **any other library**, auto-discover:

```bash
# 1. With the drum plugin on a track that has its .midnam loaded:
python3 reaperd.py discover-map Drums --save MyKit
# 2. Use it:
python3 reaperd.py groove beat.dsl --track Drums --map MyKit
#    or in the DSL:   @map MyKit
```

`discover-map` reads the MIDI note names REAPER has for the track (the
`.midnam` the library installed), classifies each note into a groovekit role
(kick / snare / hat-closed / hat-open / ride / crash / china / tom1..4 / ...),
fills missing articulations by fallback so a sparse kit never breaks the
engine, and saves the result to the user overlay
(`skills/drum-apparatus/maps/<name>.json`, gitignored). Libraries that don't
ship a `.midnam` (some Kontakt kits) report no note names; for those, build the
map by hand with `add-map`:

```bash
python3 reaperd.py add-map MyKontactKit --roles '{"KICK_R":36,"SNARE":38,"HH_OPEN_1":46,"CRASH_R":49,"CHINA_R":52}'
```

## Daemon Beater: profile a stem before you write drums

`profile` reads a guitar stem bar by bar and prints the numbers an agent
needs to plan drums: onset density, timing regularity, palm-mute vs ringing
decay, silence, low/bright band balance, and a 16th-note accent grid, plus
suggested section boundaries and repeat groups (A / B / A). Numbers, not
verdicts: the agent proposes section labels, you correct them.

```bash
python3 reaperd.py profile song.rpp guitar-di
python3 reaperd.py profile song.rpp guitar-di --start-bar 32 --bars 8
python3 reaperd.py profile song.rpp guitar-di --start-bar 32 --max-seconds 10
```

Point it at any bar and it analyzes just that window (plus
one bar of pre-roll and post-roll for context), never the whole stem. The
cut is hop-aligned, so timing, onset, grid, decay, and band numbers from a
window match a full pass; only the silence ratio is scored against a
window-local loudness reference. `--max-seconds` counts whole bars that fit
inside the cap, and refuses caps shorter than one bar instead of padding.

Prefer the DI track when there is one; distortion flattens the decay
contrast that separates open notes from palm mutes. Ships in the cloned
repo (`skills/drum-apparatus/`), not via ReaPack.

MCP clients get the same three steps without a shell: `profile_track`,
`riff_grid`, and `insert_groove`. The two analysis tools parse the `.rpp`
file on disk, so save the project before calling them. On an unsaved
project they describe stale material, which their payloads state outright.


## Humanize an existing drum take

`humanize` takes a flat drum item that is already on a track and gives it a
dynamic contour and micro-timing, in place.

```bash
python3 reaperd.py humanize --track drums --dry-run       # plan, print, write nothing
python3 reaperd.py humanize --track drums --amount 25     # 0-100 looseness (default 25)
python3 reaperd.py humanize --track drums --follow-lead   # copy the hand from your own bars
```

The dynamic contour is always applied; `--amount` only scales the random
spread and timing looseness on top of it. Fills build as a crescendo that
peaks at the resolve rather than piling up on the ceiling. The golden rule is
hardline (`skills/drum-apparatus/drumgen/goldenrule.py`): no drum hits the
same velocity twice in a row, per drum in time order, whatever lands between.

`--follow-lead` reads the velocity hand out of the bars you humanized by hand
and carries it across the rest of the take instead of applying the shared
taste model. It auto-detects the first flat bar; `--example-through-bar N`
sets the boundary explicitly. `--seed` is fixed by default, so a run is
reproducible.

