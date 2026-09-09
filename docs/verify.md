# Closed-loop verify — mix moves with measured proof

Every mutating command returns `ok: true`, but `ok` only means "REAPER did
it" — not "the mix got better". `verify` closes that loop: it captures the
track, runs your command, captures the **same spot** again, and reports what
actually changed in the audio.

```bash
python3 reaperd.py verify Bass -- set_fx_param \
  '{"target_track_name":"Bass","fx_name_contains":"ReaEQ","param_name_contains":"Gain","formatted_value":"-2.5 dB"}'
```

```text
[verify] pre:  LUFS-I -14.1 | RMS -18.0 dBFS | scope isolated_track (verified)
[verify] mutation set_fx_param: ok
[verify] post: LUFS-I -14.9 | RMS -18.8 dBFS | scope isolated_track (verified)
[verify] dLUFS-I -0.80   dRMS -0.80 dB
[verify] biggest spectrum moves: 315 Hz -3.1 dB, 250 Hz -1.7 dB
[verify] VERDICT: VERIFIED
```

Exit codes are the contract (agents branch on them): `0` VERIFIED (both
captures clean and comparable, deltas reported), `1` REFUSED (the mutation
was never sent: the pre-capture was blocked or silent, so nothing was
mutated), `2` UNVERIFIED: the mutation was sent and the project **may have
changed** but the change could not be verified. Exit 2 covers: post-capture
failed or silent, a partially-applied `batch` (the bridge keeps sub-commands
that ran before the failure), a bridge rejection (the JSON carries the
rejection code; a handler that failed mid-edit can leave a partial change
inside one closed undo block, indistinguishable from a clean resolution
rejection from outside), a mutation whose reply timed out or could not be
read (it may have executed, or may execute later), and pre/post captures
that stopped being comparable (track identity or capture scope changed
mid-verify). Nothing is ever rolled back automatically (one Ctrl/Cmd+Z
reverts it), and an agent must NOT blindly retry on exit 2: the change may
already be live.

Honest limits, by design:

- Bounds are frozen once, before the mutation: pre and post captures use the
  byte-identical `start_seconds`/`duration_seconds`, so a moved cursor or
  time selection between captures cannot skew the comparison.
- With Post Mortem installed you get per-band spectrum deltas, true peak,
  RMS, and stereo-image deltas; without it, LUFS-I deltas only (the report
  labels its `metrics_source`).
- If either capture is not a verified isolated track (some tracks fall back
  to a full-mix render), the report says the deltas describe the capture
  scope — it never presents full-mix deltas as per-track evidence.
- A silent capture refuses a verdict rather than comparing dead air.
- Two renders per verify: each capture blocks REAPER's UI for the render
  duration (default 10 s of audio; keep `--seconds` short).

