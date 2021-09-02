""" This is the MAIN file for Dungeons of Dork (Python Edition.)
    Copyright 2021 (c) JamesBurchill.com
"""
import random
from pandas import read_csv, isna


class Player:
    """ The main protagonist in our game"""

    def __init__(self, loc_list, obj_list, npc_list):
        self.backpack = [0, 0, 0, 0, 0]  # 5 storage spaces in the backpack
        self.current_loc = 1  # set to 1 to account for zero-offset indexing
        self.health = 100  # number of health points to lose before player dies!
        self.game_over = False  # play game until True
        self.locs = loc_list  # all the locations in the game
        self.objs = obj_list  # all the objects in the game
        self.npcs = npc_list  # all the npcs in the game
        self.new_location = True
        self.instructions = "---------------------------------------------------------------------------------- \n" \
            "The object of the game is simple ... escape the 'Dungeons of Dork!'\n" \
            "You may encounter monsters along your journey and you may find objects too.\n" \
            "In each situation you will need to decide what to do. Here are your controls:\n" \
            "Move using 'N','S','E','W'. 'M' lists available moves. Look around with 'L'. \n" \
            "Exit the game with 'Q'. Pickup items with 'U', drop them with 'D' \n" \
            "and finally, itemize your backpack with 'I'. Good luck! \n" \
            "----------------------------------------------------------------------------------"
        self.valid_command = True
        self.told_story = False
        self.debug_mode = True  # change to False when ready :)

        self.show_instructions()  # show game instructions at start

    def play_game(self):  # main game loop
        if self.new_location:
            if self.current_loc == 90:  # winning location ID in map.
                self.found_exit()
            else:
                self.report_location_status()
        else:
            self.valid_command = self.get_user_input()
        return self.game_over

    def report_location_status(self):
        self.look_around()
        self.list_directions()
        self.list_objects()
        self.list_npcs()

    def found_exit(self):
        """A simple 'You Won' message and an exit from the game loop"""
        self.game_over = True
        print("Congratulations, you have escaped the Dungeons of Dork!")
        return self.game_over

    def move(self, direction):
        self.told_story = False     # Reset told_story for THIS location
        self.new_location = True
        if direction == 'N':  # go north
            # if the current location obj N is not null
            if locs[self.current_loc - 1].N != 0:
                self.current_loc = locs[self.current_loc - 1].N
                self.report_location_status()
                return True
            else:
                print("You cannot go North. Try again.")
                return False
        elif direction == 'S':  # go south
            if locs[self.current_loc - 1].S != 0:
                self.current_loc = locs[self.current_loc - 1].S
                self.report_location_status()
                return True
            else:
                print("You cannot go south. Try again.")
                return False
        elif direction == 'E':  # go east
            if locs[self.current_loc - 1].E != 0:
                self.current_loc = locs[self.current_loc - 1].E
                self.report_location_status()
                return True
            else:
                print("You cannot go East. Try again.")
                return False
        elif direction == 'W':  # go west
            if locs[self.current_loc - 1].W != 0:
                self.current_loc = locs[self.current_loc - 1].W
                self.report_location_status()
                return True
            else:
                print("You cannot go West. Try again.")
                return False

    def look_around(self):
        self.new_location = False
        if self.told_story:
            print(self.locs[self.current_loc - 1].Desc)
            self.told_story = True
            return self.told_story
        else:
            print(self.locs[self.current_loc - 1].Story)
            self.told_story = True
            return self.told_story

    def list_directions(self):
        directions = []
        if self.locs[self.current_loc - 1].N != 0:
            directions.append("N")
        if self.locs[self.current_loc - 1].S != 0:
            directions.append("S")
        if self.locs[self.current_loc - 1].E != 0:
            directions.append("E")
        if self.locs[self.current_loc - 1].W != 0:
            directions.append("W")
        print("You may go", directions)
        return True

    def drop_object(self):
        valid_choices = "0123456789"
        for i, o in enumerate(self.backpack):
            if not isinstance(o, int):
                print("[", i, "] ", o.Name)
        drop = input("Which object do you wish to drop? Type its number > ")
        if (drop in valid_choices) and (int(drop) <= len(self.backpack)):
            if isinstance(self.backpack[int(drop)], int):        # check that they're picking an actual object!
                print("Please choose a valid object number. Try again.")
                return False
            else:
                prompt = "You have chosen to drop the " + self.backpack[int(drop)].Name + ". Are you sure? Y/N > "
                if input(prompt).upper()[0] == "Y":
                    print("You take the " + self.backpack[int(drop)].Name + " and drop it.")
                    self.locs[self.current_loc - 1].ObjectID = self.backpack[int(drop)].ID   # drop objid into loc objid
                    self.backpack[int(drop)] = 0     # empty backpack space (remove obj reference)
                    return True
                else:
                    # do NOT drop, just exit
                    return False
        print("Please choose a valid object number. Try again.")
        return False

    def pickup_object(self):  # tbc
        if self.locs[self.current_loc - 1].ObjectID > 0:    # There's an OBJ at this location
            # Now figure out if there's space in the backpack
            space, x = self.backpack_has_space()
            if space:  # x == location in backpack
                # Get ObjectID from adjusted current locaction
                oid = self.locs[self.current_loc - 1].ObjectID
                # Adjust oid for index offset
                oid = oid - 1
                self.backpack[x] = self.objs[oid]
                print("You pickup the", self.objs[oid].Name, "and stow it in your backpack.")
                self.locs[self.current_loc - 1].ObjectID = 0  # erase object from current location
                return True
        else:
            return False

    def backpack_has_space(self):  # tbc
        """Ensure there's space in the backpack"""
        for i, space in enumerate(self.backpack):
            if isinstance(space, int):  # then there's no object there
                return True, i  # index of free space
        return False, -1  # 0 means NO free spaces!

    def look_in_backpack(self):
        """List what's in the backpack"""
        collected = []
        for item in self.backpack:
            if not isinstance(item, int):
                collected.append(item.Desc)
        if len(collected) > 0:
            print("You have ", collected, " in your backpack.")
            return True
        else:
            return False

    def get_user_input(self):
        # Get user input
        i = input("What now? > ")
        if i:  # check to ensure NOT empty!
            r = i.upper()[0]  # upper 1st char
            if r == "Q":
                if input("Are you sure? > ").upper()[0] == "Y":
                    return self.quit_game()
            elif r == 'I':  # list inventory
                return self.look_in_backpack()
            elif r == 'U':  # pickup item
                return self.pickup_object()
            elif r == 'D':  # drop item
                return self.drop_object()
            elif r == 'L':  # look around
                return self.report_location_status()
            elif r == 'H':  # help!
                return self.show_instructions()
            elif r == "N" or r == "S" or r == "E" or r == "W":
                return self.move(r)
            elif r == 'M':  # Direction choices
                return self.list_directions()
            else:
                print("Sorry I don't understand that instruction. Try again. Press 'H' for help.")
                return False
        else:
            return False

    def quit_game(self):
        self.game_over = True
        return True

    def show_instructions(self):
        """Show Instructions How To Play"""
        print(self.instructions)
        return True

    def list_objects(self):
        if self.locs[self.current_loc - 1].ObjectID > 0:
            # Get ObjectID from adjusted current locaction
            oid = self.locs[self.current_loc - 1].ObjectID
            # Adjust oid for index offset
            oid = oid - 1
            print("There is ", self.objs[oid].Desc, " here.")

    def list_npcs(self):
        if self.locs[self.current_loc - 1].NpcID > 0:
            print("There is ", self.npcs[self.locs[self.current_loc - 1].NpcID].Desc, " here.")
        '''I have not yet programmed the NPC logic. Monster NPCs will either do something bad (if you don't have 
        their equivalent kryptonite object in your backpack, or if you do, they will run away or some such thing.
        If you don't have their nullifying object in your posession, you might lose another object, get transported
        to some random location in the game and so on. It's currently up to you! Have fun.'''


