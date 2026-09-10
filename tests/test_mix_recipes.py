import copy
import json

import pytest

import mix_recipes as recipes


def sample():
    return {"format": recipes.FORMAT, "bpm": 148, "numerator": 4, "denominator": 4,
            "tempo_markers": [], "tracks": [{"name": "MASTER", "is_master": True,
            "fx_parameters": [{"name": "Example", "enabled": True, "values": [0.5]}],
            "chunk": '<TRACK\nVOLPAN 1 0\n<FXCHAIN\nSHOW 0\nBYPASS 0\n<VST "Example"\nopaque\n>\n<PARMENV 0\nPT 0 0.5\n>\n>\n>\n'}]}


def test_capture_refuses_overwrite(tmp_path):
    path = tmp_path / "recipe.json"
    recipes.save(path, sample())
    with pytest.raises(FileExistsError):
        recipes.save(path, sample())
    assert recipes.load(path) == sample()


def test_layout_is_ignored_but_routing_is_not():
    a, b = sample(), sample()
    b["tracks"][0]["chunk"] = b["tracks"][0]["chunk"].replace("SHOW 0", "SHOW 9")
    assert recipes.diff(a,b)["matches"]
    b["tracks"][0]["chunk"] = b["tracks"][0]["chunk"].replace("VOLPAN 1 0", "VOLPAN 0.5 0\nAUXRECV 2 0 1")
    assert recipes.diff(a,b)["changes"][0]["fields"] == ["AUXRECV", "VOLPAN"]


def test_opaque_state_is_never_reported_verified():
    a, b = sample(), sample()
    b["tracks"][0]["chunk"] = b["tracks"][0]["chunk"].replace("opaque", "different")
    d = recipes.diff(a,b)
    assert d["settings_match"] and not d["matches"] and d["opaque_state_changes"]


def test_automation_change_is_definite_even_with_equal_parameters():
    a, b = sample(), sample()
    b["tracks"][0]["chunk"] = b["tracks"][0]["chunk"].replace("PT 0 0.5", "PT 0 0.9")
    d = recipes.diff(a,b)
    assert not d["settings_match"] and not d["opaque_state_changes"]


def test_parameter_quantization_tolerance_and_real_change():
    a, b = sample(), sample()
    b["tracks"][0]["fx_parameters"][0]["values"][0] += 1.2e-7
    assert recipes.diff(a,b)["matches"]
    b["tracks"][0]["fx_parameters"][0]["values"][0] += .01
    assert not recipes.diff(a,b)["settings_match"]


def test_rejects_media_and_malformed_recipe():
    r = sample()
    r["tracks"][0]["chunk"] = '<TRACK\n<ITEM\n<SOURCE WAVE\nFILE song.wav\n>\n>\n>\n'
    with pytest.raises(ValueError):
        recipes.validate(r)
    with pytest.raises(ValueError):
        recipes.validate({"format":"other"})


def test_failed_bridge_capture_does_not_write(tmp_path):
    p = tmp_path / "missing.json"
    result = recipes.run("capture",p,lambda *args:{"ok":False,"error":"offline"})
    assert not result["ok"] and not p.exists()


def test_rebuild_dry_run_and_verification(tmp_path):
    p = tmp_path / "recipe.json"
    recipes.save(p,sample())
    calls = []
    def sender(kind,payload):
        calls.append((kind,payload))
        return {"ok": True, "data": {"rebuilt": copy.deepcopy(sample())}}
    result = recipes.run("rebuild",p,sender)
    assert result["data"]["verified"]
    assert calls[0][0] == "rebuild_mix_recipe"
    recipes.run("rebuild",p,sender,dry_run=True)
    assert calls[-1][1]["dry_run"]


def test_default_tempo_marker_is_equivalent():
    a, b = sample(), sample()
    b["tempo_markers"] = [{"time":0,"bpm":148,"num":4,"denom":4,"linear":False}]
    assert recipes.diff(a,b)["matches"]
    b["tempo_markers"][0]["bpm"] = 150
    assert not recipes.diff(a,b)["matches"]


def test_mcp_uses_shared_recipe_path(monkeypatch, tmp_path):
    import reaper_mcp
    monkeypatch.setattr(reaper_mcp.reaperd,"send_type",lambda *args,**kwargs:{"ok":True,"data":sample()})
    result = reaper_mcp.tool_mix_recipe({"action":"capture","path":str(tmp_path/"mcp.json")})
    assert json.loads(result["content"][0]["text"])["ok"]
