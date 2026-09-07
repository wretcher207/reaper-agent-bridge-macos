---
name: arrangement-midi
description: Compose complementary MIDI for an existing REAPER arrangement using a loaded virtual instrument. Use for pads, ominous textures, evolving synths, pulses, or melodic layers over marked sections, including Kontakt libraries and other synths. Adapts to the actual instrument and sounding music; does not create a new scratch session.
---

# Arrangement MIDI

Read the existing music, compose a part with a role, and audition it through the
user's loaded instrument. Preserve the project and work inside the requested span.
The successful outcome is a part the user likes in context, not merely valid MIDI.

## Establish the live contract

- Check bridge liveness once; inspect current context. Recheck project identity,
  tempo, marker bounds, and destination immediately before writing.
- Resolve the user's markers (for example `Synth` / `Synth End`) without case
  sensitivity. Ambiguous duplicate markers need clarification. Use their exact
  times; do not round a deliberately off-grid boundary to a bar.
- Resolve the instrument track and MIDI destination separately by GUID. A track
  named `Instrument MIDI` may send MIDI to the host and receive its audio back.
  Inspect sends, receives, channel mapping, mute/bypass/offline state and master
  routing. Track names alone do not establish the signal path.
- Inventory items in the span. Preserve existing material. A request to add a part
  does not authorize deleting another take, replacing the project, or resetting a
  scoring workspace. If the destination is occupied, use an unambiguous additive
  placement or clarify replacement intent.
- Carry forward the user's mood and musical role. Infer routine choices; ask only
  where missing information materially changes the result.

Prefer available REAPER MCP tools; otherwise use `reaperd.py cmd`. Discover the
repository from the current environment; do not hardcode a user's machine paths.
Read relevant sections of `bridge/command_schema.md` for payloads. The bridge is
the only live write surface; do not send ad hoc file-protocol JSON.

## Read what is actually sounding

1. **MIDI:** read notes, timing, durations, velocities, channels, mute state, and
   truncation flags. Inspect controller data, bends, articulation triggers and
   automation when a supported reader exists. Disclose missing reads; notes alone
   are not the complete performance. Do not treat keyswitches as harmony.
2. **Audio:** prefer isolated sources or verified isolated post-FX audio. Bass can
   anchor tonal movement; guitars expose harmony and phrasing; drums reveal
   accents, space and intensity. Compare multiple tracks before declaring a key.
3. **Timeline:** account for take offsets, playrate, pitch shifts, item boundaries,
   loops, active takes, and stretch markers. `get_items` is not a complete take
   transform reader. A saved RPP can supply missing information, but compare its
   items to live inventory and label it as saved-state evidence. Never silently
   substitute a conflicting saved edit for the live one.
4. **Sounding pitch:** inspect instrument/take/FX transposition and pitch automation
   where possible, or obtain the user's tuning/transposition. Raw DI analysis is
   pre-FX. Drop C shifted down nine semitones sounds with an E-flat low string;
   copying the dry-file C harmony would be wrong. Apply each known shift once,
   including any shift in the destination instrument.
5. **Confidence:** low instruments often have stronger harmonics than fundamentals.
   Cross-check candidate fundamentals across windows and against other instruments.
   Separate observed pitches, probable tonal center, and creative harmony. A
   dominant pitch class is not proof of a full key or note-perfect transcription.

Analyze the exact same bounded range throughout. Do not build an audio verdict on
silence. If media goes offline when REAPER loses focus, report that condition;
do not silently change a global preference. Direct source-file analysis can still
help, with its pre-FX/timeline limitations stated.

Produce a compact bar/beat map: recurring tonal material, likely section changes,
attack density, rests, energy, and uncertainty. Use this map to make compositional
decisions, not to mechanically double every detected event.

## Discover the destination instrument

Inspect the actual loaded instrument and patch through exposed parameters, supported
UI inspection, or documentation. Kontakt's host identity does not reveal its library.
User-provided patch identity is useful; do not claim to have verified hidden state.

Establish as needed: playable pitch range, MIDI channel, key zones/keyswitches,
mono/polyphony, velocity response, attack/release, internal arpeggiator/sequencer,
and mapped expression controls. Unknowns should limit specific actions, not prevent
all composition. Use the existing playable patch for a first audition when reasonable.

- Calmness comes from voicing, pacing, envelope and movement, not automatically
  low velocity. Values 29-49 were barely audible in one Dystropia audition;
  70-94 worked in another. These are observations, not a universal velocity preset.
- Do not assume CC1 or CC11 controls dynamics. Discover mappings before writing
  controllers, pitch bends, or patch automation; preserve unrelated automation.
- Parameter names such as Motion, Space, or Tone are patch-specific. Scan and use
  stable FX identities; never transplant Kontakt indices to another instrument.
- If the instrument feeds an audio return pre-fader, its source fader will not
  control that feed. Trace the real output before boosting gain. Check velocity,
  expression, patch levels, and return level rather than blindly adding +12 dB.

## Compose and write

Choose register, density, voice leading and dynamics for the existing mix. Let
sections develop: a restrained opening can broaden at a real arrangement change.
Leave rests and release room. Ominous texture may use a pedal, open fifths, suspended
tones or controlled dissonance; do not impose the same chord recipe on every song.
Avoid unnecessary sub-bass duplication. Preserve the requested creative role.

Write a local note plan with explicit time units, sounding-pitch reasoning,
destination/channel and source evidence. For a constant-tempo section, the helper
in [references/midi-plan.md](references/midi-plan.md) writes a standard MIDI file
and checks live note readback. It supports notes, not controllers or automation.
Use a suitable existing writer when those are needed. For tempo/meter changes,
derive positions from the live tempo map; do not use a single-BPM approximation.

Before insertion, validate pitch/channel/velocity bounds, positive durations,
same-pitch overlaps, and section bounds. Re-read live context and the destination.
Use a unique output path, explicit destination GUID, exact start and length,
`loop: false`, and `replace_existing_in_range: false` for a new part. Name the take
meaningfully. Do not import an unintended project tempo map.

## Verify and audition

- Re-read every written note and compare pitch, channel, velocity, start AND end.
  Confirm item boundaries and destination. Verify CC/automation separately if used.
- After a timeout or failed reply, inspect the destination before retrying. A
  mutation may already have happened. Avoid duplicate takes; report unverified
  changes and the undo boundary rather than claiming success.
- Audition the marked span through the loaded patch with the band. Do not claim
  audio quality from a command success or MIDI readback. User listening is a valid
  acceptance gate; label a first insertion as ready to audition until that happens.
- For measured before/after claims, use the same frozen range and valid non-silent
  captures. Preserve the tool's isolation/full-mix and live/saved-state caveats.
  Rendering, saving and destructive replacement still need the intent required by
  the repository's action boundary. Do not render solely because a skill says QA.
- On feedback, adjust the narrow cause: level/routing, register, density, harmonic
  clash, envelope or expression. Avoid rewriting a successful part unnecessarily.

Deliver a concise account of destination, span, musical development and verification
limits. Keep the MIDI and note plan for reproducibility. Never automatically save
the user's RPP or modify their agent memory as part of this workflow.
