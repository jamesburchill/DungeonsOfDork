# The Dungeons of Dork

This game was originally written as a ManyChat chatbot as part of a training class I ran teaching how to code 'old-school' text-based RPG's. This is the object-oriented Python 3 port. I have provided the data files that provide the structure for the game and other elements in the /src/data directory.

The game loads data from CSV files and now includes a more complete CLI gameplay loop:

- Required relic chain to unlock the exit (Amulet, Dagger, Book of Spells)
- Patrol NPCs with door blocking and weakness-based encounters
- Room tags and events (safe, trap, treasure, lore, dark)
- Quest givers, XP, perks, and alternate endings
- Short and full-text commands (`N`, `north`, `pickup torch`, `use amulet`, etc.)
- Boss fight with telegraphed multi-phase attacks
- Meta progression persisted in `src/data/meta.json` (class unlocks)
- Random mutators each run (e.g. Fog of War, Ironman, Rich Vaults)
- Item synergies (`use <item> with <item>`)
- Faction reputation effects, timed hazards, secrets, class abilities, combat log, and map reveal

Run from the repository root:

`python3 src/DunDork.py`

Run tests:

`python3 -m pytest -q`

The overall logic of the game is pretty straightforward:

1. Load the various data files.
2. Create 3 main lists: objects, npcs and locations. 
3. Finally, create a Player, and along with passing in the 3 object lists, start the game.
4. A While (not player.game_over) keeps the loop running.

I haven't bullet-proofed all the code, there are no 'type hints' (currently) and only some error trapping, and basic input validation and so on. There's plenty of opportunity to do more, and do it better. I just wanted to get the game running and the port stable. 

Have fun, and as I'm fond of saying ... #StayFrosty :)

James Burchill

https://jcb.dev

*PS. Remember to take a closer look at the map.png for a better understanding of the game layout.*