class Location:
    """Locations in the DOD game"""

    def __init__(self, loc, gen_text):
        rint = random.randint(0, len(gen_text) - 1)
        if isna(loc["LOC_ID"]):
            self.ID = 0
        else:
            self.ID = int(loc["LOC_ID"])
        if isna(loc["LOC_N"]):
            self.N = 0
        else:
            self.N = int(loc["LOC_N"])
        if isna(loc["LOC_S"]):
            self.S = 0
        else:
            self.S = int(loc["LOC_S"])
        if isna(loc["LOC_W"]):
            self.W = 0
        else:
            self.W = int(loc["LOC_W"])
        if isna(loc["LOC_E"]):
            self.E = 0
        else:
            self.E = int(loc["LOC_E"])
        if isna(loc["LOC_IS_DARK"]):
            self.IsDark = 0
        else:
            self.IsDark = loc["LOC_IS-DARK"]
        if isna(loc["LOC_STORY"]):
            self.Story = gen_text[rint].Story
        else:
            self.Story = loc["LOC_STORY"]
        if isna(loc["LOC_DESC"]):
            self.Desc = gen_text[rint].Desc
        else:
            self.Desc = loc["LOC_DESC"]
        if isna(loc["LOC_OBJ_ID"]):
            self.ObjectID = 0
        else:
            self.ObjectID = int(loc["LOC_OBJ_ID"])
        if isna(loc["LOC_NPC_ID"]):
            self.NpcID = 0
        else:
            self.NpcID = int(loc["LOC_NPC_ID"])


