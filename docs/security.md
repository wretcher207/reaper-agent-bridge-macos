# Security

The bridge is a **local file** control channel: any process that can write to
`inbox/` can drive REAPER (load FX, change tracks, render). That's fine for a
single-user dev box, which is what it's built for. Two rules keep it that way:

- **Keep the bridge folder local.** Don't put it on a network share, a synced
  drive, or anywhere another machine/user can write. That's the real boundary.
- Mutating commands run inside REAPER undo blocks, so anything an agent does is
  `Cmd/Ctrl+Z`-reversible.

**Optional shared-secret token.** On a shared or less-trusted box you can require
a token: set `auth_token` to any string in `bridge/bridge_config.json`. The
bridge then rejects any command without a matching `token` (`AUTH_FAILED`), and
`reaperd.py` reads the same config and attaches it automatically — no other
setup. Honest limit: the token lives in a local-readable config, so it stops
*accidental or other-app* writes, **not** a local attacker who can read that
file. Keeping the folder local is still the actual protection.

