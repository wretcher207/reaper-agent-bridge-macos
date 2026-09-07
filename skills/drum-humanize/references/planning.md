# Native planning and verification

Resolve paths relative to the reaper-daemon checkout. The model is
`skills/drum-apparatus/drumgen/humanize.py`; learned dynamics are in `learn.py`.
Read only the command schema sections needed for current work.

## Supported CLI routes

```
python reaperd.py humanize --track "Drum track" --item-index 0 --map "Verified kit" --dry-run
python reaperd.py humanize --track "Drum track" --item-index 0 --map "Verified kit"
python reaperd.py humanize --track "Drum track" --item-index 0 --map "Verified kit" --follow-lead --example-through-bar 8 --dry-run
```

Replace the illustrative map and track with actual names. Check current `--help`.
The ordinary route changes velocity AND timing; `amount=0` still reshapes velocity.
The follow-lead implementation writes velocity only. Its explicit example bar
boundary is relative to the take's PPQ origin, not necessarily the project bar.
Both routes currently assume a 4/4 metric map. Dry-run and apply read/plan again;
same seed does not freeze a changed input. Neither command limits itself to the
time selection. Do not use it directly for a selected-range-only request.

There is currently no native CLI `--velocity-only` or `--timing-only` flag.
Use a local plan and explicit bridge payload for those dimensions or subranges.
Prefer the shared MCP surface when it supports the requested behavior; inspect
its current schema rather than assuming flags match.

## Velocity-only plan for flat material

This is an offline planning pattern, not a complete autonomous write script:

```python
from drumgen.humanize import plan_humanize
from drumgen import goldenrule

# notes/ppq/map were read and verified from the target take.
plan = plan_humanize(notes, ppq, kit_map=kit_map, amount=25, seed=seed)
vel = {edit['index']: edit['velocity'] for edit in plan['edits']}
vel = goldenrule.enforce(notes, vel, pitch_bands)
assert not goldenrule.violations(notes, vel)
edits = [{'index': note['index'], 'velocity': vel[note['index']]}
         for note in notes if vel[note['index']] != note['velocity']]
```

Import `drumgen` by adding the checkout's `skills/drum-apparatus` to Python's
module path. Pass `map_name` too when applying an approved per-kit profile.
`pitch_bands` must reflect verified kit/articulation constraints; do not invent
bands or clamp authored ghosts into accent bands. Run this model only on material
suited to an absolute rewrite. For authored dynamics, build targeted edits around
the original contour instead, then use the same shared enforcement/check.

For timing-only, keep only `index`, `new_ppq`, and `new_end_ppq` from position edits;
never send a velocity field. The model's independent tick offsets are proposals,
not a guarantee of safe timing. Validate boundaries/order/flam spacing/overlaps
and preserve durations. It does not implement a general human timing learner.

For a subrange, preserve original note indices, analyze neighboring notes for
phrase context, and include immutable neighbors in boundary checks. Restrict
emitted edits to the authorized range. Enforcement must not modify neighbors
outside it: use `skip` for their indices, then validate the complete boundary.
An unsatisfied boundary constraint calls for replanning the editable notes.

## Prewrite gate

- Keep the input snapshot and a deterministic note plan locally.
- Re-read note fields immediately before an index-addressed write and replan if
  they changed. A count guard is useful, but not a full concurrency guard.
- Prove the golden rule, final fill contour and bounds before a velocity write.
- Preserve triggers and unknown roles; resolve required roles before reshaping.
- Send `apply_note_edits` with target GUID, item index, full take note count and
  `allow_partial: false`. Skip a write if there are no edits.
- Verify readback by expected musical identity as well as index: sorting can
  change note indices after timing edits. Compare multisets of pitch, channel,
  start, end, velocity and mute state, preserving duplicate-note multiplicity.

The bridge's `end_advisory_drift` is not an exact-duration pass. Velocity-only
acceptance requires all original starts and ends unchanged. Timing acceptance
requires the expected starts/ends, intended spacing and no unapproved trimming.

## Evaluation cases

Use offline fixtures and an authorized audition, not word-count/style tests:

1. Flat backbeats, ghosts, hats, and a multi-tom fill: role contrast and fill arc.
2. Authored ghost/accent velocities on the same pitch: preserved contrast.
3. Velocity-only: byte-equivalent note starts/ends and unchanged channel/pitch.
4. Stacked hits and a deliberate flam: count/multiplicity and spacing preserved.
5. Dense kicks, long rolls and adjacent items: no mechanical two-value lock,
   invalid notes, flattened fill ceiling, or boundary repeats.
6. Odd meter, halftime, tempo changes: no silent 4/4 or global-ms assumption.
7. Changed take after planning: no stale write; replan or stop.
8. Unknown kit roles: no confident GM substitution or accidental bass edits.

Existing native model checks run with:
`python -m pytest skills/drum-apparatus/tests/test_humanize.py skills/drum-apparatus/tests/test_golden_rule.py`.
These are model regression checks, not coverage of every workflow case above or
proof of more realistic sound. On listening feedback, adjust one musical cause
at a time and compare to the original in the same passage.
