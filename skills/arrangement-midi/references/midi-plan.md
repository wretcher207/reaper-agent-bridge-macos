# Portable MIDI note plan

Run `python skills/arrangement-midi/scripts/midi_plan.py write plan.json part.mid`
from the repository, or resolve the script relative to this skill. Python standard
library only. The writer refuses to overwrite a file and never contacts REAPER.

```json
{
  "name": "Evolving texture v1",
  "bpm": 120,
  "length_qn": 16,
  "notes": [
    {"start_qn": 0, "end_qn": 15.5, "pitch": 60, "velocity": 85, "channel": 0},
    {"start_qn": 1, "end_qn": 14.5, "pitch": 67, "velocity": 79, "channel": 0}
  ]
}
```

Positions are quarter notes relative to the item, not bars or seconds. Channels
are zero-based; pitch is a MIDI number, avoiding DAW octave-label differences.
The example is a format demonstration, not a default harmony or instrument range.
Same-pitch overlaps on the same channel are refused. Overlaps between different
pitches are permitted. Resolution is 960 PPQ; starts and ends round to that grid.

Use only for constant-tempo sections. The tempo event describes the file's timing;
insert into the already verified project tempo without changing project tempo.
For a marker not on a bar line, derive duration in quarter notes from the live
tempo map and use the exact marker time for insertion. Release sound may extend
beyond note-offs; MIDI-bound verification is not an audible-tail measurement.

After insertion, save the `get_midi_notes` response as JSON (either the complete
response or its `data` object) and run:

```
python skills/arrangement-midi/scripts/midi_plan.py verify plan.json readback.json
```

Verification compares every note's pitch, velocity, channel, start, end and mute
state, with a one-millionth-tick tolerance for numeric serialization. It rejects
truncated results and checks counts. It does not verify item placement, track GUID,
CC, automation, patch sound, or loudness; those require the live workflow checks.
Neither command mutates REAPER. Keep the evidence and user acceptance separate
from a passing file check.
