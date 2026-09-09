# MCP server — talk to REAPER in plain English

`reaper_mcp.py` wraps the same file bridge as an
[MCP](https://modelcontextprotocol.io) stdio server, so any MCP client can
drive REAPER conversationally. Zero dependencies, no network listener — it
translates tool calls into the same inbox/outbox files, with the same safety
semantics (undo blocks, `dry_run`, risk gating).

Claude Code:

```bash
claude mcp add reaper -- python3 /path/to/reaper-daemon/reaper_mcp.py
```

(Use `python` instead of `python3` on Windows if that's what is on PATH.)

Claude Desktop (`claude_desktop_config.json`):

```json
{ "mcpServers": { "reaper": {
    "command": "python",
    "args": ["C:/path/to/reaper-daemon/reaper_mcp.py"] } } }
```

Then just ask: *"add a ReaEQ to the bass and carve 2 dB at 300 Hz"*, *"what
plugins are on the master?"*, *"program a d-beat groove at bar 33"*.

29 tools: project/FX discovery (`get_context`, `scan_fx`,
`get_fx_parameters`, `get_track_routing`), transport, tracks, FX chains,
`set_fx_param` (formatted values like `"-16.00 dB"` work), independent
automation-envelope readback (`get_fx_param_automation`) and writes,
markers/regions, MIDI insertion, `batch` (one undo block),
post-FX stem capture, the drum-workflow trio (`profile_track` and
`riff_grid`, which analyze a guitar stem out of the SAVED `.rpp` on disk
rather than REAPER's live project, a caveat every payload carries, plus
`insert_groove`, which renders a drum DSL to MIDI and inserts it in one
call), the part-writing trio (`insert_riff` for one humanized guitar or
bass part, `cut_band` for the whole four-track jam with per-leg results,
`humanize_take` for dynamics and micro-timing on a take already on a
track, `--follow-lead` included), the closed-loop pair — `verify_change` (run one
mutation with measured pre/post proof, see
[Closed-loop verify](verify.md))
and `tune_param` (iteratively search a parameter until a measured target
like "bass LUFS-I down 3 dB" is hit; a baseline render plus up to 5
iteration renders — 6 total — with honest converged/unconverged/
non-monotone reporting) — and, with
[Post Mortem](https://github.com/wretcher207/post-mortem) installed,
`analyze_track` / `compare_tracks`, which hand the calling model measured
mix data (LUFS, true peak, spectrum, stereo image, masking table) to
diagnose. Mutations are undoable with Ctrl/Cmd+Z (single commands and
batches are one undo step each; `tune_param` leaves one undo point per
iteration set); destructive tools ask the model to confirm intent; audio
capture stays behind the `allow_audio_writes` config gate (turn it on with
`python3 setup/install.py --allow-audio-writes`, then send `reload_bridge`;
saving the project and writing REAPER preferences are separate gates, so
measuring never requires granting those).

FX discovery returns REAPER's real track and FX GUIDs alongside names and
indices. Use the GUIDs as stable identity when planning a later change: names
can be duplicated, and indices move when a user edits the chain. The exact
identity fields and compatibility rules are documented in
[`bridge/command_schema.md`](../bridge/command_schema.md#stable-discovery-identities).

Post Mortem Phase 1 consumes these read-only identities to validate structured
recommendations. Reaper Daemon does not preview or apply those recommendations;
its existing mutation commands remain explicit, independently authorized bridge
operations. Reaper Daemon stays MIT-licensed and local. Planned hosted Post
Mortem services or UI do not move this bridge behind a commercial boundary.

