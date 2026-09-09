# Troubleshooting

## If a capture comes back silent or quiet

REAPER has a preference, **Preferences → Audio → "set media items offline when
application is not active"**, that unloads disk media whenever REAPER is not
the active application. It exists to save RAM and for normal hand-driven use it
is invisible.

It is not invisible to a daemon. Every command here arrives from another
process — the CLI, the MCP server, the console sidecar — so REAPER is *always*
in the background when it runs one. With that preference on, reads see unloaded
media and a capture can measure sources that are not loaded. Virtual
instruments are unaffected, because there is no file to unload, which is what
makes the symptom look like a plugin bug rather than a preference.

Check it and clear it:

```bash
python3 reaperd.py cmd get_context '{"include_fx":false}'
python3 reaperd.py cmd get_items '{"target_track_name":"Gtr L"}'
python3 reaperd.py cmd set_media_offline_when_inactive '{"enabled":false}'
python3 reaperd.py cmd set_all_media_online '{}'
```

`get_context` reports `media_offline_when_inactive`. `get_items` reports a
`source_state` per item: `loaded`, `offline` (REAPER is not loading a file that
is right there), `unresolved` (the file genuinely cannot be read — a different
problem with a different fix), or `midi`.

Two things worth knowing. `source_state` is **inferred**, not read — REAPER
exposes no ReaScript call for media-item offline state, so the bridge infers it
from a source reporting zero length and zero sample rate while its file still
opens, and ships `source_state_inferred: true` so nothing mistakes it for an
API read. And once media has been unloaded the state is **sticky**: it does not
come back from restoring or focusing the window, from starting playback, or
from turning the preference back off. `set_all_media_online` is what clears it.

`get_capture_preflight` warns when the preference is on, so a measurement never
quietly reports a number taken against unloaded media.

