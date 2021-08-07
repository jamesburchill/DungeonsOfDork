# The Dungeons of Dork

This game was originally written as a ManyChat chatbot, and this is the object oriented Python port. The chatbot edition of DoD (** Currently not active at the moment **) was/is available here: https://manychat.com/l13/jamescburchill 

DoD has been written in Python 3 and requires the various data files in the /data directory and uses Pandas to load them and subsequently create various lists of objects. You'll see inside the code :)

The game runs and you can explore the map, pickup and drop objects, look about and more. The NPC logic has been stubbed out and you are welcome to read the code and create your own handlers. 

The overall logic of the game is pretty straightforward:

Load the various data files.
Spin up 3 main lists: objects, npcs and locations
(The lists are comprised of OBJECTS, you'll see.)
Finally, the main class: Player is created, and along with passing in the 3 object lists, starts the game.
A While not player.game_over keeps the loop running.

I haven't bullet-proofed all the code, there is some error trapping, input validation and so on. I know there's plenty of opportunity to do more, and do it better. I just wanted to get the game running and the port stable. Mission accomplished :)

Have fun, and as I'm fond of saying ... #StayFrosty :)

James Burchill 

[August 7, 2021]

http://JamesBurchill.com

PS. Remember to take a closer look at the map.png for a better understanding of the game layout.