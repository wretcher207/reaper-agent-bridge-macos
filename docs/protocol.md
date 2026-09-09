# Protocol

The file wire format. The CLI and the MCP server both speak it. Write it
yourself only if you are driving the bridge from something else. Every rule
here is load-bearing.

## A command is one JSON file in `inbox/`

```json
{
  "id": "agent-2026-08-17T21-14-03-9f2c",
  "type": "set_track_volume",
  "version": 3,
  "created_at": "2026-08-17T21:14:03-04:00",
  "payload": { "target_track_name": "Kick", "volume_db": -3.0 }
}
```

| Field | Rule |
| --- | --- |
| `id` | Timestamp-prefixed: `agent-YYYY-MM-DDTHH-MM-SS-hex`. Inbox order is a lexical sort of filenames, so the stamp is what makes commands run in the order you wrote them. The retention sweep parses the same stamp to find the oldest files. A random id runs at an arbitrary point and ages unpredictably. |
| `created_at` | Required. If the bridge dies mid-command the file stays in `processing/`. At startup the triage reads `created_at` and refuses to re-run anything stale. Without it, the bridge cannot tell and re-runs. |
| `version` | Must be `3`. Anything else returns `UNSUPPORTED_VERSION`. |
| `token` | Required only when `auth_token` is set in `bridge/bridge_config.json`. Missing or wrong returns `AUTH_FAILED`. |

## Publish with a rename

Write `<id>.json.tmp`, then rename it to `<id>.json`. The bridge scans for
`.json` and skips `.tmp`, so the rename is what publishes the command.
Writing straight to `.json` races the poll loop and can hand the bridge half
a file.

## Replies

Replies land in `outbox/<id>.json`, usually within one poll tick. The loop
runs four times a second. A render blocks it for the length of the render,
and `bridge/heartbeat.json` carries `busy` while that happens.

Delete each reply after you read it. The retention sweep never touches
`outbox/`, because a count-based sweep there would delete replies an agent
had not polled yet. Uncollected replies stay forever. Cleaning up is the
reader's job.

## Lifecycle

Command files move from `inbox/` to `processing/`, then to `archive/` on
success or `failed/` on error. The sweep bounds those folders.
