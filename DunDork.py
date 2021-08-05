""" This is the MAIN file for Dungeons of Dork (Python Edition.)
    Copyright 2021 (c) JamesBurchill.com
"""
import pandas
import pandas as pd

TEST_MODE = True  # used to print out stuff during dev/testing ...
current_loc = 0


class Location:
    """Locations in the DOD game"""

    def __init__(self, loc):
        if pandas.isna(loc["LOC_ID"]):
            self.ID = 0
        else:
            self.ID = int(loc["LOC_ID"])
        if pandas.isna(loc["LOC_N"]):
            self.N =  0
        else:
            self.N = int(loc["LOC_N"])
        if pandas.isna(loc["LOC_S"]):
            self.S =  0
        else:
            self.S = int(loc["LOC_S"])
        if pandas.isna(loc["LOC_W"]):
            self.W =  0
        else:
            self.W = int(loc["LOC_W"])
        if pandas.isna(loc["LOC_E"]):
            self.E =  0
        else:
            self.E = int(loc["LOC_E"])
        if pandas.isna(loc["LOC_IS_DARK"]):
            self.IsDark =  0
        else:
            self.IsDark = loc["LOC_IS-DARK"]
        if pandas.isna(loc["LOC_STORY"]):
            self.Story =  ""
        else:
            self.Story = loc["LOC_STORY"]
        if pandas.isna(loc["LOC_DESC"]):
            self.Desc = ""
        else:
            self.Desc = loc["LOC_DESC"]
        if pandas.isna(loc["LOC_OBJ_ID"]):
            self.ObjectID = 0
        else:
            self.ObjectID = loc["LOC_OBJ_ID"]
        if pandas.isna(loc["LOC_NPC_ID"]):
            self.NpcID = 0
        else:
            self.NpcID = loc["LOC_NPC_ID"]


    def location_details(self, loc):
        ...

    def direction_choices(self, loc):
        ...

    def objects_in_location(self, loc):
        ...


class Object:
    """Objects in the DOD game"""

    def __init__(self, obj):
        self.ID = obj["OBJ_ID"]
        self.Desc = obj["OBJ_DESC"]
        self.Name = obj["OBJ_NAME"]
        self.Story = obj["OBJ_NARRATIVE"]  # Narrative when collected
        self.RequiredToWin = obj["OBJ_WIN"]
        self.inBackPack = False


class NPC:
    """Non Player Characters"""

    def __init__(self, n):
        self.ID = n["NPC_ID"]
        self.Name = n["NPC_NAME"]
        self.Desc = n["NPC_DESC"]
        self.ObjectID = n["NPC_OBJID"]  # Kryptonite to this NPC
        self.CanMove = n["NPC_CAN_MOVE"]
        self.StartLocationID = n["NPC_START_LOC_ID"]
        self.CurrentLocationID = n["NPC_CURRENT_LOC_ID"]


class Genloc:
    """Arbitrary text for the game locations"""

    def __init__(self, gl):
        self.ID = gl["GEN_LOC_ID"]
        self.Story = gl["GEN_STORY"]
        self.Desc = gl["GEN_DESC"]


def spaces_available(backpack):
    """Ensure there's space in the backpack"""
    ...


def inventory_list(backpack):
    ...


def object_collected(object_id):
    ...


def object_dropped(object_id):
    ...
# End of backpack functions


def game_instructions():
    """Show Instructions How To Play"""
    ...


def locations_from_file(loc_fname):
    """Load Locations from CSV file and iterate through to create class objects"""
    try:
        locations = pd.read_csv(loc_fname)
    except FileNotFoundError:
        raise Exception("Cannot open locations file within data folder.")
    try:
        loclist = []  # set up an empty object list
        for i, r in locations.iterrows():
            loclist.append(Location(r))  # create a NEW location, append to list
    except FileNotFoundError:
        raise Exception("Cannot create LOCATION list.")
    return loclist


def objects_from_file(obj_fname):
    """Load Objects from CSV file and iterate through to create class objects"""
    try:
        objects = pd.read_csv(obj_fname)
    except FileNotFoundError:
        raise Exception("Cannot open objects file within data folder.")
    try:
        objlist = []
        for i, o in objects.iterrows():
            objlist.append(Object(o))  # create a NEW object, append to list
    except FileNotFoundError:
        raise Exception("Cannot create OBJECT list.")
    return objlist


