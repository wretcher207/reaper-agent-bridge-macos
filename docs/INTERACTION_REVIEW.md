# Interaction review - 2026-09-07

## Result

The hidden bottleneck was REAPER's directory enumeration cache. The old scanner
started at index 0 but never invalidated the cache. Native index -1 forces refresh:
https://www.reaper.fm/sdk/reascript/reascripthelp.html#EnumerateFiles

Live Windows measurements, stopped empty Untitled project, 12 calls per probe:

| Probe | Median |
|---|---:|
| Original get_context | 558.34 ms |
| Faster polling before cache fix | about 530 ms |
| Cache fix, matching context probe | 29.53 ms |
| Final repeated context probe | 30.51 ms |
| Final snapshot probe | 32.16 ms |
| Final eight snapshots in one batch | 31.67 ms |

About 18x faster single-command interaction on this machine. Final raw samples
are in interaction-benchmark-2026-09-07.json. Repeat with:
`python tools/benchmark_interaction.py --count 12 --output results.json`.
This only reads the project. No audio capture, mix edit, transport change or paid
agent was used. Live reload timestamps and new-command replies proved the loaded
code. Mutation failure behavior was tested with mocked REAPER, not a live mix.
Loaded-project audio/UI performance and macOS/Linux timing remain unverified.

## Trace and real costs

CLI send_type normalizes aliases / resolves an installed FX name where requested,
then send_command fills ID/version/auth, removes a stale reply, writes .tmp and
publishes via os.replace. MCP _forward / _send uses that same sender. Lua scans,
claims into processing, parses/authenticates, publishes busy identity, dispatches
under protected undo, writes reply and archives/fails the input. Python polls the
exact result path, reads/removes it and parses JSON. MCP adds a JSON-RPC text
wrapper; it does not add another bridge hop. Process startup and model inference
are excluded from this benchmark.

The actual code already drained up to 50 files under a 30 ms budget, and already
had ordered batches. It was not one operation per tick. The 250 ms scan gate and
50 ms Python sleep added delay, but cache staleness caused the unexplained
half-second staircase. Instrumentation measured roughly 30-32 ms defer gaps,
0.05 ms simple handlers and 5-9 ms setup including claim/parse/heartbeat/log.
Python profiling put almost all pre-fix elapsed time in reply sleep. Publication
and JSON serialization are not separately measured.

## Implemented

- Refresh directory cache before enumeration; still ignore unfinished .tmp files.
- Scan every defer for two seconds after traffic; idle interval capped at 50 ms.
  adaptive_poll:false restores the configured legacy scan gate. This does not
  change REAPER's own defer frequency or spin the UI thread.
- Drain one file per tick during playback/recording, otherwise up to 50 under
  an 8 ms cooperative budget. A single command/batch can still exceed it.
- Python reply checks at 5 ms for the first second, then 25 ms, without OS deps.
- Reject malformed batch entries, nested batches and more than 128 operations
  before edits. Keep partial results with return_partial_results:true. Legacy
  fail-fast errors remain compatible. All-read batches create no undo point.
- get_mix_snapshot: bounded track pages, master, GUIDs, routing, FX state and
  optional first N parameter values, transport/selection, peak samples, pan
  law/mode, folder depth, envelope counts and project revision.
- Routing adds route indices, peer GUIDs and hardware output inspection.
- Non-object JSON now gets a typed failure instead of stranding before dispatch.
- Reply timing fields; CLI/MCP/schema/examples/installer defaults and tests.

## Findings and risk register

| Finding | Severity/status | Evidence and mitigation |
|---|---|---|
| Cached inbox hides new commands | High/fixed | Live benchmark and stale-cache regression |
| Malformed batch can escape before closing undo | High/fixed | sub.type was accessed outside pcall; validate all entries first |
| Stopped batch loses prior result details | High/fixed opt-in | Check data.all_ok and every result, not outer ok alone |
| Non-object JSON crashes before dispatch | Medium/fixed | Validate decoded root |
| Caller-supplied IDs can collide | High/open | Shared tmp/reply names; random default IDs avoid normal collisions |
| Crash after mutation before reply is ambiguous | High/open | Processing age rules are not an execution journal |
| Windows remove+rename replacement has a gap | Medium/open | Not fully atomic; readers tolerate missing file, singleton is advisory |
| Copy/remove fallback is not an atomic claim | Medium/open | Singleton reduces exposure; lifecycle revision needs rename-only claims |
| Both result publication attempts fail but input advances | High/open | process_file can archive after failed success and failure replies |
| Lexical file ordering is not enqueue order | Medium/documented | Use batch for causal ordering, not separate client IDs |
| Tick budget cannot preempt a handler | Medium/mitigated | Small batches/pages; enumeration and slow plugins can still stall |
| Pages are separate observations | Medium/documented | Revision token detects project changes; GUIDs remain authority |
| Undo does not cover disk/preferences | High/preserved | Existing separate gates remain; no automatic audio writes added |

Timeout may occur after execution. Never retry an uncertain mutation blindly.
No generic auto-undo was added: another actor can edit during measurement, and
blind global Undo may revert their work. Existing preview has targeted preimages
and explicit accept/cancel; general compensation needs conflict detection.

