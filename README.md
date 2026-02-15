# The Dungeons of Dork

This game was originally written as a ManyChat chatbot as part of a training class I ran teaching how to code old-school text RPGs. This project is the object-oriented Python 3 edition with a Tkinter UI.

## Current Gameplay Overview

The game loads base world data from CSV files in `src/data/`, then builds a run with randomized systems:

- Relic-gated win condition: collect Amulet, Dagger, and Book of Spells before exiting
- Dynamic room events via tags (`safe`, `trap`, `treasure`, `lore`, `dark`)
- Moving hostile NPCs with patrol and pathing behavior
- Weakness-based encounters and a multi-phase final boss
- Quest givers, faction reputation, XP, and perk unlocks
- Secret rune puzzle and shortcut route
- Timed hazards (temporary blocked directions) and Hunter activation
- Class-specific abilities (`fighter`, `scout`, `scholar`) unlocked via wins
- Run mutators (for example `Ironman`, `Fog of War`, `Rich Vaults`)
- Meta progression stored in `src/data/meta.json`
- Tkinter UI with a drawn map view, command entry, log panel, and inventory panel
- Tkinter action strip with state-aware buttons (movement, exploration, and combat actions)
- Tkinter item emojis in inventory and visible room tiles for faster visual scanning
- Tkinter player avatar emoji (class-based, with male/female fallback for adventurer)
- Tkinter emoji theme toggle (`Emoji: On/Off`) for map symbols, action labels, status line, and chronicle style
- Tkinter voice feedback toggle (`Voice: On/Off`) for spoken system messages (macOS `say`)

## Running The Game

From the repository root:

```bash
python3 src/DunDork.py
```

At startup:

1. A random mutator is selected.
2. You choose a class from currently unlocked classes.
3. The dungeon is prepared (room tags, item placement, NPC placement, boss setup).

## Core Loop Logic

Each turn generally follows this flow:

1. Enter/report room state (description, exits, objects, NPCs).
2. Resolve one-time room event.
3. Resolve any quest interactions in that room.
4. Trigger encounters if hostile NPCs are present.
5. Accept player command.
6. If command is a valid action, process end-of-turn systems:
   - turn counter increment
   - timed event spawn/check
   - NPC movement
   - ongoing effects (for example Cursed Idol drain)

The UI log is concise and panel-driven (map/status/inventory are shown visually), and uses a `Chronicle:` summary line after actions to highlight changes.

## Commands

Movement:

- `N`, `S`, `E`, `W`
- `north`, `south`, `east`, `west`
- `go north`, `move west`

Exploration and inventory:

- `look`
- `moves`
- `pickup <item>`
- `drop <item|slot>`
- `inventory`
- `map`
- `status`
- `quests`
- `log`
- `rune <word>`
- `style color`
- `style type`
- `help`
- `quit`

Combat:

- `attack`
- `flee`
- `use <item>`
- `use <item> with <item>` (synergies)
- `powerstrike` (fighter)
- `analyze` (scholar)

Class utility:

- `scan` (scout)

Tkinter map legend:

- `@` you
- `!` hostile
- `*` item present
- `.` explored room
- `?` unknown room
- unavailable directions are not drawn

## Tkinter Controls

The Tkinter client includes:

- command entry for free-form commands
- quick buttons (`Help`, `Status`, `Inventory`, `Map`)
- a state-aware action strip for movement, exploration, and combat
- an emoji theme toggle button to switch between classic and emoji-heavy UI styles
- a voice toggle button to speak system feedback (when available)

Action strip behavior:

- movement buttons enable only when that direction is valid (and not blocked)
- combat buttons (`Attack`, `Flee`, class combat actions) enable only during encounters
- class-specific buttons (`Powerstrike`, `Analyze`, `Scan`) enable only when relevant to your class/state
- prompt-driven actions (`Pickup`, `Drop`, `Use`, `Rune`) open a small input dialog

## Winning and Endings

You win by reaching the exit room after collecting required relics.

Ending text depends on run outcomes such as:

- quest completion
- lore discovered
- enemies defeated

On victory, meta progression is updated (wins, total XP, class unlocks, best ending).

## Testing

If `pytest` is installed in your active environment:

```bash
python3 -m pytest -q
```

The test file is located at `tests/test_dungeon_cli.py`.

## Notes

- The game data and persisted meta file live under `src/data/`.
- Check `src/data/map.png` for a visual layout reference.

Have fun, and as I'm fond of saying ... #StayFrosty :)

James Burchill

https://jamesburchill.com

*PS. Remember to take a closer look at the map.png for a better understanding of the game layout.*