def npcs_from_file(npc_fname):
    """Load NPCs from CSV file and iterate through to create class objects"""
    try:
        npcs = pd.read_csv(npc_fname)
    except FileNotFoundError:
        raise Exception("Cannot open npcs file within data folder.")
    try:
        npclist = []
        for i, n in npcs.iterrows():
            npclist.append(NPC(n))  # create a NEW npc, append to list
    except:
        raise Exception("ERROR: Cannot create NPC list.")
    return npclist


def genlocs_from_file(gen_fname):
    """Load GenLocs from CSV file and iterate through to create class objects"""
    try:
        genlocs = pd.read_csv(gen_fname)
    except FileNotFoundError:
        raise Exception("Cannot open genlocs file within data folder.")
    try:
        genloclist = []
        for i, gl in genlocs.iterrows():
            genloclist.append(Genloc(gl))
    except:
        raise Exception("Cannot create GENLOC list.")
    return genloclist


def location_logic(loc):
    for i in range(2):
        print(" ")
    print(loc.Story)
    return True


def object_logic(loc):
    ...


def npc_logic(loc):
    ...


def blank_lines(x):
    for i in range(x):
        print(" ")


def user_logic(loc):
    # Get user input
    global current_loc
    global TEST_MODE
    blank_lines(2)
    i = input("What now? ")
    if i:   # check to ensure NOT empty!
        r = i.upper()[0]  # take 1st char and UPPER it
        if r == "Q":    # quit
            if input("Are you sure? Y/N").upper()[0] == "Y":
                blank_lines(2)
                print("... GAME OVER ...")
                return True
            else:
                return False
        elif r == 'N':  # go north
            # if the current location obj N is not null
            if TEST_MODE: print(loc.N)
            if loc.N != 0:
                current_loc = loc.N
                return False
            else:
                print("You cannot go North. Try again.")
        elif r == 'S':  # go south
            if TEST_MODE: print(loc.S)
            if loc.S != 0:
                current_loc = loc.S
                return False
            else:
                print("You cannot go south. Try again.")
            ...
        elif r == 'E':  # go east
            if TEST_MODE: print(loc.E)
            if loc.E != 0:
                current_loc = loc.E
                return False
            else:
                print("You cannot go East. Try again.")
            ...
        elif r == 'W':  # go west
            if TEST_MODE: print(loc.W)
            if loc.W != 0:
                current_loc = loc.W
                return False
            else:
                print("You cannot go West. Try again.")
            ...
        elif r == 'I':  # list inventory
            blank_lines(2)
            ...
        elif r == 'U':  # pickup item
            blank_lines(2)
            ...
        elif r == 'D':  # drop item
            blank_lines(2)
            ...
        elif r == 'L':  # look around
            blank_lines(2)
            print(loc.Desc)
            return False
        elif r == 'H':  # help!
            blank_lines(2)
            print("Your commands are as follows: Move using 'N','S','E','W'. Look around with 'L'. Exit the game with 'Q'. "
                  "Pickup items with 'U', drop them with 'D' and list your backapack contents with 'I'.")
            return False
        else:
            return False
        return False
    else:
        return False


def run_game():
    """Run the game if run as standalone program"""

    loc_fname = 'data/locations.csv'
    obj_fname = 'data/objects.csv'
    npc_fname = 'data/npcs.csv'
    gen_fname = 'data/genlocs.csv'

    backpack = [0, 0, 0, 0, 0]  # Create a backpack with 5 spaces to hold OBJ IDs
    genlocs = genlocs_from_file(gen_fname)  # Load genloc text and create list of 'random' text
    npcs = npcs_from_file(npc_fname)  # Load npc's and create list
    things = objects_from_file(obj_fname)  # Load objects and create list
    locations = locations_from_file(loc_fname)  # Load locations and create list

    game_instructions()     # Display game rules

    game_over = False


    if TEST_MODE:
        # DUMMY TEST STUFF
        # print(things[current_loc].Desc)
        # print(npcs[current_loc].Desc)
        # print(genlocs[current_loc].Desc)
        # print(locations[current_loc].Desc)  # how to access the locations's value(s) by field
        # print('backpack has ' + str(len(backpack)) + ' spaces')
        # print(locations[current_loc].ID,locations[current_loc].Desc)
        if pandas.isna(locations[current_loc].N):
            print("Empty value")
        else:
            print("Some value")

    while not game_over:    # Main Game Loop
        location_logic(locations[current_loc])
        object_logic(locations[current_loc])
        npc_logic(locations[current_loc])
        game_over = user_logic(locations[current_loc])
        print(" ")


if __name__ == "__main__":
    """Call runGame() to get this party started!"""
    run_game()
