# Develop

The CI matrix covers Windows, macOS, and Linux. From the repository root:

```bash
python -m pip install pytest
python -m pytest tests skills/drum-apparatus/tests -q
python -m py_compile reaperd.py reaper_mcp.py setup/install.py
lua bridge/test_bridge.lua
lua bridge/test_json.lua
```

The Lua checks require Lua 5.4. Live REAPER integration remains a separate
manual gate because CI does not launch the DAW.


## Layout

```text
bridge/reaper_agent_bridge.lua   the bridge (runs inside REAPER, OS-neutral)
bridge/bridge_config.json        machine-specific config (regenerated)
bridge/command_schema.md         full command reference
reaperd.py                       cross-platform agent CLI (Python 3)
reaper_mcp.py                    MCP stdio server over the same bridge
console_sidecar.py               Daemon Console broker (headless Claude session)
bridge/reaper_daemon_console.lua Daemon Console panel (ReaImGui, clone-only)
docs/CONSOLE.md                  console architecture + operating rules
setup/install.py                 wire auto-start into REAPER (cross-platform)
commands/examples/               one JSON example per command
skills/drum-apparatus/           DSL drum engine + kit-map auto-discovery
skills/guitar-apparatus/         guitar/bass riff notation + performance engine
inbox/ outbox/ processing/ ...   runtime folders
```

