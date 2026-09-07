"""Read-only live IPC benchmark; does not start REAPER, render, or edit a project."""
import argparse
import json
from pathlib import Path
import statistics
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import reaperd


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=12)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not 1 <= args.count <= 100:
        parser.error("--count must be 1..100")
    if not reaperd.status_ok(quiet=True):
        raise SystemExit("Bridge is not live")
    results = {}
    for label, kind, payload in (
        ("context", "get_context", {"include_fx": False}),
        ("snapshot", "get_mix_snapshot", {"limit": 16}),
        ("eight_reads", "batch", {"commands": [
            {"type": "get_mix_snapshot", "payload": {"limit": 16}}
            for _ in range(8)], "return_partial_results": True}),
    ):
        samples = []
        timings = []
        for _ in range(args.count):
            started = time.perf_counter()
            reply = reaperd.send_type(kind, payload)
            samples.append(round((time.perf_counter() - started) * 1000, 3))
            if not reply.get("ok") or reply.get("data", {}).get("all_ok") is False:
                raise RuntimeError(reply)
            timings.append(reply.get("timing"))
        results[label] = {"samples_ms": samples,
                          "median_ms": statistics.median(samples),
                          "bridge_timings": timings}
    text = json.dumps(results, indent=2)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()

