# studio-arcade

Eight constraint-deduction puzzle games. Each shipped with verified correctness, difficulty calibration, legibility, and soft-lock fuzz testing.

**Live:** https://brotatotes.github.io/studio-arcade/

## Games

- [Lanternkeep](https://brotatotes.github.io/studio-arcade/lanternkeep/) — 1-bit stealth
- [Nonogram](https://brotatotes.github.io/studio-arcade/nonogram/) — picross / griddler
- [Slitherlink](https://brotatotes.github.io/studio-arcade/slitherlink/) — single closed loop
- [Hashi](https://brotatotes.github.io/studio-arcade/hashi/) — bridges between islands
- [Sudoku](https://brotatotes.github.io/studio-arcade/sudoku/) — classic 9×9
- [Akari](https://brotatotes.github.io/studio-arcade/akari/) — light up
- [Shikaku](https://brotatotes.github.io/studio-arcade/shikaku/) — rectangle partition
- [Star Battle](https://brotatotes.github.io/studio-arcade/starbattle/) — 1★ variant

## Layout

```
/index.html              landing
/games.json              manifest (single source of truth)
/<game>/index.html       playable bundle
/<game>/bundle.js
/<game>/about.html       generated info page
/scripts/render.py       static-site generator
/scripts/deploy-game.sh  per-game deploy
```

## Deploying a game

Each game has a source `dist/` produced by its own project repo. To publish:

```bash
scripts/deploy-game.sh <game-slug>
```

This:
1. Verifies `<slug>` is in `games.json`
2. Copies `dist/index.html` and `dist/bundle.js` into `/<slug>/` (and injects an "← arcade" nav bar)
3. Regenerates `/index.html` and every `/<game>/about.html` from `games.json`
4. Commits and pushes

The script is idempotent — re-running with no changes is a no-op.

Source dist path defaults to `~/.openclaw/workspace/studio/projects/<slug>/game/dist`. Override with `STUDIO_PROJECTS=/some/path`.

## License

MIT — see `LICENSE`.
