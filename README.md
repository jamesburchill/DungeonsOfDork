# The Dungeons of Dork

This game was originally written as a ManyChat chatbot as part of a training class I ran teaching how to code old-school text RPGs. This project is the object-oriented Python 3 CLI edition.

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

https://jcb.dev

*PS. Remember to take a closer look at the map.png for a better understanding of the game layout.*
