# The agent CLI — `reaperd.py`

One Python entry point for everything an agent does (no shell helpers, no
`jq`/`grep` pipelines — works identically on macOS, Windows, Linux):

```bash
python3 reaperd.py status                       # liveness check (run first)
python3 reaperd.py send <cmd.json> --wait       # send a command file
python3 reaperd.py cmd <type> '<payload-json>'  # send by type + payload
python3 reaperd.py fxload "<plugin query>" <track|master>
python3 reaperd.py save-chain <track|master> [--name NAME] [--overwrite]   # live FX chain -> .RfxChain
python3 reaperd.py snapshot-chains [--prefix P] [--overwrite] [--dry-run]  # every track with FX
python3 reaperd.py setparam <track> "<fx>" "<param>" "<display value>"
python3 reaperd.py eq <track> "<fx>" <band> <freqHz> <gaindB> [Q]
python3 reaperd.py measure <track> [--seconds N] [--start S] [--json]
python3 reaperd.py verify <track> [--seconds N] [--json] -- <type> '<payload-json>'
python3 reaperd.py profile <project.rpp> <track> [--start-bar N] [--bars N] [--max-seconds S]
python3 reaperd.py groove <beat.dsl> --track Drums [--position SEC] [--map NAME]
python3 reaperd.py jam                          # DSL drum beat from stdin -> selected track
python3 reaperd.py humanize --track Drums [--amount 0-100] [--follow-lead] [--dry-run]
python3 reaperd.py shred --track argent-l [--part guitar|bass] [--bars-file riff.txt] [--seed N]
python3 reaperd.py band                         # 2 guitars + bass + drums, one command
python3 reaperd.py list-maps                    # available drum-kit maps
python3 reaperd.py discover-map <track> [--save <name>]
python3 reaperd.py add-map <name> --file <map.json>   # or --roles '{...}' / stdin
python3 reaperd.py remove-map <name>
```

`fxload` and `cmd add_fx` resolve a fuzzy plugin query to REAPER's exact
installed name from the VST/CLAP/AU cache before loading. `setparam` works on
any plugin by parameter index, binary-searching the normalized value that
produces a target display value, then verifying.

`measure` captures one track once (behind the same `allow_audio_writes` gate
as `capture_track_audio`) and prints measured audio metrics: LUFS-I whenever
REAPER reports it (digital silence reads as null and is flagged), plus — when
[Post Mortem](https://github.com/wretcher207/post-mortem) is installed —
sample peak, RMS, crest factor, 1/3-octave spectrum, stereo image, and a
silence check. Bounds are resolved once (time selection start if active, else
edit cursor; override with `--start`) and passed explicitly; to compare two
separate runs of the same spot, pass the same `--start`/`--seconds` to both.
The output labels its `metrics_source` (`postmortem` or `render_stats`) and
its capture scope — full-mix fallbacks are reported honestly, never presented
as per-track evidence.

