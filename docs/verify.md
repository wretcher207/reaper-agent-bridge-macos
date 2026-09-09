# Verify

Every mutating command returns `ok: true`. That means REAPER did it, not that
the mix got better. `verify` closes the loop: capture the track, run the
command, capture the same spot again, report what changed in the audio.

## Example

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

## Exit codes

Agents branch on these.

| Exit | Verdict | Meaning |
| --- | --- | --- |
| 0 | VERIFIED | both captures clean and comparable, deltas reported |
| 1 | REFUSED | the mutation was never sent. The pre-capture was blocked or silent, so nothing changed. |
| 2 | UNVERIFIED | the mutation was sent and the project may have changed, but the change could not be verified |

Exit 2 covers:

- post-capture failed or silent
- a partially applied `batch` (the bridge keeps sub-commands that ran before
  the failure)
- a bridge rejection. The JSON carries the rejection code. A handler that
  failed mid-edit can leave a partial change inside one closed undo block,
  which looks the same from outside as a clean rejection.
- a mutation whose reply timed out or could not be read. It may have
  executed, or may execute later.
- pre and post captures that stopped being comparable because track identity
  or capture scope changed mid-verify

Nothing is rolled back automatically. One Ctrl/Cmd+Z reverts it. An agent
must not blindly retry on exit 2, because the change may already be live.

## Limits

- Bounds are frozen once, before the mutation. Pre and post captures use
  identical `start_seconds` and `duration_seconds`, so a moved cursor or time
  selection between captures cannot skew the comparison.
- With [Post Mortem](https://github.com/wretcher207/post-mortem) installed you
  get per-band spectrum, true peak, RMS, and stereo-image deltas. Without it,
  LUFS-I deltas only. The report labels its `metrics_source`.
- If either capture is not a verified isolated track (some tracks fall back
  to a full-mix render), the report says the deltas describe the capture
  scope. It never presents full-mix deltas as per-track evidence.
- A silent capture refuses a verdict rather than comparing dead air.
- Two renders per verify. Each capture blocks REAPER's UI for the render
  duration. Default is 10 seconds of audio. Keep `--seconds` short.
