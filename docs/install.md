# Install

Requires REAPER and Python 3.8+ (no pip packages needed).

```bash
git clone https://github.com/wretcher207/reaper-daemon.git
cd reaper-daemon
python3 setup/install.py        # macOS/Linux  (use `python` on Windows)
```

`setup/install.py` detects your OS, locates REAPER's per-user resource
directory, and writes a marker-delimited block into `Scripts/__startup.lua`
that auto-loads the bridge on every launch, pointing at this clone. It is
idempotent — re-run it any time you move the repo. Then **(re)start REAPER**.

Options:

```bash
python3 setup/install.py --dry-run     # preview, change nothing
python3 setup/install.py --uninstall   # remove the managed auto-start block
python3 setup/install.py --bridge-root /path/to/clone
REAPER_RESOURCE_PATH=/custom/dir python3 setup/install.py
```

Prefer to load it manually instead of at startup? In REAPER:
`Actions > Show action list > ReaScript: Load…`, pick
`bridge/reaper_agent_bridge.lua`, run it once. It runs as a background deferred
script and regenerates `bridge/bridge_config.json` and its working folders on
first run.

## Via ReaPack (REAPER-native, alternative)

Prefer REAPER's own package manager? Add this repo to ReaPack:

1. In REAPER: `Extensions > ReaPack > Import repositories`.
2. Paste: `https://github.com/wretcher207/reaper-daemon/raw/main/index.xml`
3. `Extensions > ReaPack > Browse packages`, find **Reaper Daemon**, install.

ReaPack 3.19.0 includes both bridge Lua files, the two workflow skills, and the
MIDI note writer. These installation details still apply:

- **It does not auto-start.** ReaPack installs the bridge as an Action but does
  not run it on launch. Run the action once per session, or add it to your
  `Scripts/__startup.lua` (`python3 setup/install.py` from a clone does this
  for you).
- **You still need the rest of the package.** `reaperd.py` (the agent CLI),
  `commands/examples/`, and `skills/drum-apparatus/` (the drum DSL engine) are
  NOT installed by ReaPack. For those, also clone the repo:
  `git clone https://github.com/wretcher207/reaper-daemon.git` and point your
  agent at the clone (or run `python3 setup/install.py` from the clone, which
  handles auto-start too). ReaPack keeps the bridge and bundled skills updated.
- **Point your agent at the install folder.** ReaPack installs to
  `<REAPER resource>/Scripts/reaper-daemon/`. Right-click the package in
  ReaPack and "Show in explorer/finder" to get the exact path, then aim your
  agent at that folder.

## Verify it

With REAPER open and a project loaded:

```bash
python3 reaperd.py status
python3 reaperd.py send commands/examples/get_context.json --wait
```

`status` reports the bridge heartbeat; `send --wait` prints a JSON result
describing the open project. If it times out, check that
`bridge/heartbeat.json` exists and is fresh.

Still not right? See [Troubleshooting](troubleshooting.md).
