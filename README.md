# The Dungeons of Dork

Dungeons of Dork is a Python dungeon crawler with a single Tkinter interface. The old text-only launcher has been removed. The game is now focused on a click-driven, visual-first UI.

## What Is In This Build

- Tkinter-only client entrypoint: `src/DunDork.py`
- Game logic module: `src/DunDorkCore.py`
- Data-driven world from CSV files in `src/data/`
- Dynamic runs with mutators, class abilities, quests, faction reputation, and boss phases
- Emoji-forward UI theme (toggleable)
- Optional spoken narration on macOS via `say`
- Single-slot autosave/resume (`src/data/savegame.json`)
- Meta progression (`src/data/meta.json`)

## Run The Game

From repo root:

```bash
python3 src/DunDork.py
```

At startup:

1. If a save exists, you are prompted to resume.
2. Otherwise a new run is created with a random mutator.
3. You pick from unlocked classes.

## UI Model

The interface is click-driven:

- Left panel: dungeon map
- Right panel: status strip, game chronicle, inventory
- Bottom panel: utility controls + action strip

The free-form text command entry was intentionally removed.

Actions requiring input (`Pickup`, `Drop`, `Use`, `Rune`) open a small prompt dialog.

## Map Rules

The map is a local room view centered on the player:

- Center tile is always the player
- Only currently connected cardinal directions are drawn
- Unknown rooms stay hidden as `?` until revealed
- Hostiles/items are only shown for revealed rooms
- Temporarily sealed paths show lock indicators
- Missing directions are not drawn

## Controls

Utility controls:

- `Help`
- `Avatar` (emoji chooser)
- `Emoji: On/Off`
- `Enable Voice` / `Disable Voice` (if voice is available)

Action strip controls:

- Movement: `N`, `S`, `E`, `W`
- Exploration: `Look`, `Pickup`, `Drop`, `Use`, `Rune`, `Quests`
- Combat: `Attack`, `Flee`, class combat actions (`Powerstrike`, `Analyze`)
- Class utility: `Scan` (scout)
- Exit run: `Quit`

Buttons are context-aware and disable when not relevant.

## Save Behavior

- The run autosaves after actions and on window close.
- There is one save slot per local copy.
- If a run ends (death/victory/quit), the active run save is cleared.

## Voice Feedback

Voice mode speaks narrative/system feedback only.

It skips UI helper lines and `Chronicle:` summary lines, and removes parenthetical metadata before speech.

## Project Layout

- `src/DunDork.py`: Tkinter app and UI behavior
- `src/DunDorkCore.py`: core game systems and rules
- `src/data/*.csv`: dungeon content
- `tests/test_dungeon_cli.py`: core logic tests (module-level, non-UI)

## Testing

If `pytest` is installed:

```bash
python3 -m pytest -q
```

## Notes

- Save/meta files are local runtime data and are gitignored.
- `src/data/map.png` remains a useful reference for world structure.

James Burchill  
https://jamesburchill.com