class Object:
    """Objects in the DOD game"""

    def __init__(self, obj):
        self.ID = obj["OBJ_ID"]
        self.Desc = obj["OBJ_DESC"]
        self.Name = obj["OBJ_NAME"]
        self.Story = obj["OBJ_NARRATIVE"]  # Narrative when collected
        self.RequiredToWin = obj["OBJ_WIN"]


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


def locations_from_file(fname, g):
    """Load Locations from CSV file and iterate through to create class objects"""
    try:
        locations = read_csv(fname)
    except FileNotFoundError:
        raise Exception("Cannot open locations file within data folder.")
    try:
        loclist = []  # set up an empty object list
        for i, r in locations.iterrows():
            loclist.append(Location(r, g))  # create a NEW location, append to list
    except FileNotFoundError:
        raise Exception("Cannot create LOCATION list.")
    return loclist


def objects_from_file(fname):
    """Load Objects from CSV file and iterate through to create class objects"""
    try:
        objects = read_csv(fname)
    except FileNotFoundError:
        raise Exception("Cannot open objects file within data folder.")
    try:
        objlist = []
        for i, o in objects.iterrows():
            objlist.append(Object(o))  # create a NEW object, append to list
    except FileNotFoundError:
        raise Exception("Cannot create OBJECT list.")
    return objlist


def npcs_from_file(fname):
    """Load NPCs from CSV file and iterate through to create class objects"""
    try:
        _npcs = read_csv(fname)
    except FileNotFoundError:
        raise Exception("Cannot open _npcs file within data folder.")
    try:
        npclist = []
        for i, n in _npcs.iterrows():
            npclist.append(NPC(n))  # create a NEW npc, append to list
    except ValueError:
        raise Exception("ERROR: Cannot create NPC list.")
    return npclist


def genlocs_from_file(file):
    """Load GenLocs from CSV file and iterate through to create class objects"""
    try:
        genlocs = read_csv(file)
    except FileNotFoundError:
        raise Exception("Cannot open gens file within data folder.")
    try:
        genloclist = []
        for i, gl in genlocs.iterrows():
            genloclist.append(Genloc(gl))
    except ValueError:
        raise Exception("Cannot create GENLOC list.")
    return genloclist


if __name__ == "__main__":
    """Run the game if run as standalone program"""

    npc_fname = 'src/data/npcs.csv'
    gen_fname = 'src/data/genlocs.csv'
    obj_fname = 'src/data/objects.csv'
    loc_fname = 'src/data/locations.csv'

    gens = genlocs_from_file(gen_fname)  # Load genloc text and create list of 'random' text
    npcs = npcs_from_file(npc_fname)  # Load npc's and create list
    objs = objects_from_file(obj_fname)  # Load objects and create list
    locs = locations_from_file(loc_fname, gens)  # Load locations and create list, fill blanks with genlocs

    player = Player(locs, objs, npcs)  # instantiate a new player, pass in ALL game lists

    while not player.game_over:
        player.play_game()

# THE END ¯\_(ツ)_/¯
