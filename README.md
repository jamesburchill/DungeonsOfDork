# The Dungeons of Dork

This game was originally written as a ManyChat chatbot as part of a training class I ran teaching how to code 'old-school' text-based RPG's. This is the object-oriented Python 3 port. I have provided the data files that provide the structure for the game and other elements in the /src/data directory.  

The game uses Pandas to load the data and subsequently creates various lists of objects. The game runs and you can explore the map, pickup and drop objects, look about and more. The NPC logic has been stubbed out and you are welcome to read the code and create your own handlers. 

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