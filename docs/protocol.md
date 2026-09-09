# Agent protocol — the file wire format

`reaperd.py` and the MCP server both speak this; write it yourself only if you
are driving the bridge from something else. Every rule below is load-bearing —
the bridge relies on it somewhere.

**A command is one JSON file in `inbox/`.**

```json
{
  "id": "agent-2026-08-17T21-14-03-9f2c",
  "type": "set_track_volume",
  "version": 3,
  "created_at": "2026-08-17T21:14:03-04:00",
  "payload": { "target_track_name": "Kick", "volume_db": -3.0 }
}
```

- **`id` must be timestamp-prefixed**, `agent-YYYY-MM-DDTHH-MM-SS-hex`. Inbox
  order is a lexical sort of filenames, so the stamp is what makes commands run
  in the order you wrote them, and the retention sweep parses that same stamp to
  find the oldest files to drop. A random id runs at an arbitrary point and
  ages unpredictably.
- **`created_at` is required.** If the bridge dies mid-command, the file is left
  in `processing/`; at startup the triage reads `created_at` and refuses to
  re-run anything stale rather than replaying an edit into a session that has
  moved on. No `created_at` means it cannot tell, and re-runs.
- **`version` is `3`.** Anything else is rejected with `UNSUPPORTED_VERSION`.
- **`token`** is required only when `auth_token` is set in
  `bridge/bridge_config.json`; without it the reply is `AUTH_FAILED`.

**Write `<id>.json.tmp`, then rename it to `<id>.json`.** The bridge scans for
`.json` and skips `.tmp`, so the rename is what publishes the command. Writing
straight to `.json` races the poll loop and can hand the bridge half a file.

**Replies land in `outbox/<id>.json`**, usually within a poll tick (the loop
runs four times a second; a render blocks it for the length of the render, and
`bridge/heartbeat.json` carries `busy` while that happens). **Delete each reply
after you read it.** The retention sweep deliberately never touches `outbox/`,
because a count-based sweep there would delete replies an agent had not polled
yet — so uncollected replies stay forever, and cleaning up is the reader's job.

Command files themselves move `inbox/` → `processing/` → `archive/` (ok) or
`failed/` (error); those the sweep does bound.

