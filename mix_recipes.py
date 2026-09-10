"""Local recipe files and semantic track-state comparison. Standard library only."""
import hashlib
import json
import math
from pathlib import Path

FORMAT = "reaper-mix-recipe-v1"
UI_KEYS = {"PEAKCOL", "BUSCOMP", "SHOWINMIX", "TRACKHEIGHT", "SEL", "LASTSEL",
           "WNDRECT", "FLOATPOS", "SHOW", "DOCKED", "TRACKID", "FXID", "EGUID"}
PARAM_TOLERANCE = 1e-6


def sections(chunk):
    """Compare state by top-level field/block without exposing plugin blobs."""
    result, stack, body, key = {}, [], [], None
    for raw in chunk.splitlines():
        line = raw.strip()
        if not line:
            continue
        token = line.split()[0]
        if len(stack) == 1 and line != ">":
            key = token.lstrip("<")
            body = []
        # Ignore UI/identity only outside opaque plugin bodies.
        ignored = token in UI_KEYS and (len(stack) == 1 or stack[-1:] in (["FXCHAIN"], ["FXCHAIN_REC"]))
        ignored = ignored or (len(stack) == 1 and line == "LANEREC -1 -1 -1 0")
        if not ignored and len(stack) >= 1 and line != ">":
            body.append(line)
        if line.startswith("<") and not line.endswith(">"):
            stack.append(token[1:])
        elif line == ">":
            if not stack:
                raise ValueError("Unbalanced track chunk")
            stack.pop()
            if len(stack) >= 1:
                body.append(line)
        if len(stack) == 1 and key and body:
            result.setdefault(key, []).append("\n".join(body))
            body = []
    if stack:
        raise ValueError("Incomplete track chunk")
    return result


def parameters_match(a, b):
    if a is None or b is None:
        return False
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        if {k:v for k,v in x.items() if k != "values"} != {k:v for k,v in y.items() if k != "values"}:
            return False
        if len(x["values"]) != len(y["values"]):
            return False
        if any(not math.isclose(u,v,rel_tol=0,abs_tol=PARAM_TOLERANCE) for u,v in zip(x["values"],y["values"])):
            return False
    return True


def fx_structure(blocks):
    """Retain host automation/bypass/routing, replacing opaque plugin contents."""
    result = []
    for block in blocks or []:
        stack, lines = [], []
        for line in block.splitlines():
            token = line.split()[0]
            in_plugin = any(k in {"VST", "AU", "CLAP", "JS", "DX", "VIDEO_EFFECT"} for k in stack)
            if not in_plugin:
                lines.append(line)
            if line.startswith("<") and not line.endswith(">"):
                stack.append(token[1:])
            elif line == ">":
                stack.pop()
        result.append(lines)
    return result


def validate(recipe):
    if not isinstance(recipe, dict) or recipe.get("format") != FORMAT:
        raise ValueError("Unsupported recipe format")
    tracks = recipe.get("tracks")
    if not isinstance(tracks, list) or not 1 <= len(tracks) <= 257:
        raise ValueError("Recipe must contain tracks and one master")
    if any(not isinstance(t, dict) for t in tracks):
        raise ValueError("Invalid track record")
    if sum(bool(t.get("is_master")) for t in tracks) != 1 or not tracks[-1].get("is_master"):
        raise ValueError("Recipe master must be last")
    for t in tracks:
        chunk = t.get("chunk")
        if not isinstance(chunk, str) or not (chunk.startswith("<TRACK\n") or chunk.startswith("<TRACK ")):
            raise ValueError("Invalid track chunk")
        if "ITEM" in sections(chunk):
            raise ValueError("Recipe contains media or a missing track chunk")
        if "\nPOOLEDENVINST " in chunk:
            raise ValueError("Automation items are not supported")
    return recipe