## Existing surface reviewed

get_context already sees master, selection, transport, markers and regions.
get_items reports item/source state and take FX. FX discovery supports input FX,
GUIDs, offline state and paginated parameters. Parameter writes support normalized
and searched display values with readback; repeated display searches can be
expensive. Track FX add/remove/move/bypass, sends/master-send, note edits and
parameter automation transactions already exist. No duplicate EQ wrapper was
added just to rename the existing Python EQ/setparam path.

verifyloop.py freezes ranges, checks provenance/silence and compares pre/post
loudness plus optional Post Mortem spectrum/stereo metrics. RENDER_STATS supplies
available loudness/true peak without numpy. Some item-based captures fall back
to full mix and must not be called isolated stems. Capture blocks the UI thread.
Profile can inspect saved RPP/media rather than live FX output; retain that caveat.
Drum/guitar generation converges on existing insertion paths; golden-rule drum
velocity enforcement is unchanged. No notes or velocities were written.

The console sidecar's headless agent uses this same MCP path; transcript/budget
logic is adjacent, not on a direct CLI hop. No paid console session was started.
There is no daemon screenshot command in this patch. Native peak samples are
orientation data, not RMS/LUFS/true-peak/phase or a silence verdict.

## Agent workflow

1. Use supplied console focus when sufficient; otherwise snapshot 16 tracks/page,
   parameters off. Retain track/FX GUIDs. Scan only parameters you intend to change.
   Restart paging if project revision changes.
2. Batch about 4-16 inexpensive operations. Keep dependent writes in one batch and
   finish with targeted readback/snapshot. Use stop_on_error:true and
   return_partial_results:true; inspect data.all_ok and each result. 128 is a hard
   ceiling, not a recommended workload. A partial batch does not roll back.
3. Measure only for audio claims, over the same frozen non-silent range and matching
   scope. Keep renders outside dense parameter batches; respect audio-write gates.
4. Use preview/accept/cancel for supported auditions. Recover generic partial edits
   with known preimages or the relevant single undo point.
5. Screenshot when waveform/layout/opaque plugin UI answers a question numbers
   cannot. Use an available external local capture tool explicitly; no screenshot
   endpoint has been invented or silently installed here.

## Precise implementation follow-ups

1. Durable journal first: request nonce + payload digest; exclusive ID reservation;
   accepted/executing/executed/published records. Never automatically replay an
   executing mutation after a crash; return OUTCOME_UNKNOWN with recovery identity.
   Rename-only claims and query_command_status on every surface. Test duplicate
   clients, every crash point, locked outbox and failed encoding/publication.
2. apply_mix_pass: whitelist reversible track/FX/send moves, resolve GUIDs and
   validate all ops, capture preimages, apply one undo block, return field diffs.
   expected_revision rejects stale plans. Compensation restores only fields still
   matching that transaction's writes; otherwise CONFLICT, never global Undo.
   Bind verifyloop acceptance to transaction ID. Test failure after every op and
   manual edits between captures.
3. Vision pages: selected parameter indices, item/envelope summaries, optional PDC
   and readable gain reduction. Total FX/parameter budgets plus continuation tokens
   for enormous chains. Revision diff cache keyed by project identity and GUID.
   Test 200-track fixtures, duplicate names, master/input FX and missing APIs.
4. Time-scoped taps: unify selection/bar/seconds resolution. Do not mislabel native
   audio accessors as post-FX. Optional local analyzer can avoid disk renders, but
   prove pre/post FX/fader isolation with known signals; preserve capture gates and
   silence/provenance checks. Test stereo metrics against deterministic references.
5. Optional capture_session_view: capability discovery; arrange/mixer/FX target;
   explicit output path and size cap; image metadata with window/GUID/time. MCP image
   content, CLI/raw metadata. Missing backend returns UNSUPPORTED_FEATURE. Test
   Retina, hidden windows, Linux Wayland denial and PNG readability. gfx's own
   canvas is not the REAPER framebuffer. No required SWS.
6. Routing updates/removal/hardware outs, sidechain maps, validated folder-bus plans,
   polarity/clip gain, preset/offline/take-FX writes. Require preimage/readback tests
   and simultaneous Lua/schema/CLI/MCP/example coverage for each command.
7. Optional transport spike: authenticated user-only Windows pipe/Unix socket vs
   the new ~31 ms baseline. REAPER calls stay on the main thread; sockets alone
   cannot bypass defer. A native extension needs platform builds, lifecycle and
   teardown tests. Ship only after measured extra benefit, keeping file IPC and
   one command schema. No LAN listener or cloud service.

These follow-ups are specified, not represented as implemented.

## Final verification

389 Python tests, 538 bridge Lua checks and 40 JSON checks passed; Lua compiles.
The final additional example-file/MCP live probe timed out after REAPER exited
(status confirmed no running process). Earlier live benchmarks and snapshot
responses succeeded. MCP forwarding is covered offline; this final live MCP probe
is not claimed as passed. No queued probe commands were retained after timeout.
