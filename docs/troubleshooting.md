# Troubleshooting

## The bridge reports STALE right after launch

REAPER takes close to a minute after launch before startup scripts run. A
stale heartbeat inside the first minute is not a failure. Wait, then run
`python3 reaperd.py status` again. If it stays stale, confirm
`bridge/heartbeat.json` exists and that the bridge action is loaded
(see [Install](install.md)).

## A capture comes back silent or quiet

REAPER has a preference, **Preferences > Audio > "set media items offline
when application is not active"**, that unloads disk media whenever REAPER
is not the active application. For hand-driven use it is invisible.

It is not invisible to a daemon. Every command arrives from another process,
so REAPER is always in the background when it runs one. With that preference
on, a capture can measure sources that are not loaded. Virtual instruments
are unaffected because there is no file to unload, which makes the symptom
look like a plugin bug instead of a preference.

Check it and clear it:

```bash
python3 reaperd.py cmd get_context '{"include_fx":false}'
python3 reaperd.py cmd get_items '{"target_track_name":"Gtr L"}'
python3 reaperd.py cmd set_media_offline_when_inactive '{"enabled":false}'
python3 reaperd.py cmd set_all_media_online '{}'
```

`get_context` reports `media_offline_when_inactive`. `get_items` reports a
`source_state` per item:

| State | Meaning |
| --- | --- |
| `loaded` | fine |
| `offline` | REAPER is not loading a file that is right there |
| `unresolved` | the file cannot be read at all. Different problem, different fix. |
| `midi` | no audio source |

Two things to know:

- `source_state` is inferred, not read. REAPER exposes no ReaScript call for
  media-item offline state, so the bridge infers it from a source reporting
  zero length and zero sample rate while its file still opens. It ships
  `source_state_inferred: true` so nothing mistakes it for an API read.
- Once media is unloaded the state is sticky. Focusing the window, starting
  playback, or turning the preference back off does not restore it.
  `set_all_media_online` is what clears it.

`get_capture_preflight` warns when the preference is on, so a measurement
never quietly reports a number taken against unloaded media.
