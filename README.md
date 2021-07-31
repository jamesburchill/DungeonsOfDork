# The Dungeons of Dork
***UNDER DEVELOPMENT***

Text-based role playing game. Python Edition.

### Variables

    GameOver            bool
    Location Invalid    bool
    GameWon             bool
    GameLost            bool

### Classes

#### Location

    ID
    N
    S
    W
    E
    isDark?
    Story
    Description
    OBJ ID [] List
    NPC ID [] List
    ---
    GetLocation

        Used to get data from sheet. If loaded into list of objects, no need - simply access Loc[i].attribute/method
        If loc 'missing' description, run GenLoc to fill it up.

    GenLoc

        Generate random text for locations that have none.
    
    ListDirectionChoices
    
        A method in a LOC obj that displays the available choices  
    
    LookAround
    
        A method in a LOC obj that reports on that location
    
    ListObjectsInLoc

        A method in a LOC obj that lists any object in that location

#### NonPlayerCharacter (NPC)

    ID
    Name
    Description
    Neutralizing OBJ ID
    canMove?
    startLocID
    currentLocID

#### Object

    ID
    Description
    Name
    Story (when colected)
    Required to Win?
    Is Collected (inBackPack?)

#### BackPack (Class or List)

    BackPack = [0,0,0,0,0] #Creates a list of 5 elements, each with NO ID. 0 means empty. 
    
    Capacity? 5 "slots"
    
    CheckInventory
    
        Lists off the OBJ's in the BackPack list.

    PickupObject

        Checks backpack. If space then ADD. Update LOC, remove object.
    
    DropObject

        Removes object from backpack. Adds OBJ ID to that LOC object.
       
### DunDork Functions/Methods

ShowInstructions

    Explain how the game is played 

LoadGameData

    Load data and setup game ...

MainGameLoop

    The heart of the game. Update, wait for input etc ...
    *** Accept INPUT, call various methods based on choices.

Move

    Check if direction is legit. If yes, Updates the Player's LOC.
    Run the "update" and report the game status.