def load(path):
    if Path(path).stat().st_size > 64_000_000:
        raise ValueError("Recipe exceeds 64 MB")
    def invalid_constant(value):
        raise ValueError("Nonfinite number in recipe: " + value)
    return validate(json.loads(Path(path).read_text(encoding="utf-8"), parse_constant=invalid_constant))


def save(path, recipe):
    validate(recipe)
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(recipe, indent=2, allow_nan=False) + "\n"
    # Exclusive create: capturing an update always requires a new filename.
    with path.open("x", encoding="utf-8") as f:
        f.write(text)
    return {"path": str(path), "tracks": len(recipe["tracks"])-1,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def diff(expected, actual):
    validate(expected)
    validate(actual)
    changes, opaque = [], []
    # Ordinal mapping is intentional: sends in track chunks reference track order.
    for i in range(max(len(expected["tracks"]), len(actual["tracks"]))):
        a = expected["tracks"][i] if i < len(expected["tracks"]) else None
        b = actual["tracks"][i] if i < len(actual["tracks"]) else None
        if a is None or b is None:
            changes.append({"track": (a or b)["name"], "change": "missing" if b is None else "extra"})
            continue
        x, y = sections(a["chunk"]), sections(b["chunk"])
        fields = sorted(k for k in x.keys() | y.keys() if x.get(k) != y.get(k))
        params_equal = parameters_match(a.get("fx_parameters"), b.get("fx_parameters"))
        if not params_equal:
            fields.append("fx_parameters")
        # Opaque changes may be learned DSP state or merely plugin UI state.
        # Never call them equivalent just because exposed parameters match.
        for key in ("FXCHAIN", "FXCHAIN_REC"):
            if key in fields and params_equal and fx_structure(x.get(key)) == fx_structure(y.get(key)):
                opaque.append({"track": a["name"], "field": key, "exposed_parameters_match": True})
                fields.remove(key)
        if fields:
            changes.append({"track": a["name"], "actual_track": b["name"], "fields": fields})
    # A default time-zero marker and no explicit map represent the same grid.
    def tempo(r):
        markers = r.get("tempo_markers") or []
        if not markers:
            markers = [{"time": 0, "bpm": r["bpm"], "num": r["numerator"], "denom": r["denominator"], "linear": False}]
        return [{k: m[k] for k in ("time", "bpm", "num", "denom", "linear")} for m in markers]
    if tempo(expected) != tempo(actual):
        changes.append({"track": "PROJECT", "fields": ["tempo_map"]})
    for key in ("sample_rate", "sample_rate_use"):
        if expected.get(key) != actual.get(key):
            changes.append({"track": "PROJECT", "fields": [key]})
    return {"matches": not changes and not opaque, "settings_match": not changes,
            "changes": changes, "opaque_state_changes": opaque,
            "parameter_tolerance": PARAM_TOLERANCE,
            "comparison": "Track order, settings, routing, plugin state and automation; ignores UI layout and instance IDs"}


def run(action, path, sender, dry_run=False):
    if dry_run and action != "rebuild":
        raise ValueError("--dry-run applies only to rebuild")
    if action == "capture":
        if Path(path).exists():
            raise FileExistsError("Recipe already exists; capture updates to a new filename")
        reply = sender("capture_mix_recipe", {})
        if not reply.get("ok"):
            return reply
        return {"ok": True, "data": save(path, reply["data"])}
    recipe = load(path)
    if action == "diff":
        reply = sender("capture_mix_recipe", {})
        return {"ok": True, "data": diff(recipe, reply["data"])} if reply.get("ok") else reply
    if action != "rebuild":
        raise ValueError("Unknown recipe action")
    reply = sender("rebuild_mix_recipe", {"recipe": recipe, "dry_run": dry_run})
    if reply.get("ok") and not dry_run:
        data = reply["data"]
        comparison = diff(recipe, data.pop("rebuilt"))
        data["verification"] = comparison
        data["verified"] = comparison["matches"]
    return reply
