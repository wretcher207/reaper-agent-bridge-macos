# Mix recipes

Save a mix setup you like, then rebuild it for another song. Recipes contain
track order, folders, sends, levels, pans, plugin state and track automation.
Media items are excluded. Samples and impulse responses stay at their existing
paths; the recipe does not bundle them.

Stop playback before capture or rebuild.

```bash
python reaperd.py recipe capture my-mix.recipe.json
python reaperd.py recipe diff my-mix.recipe.json
python reaperd.py recipe rebuild my-mix.recipe.json --dry-run
python reaperd.py recipe rebuild my-mix.recipe.json
```

Capture requires a new filename. To update a recipe, capture another version.
Rebuild creates a separate, unsaved project tab and returns focus to the original.
It never replaces tracks in an existing mix. If loading fails, the partial tab
stays available for inspection. Do not retry a timed-out rebuild without checking
the open tabs first.

Diff compares tracks in order because routing depends on that order. It reports
changed state fields and exposed plugin parameters, using a normalized parameter
tolerance of 0.000001. Window layout and instance IDs are ignored.

Some plugins change their opaque state when loaded or inspected. These differences
are reported separately even when exposed parameters match. `settings_match` does
not prove those hidden states sound the same. Audition the rebuilt setup with your
new material before relying on it.

Exit 0 means a complete match or successful capture/preview. Exit 1 means an error;
a failed rebuild can leave a partial tab. Exit 2 means comparison found differences,
including opaque state that needs review.

Automation keeps its original song times and tempo map. Automation items are
currently refused because their shared pools are not captured. Recipes support
up to 256 ordinary tracks plus master and a 64 MB input file.

Project sample-rate settings are included. Other project defaults, including an
inherited pan law, are not captured; check those when moving between setups.

MCP exposes the same workflow as `mix_recipe`, with `action`, `path`, and optional
`dry_run`. The recipe file stays on the machine running the bridge.
