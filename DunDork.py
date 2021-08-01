""" This is the MAIN file for Dungeons of Dork (Python Edition.)
    Copyright 2021 (c) JamesBurchil.com
    """

import pandas as pd

GAMEOVER = False
TESTMODE = True  # used to print out stuff during dev/testing ...

class Location:
    """Locations in the DOD game"""
    def __init__(self, loc):
        self.ID = loc["LOC_ID"]
        self.N = loc["LOC_N"]
        self.S = loc["LOC_S"]
        self.W = loc["LOC_W"]
        self.E = loc["LOC_E"]
        self.IsDark = loc["LOC_IS_DARK"]
        self.Story = loc["LOC_STORY"]
        self.Desc = loc["LOC_DESC"]
        self.ObjectID = loc["LOC_OBJ_ID"]
        self.NpcID = loc["LOC_NPC_ID"]

    def GetLocation(self,id):
        pass

    def GenerateLocationInfo(self,id):
        pass

    def ListDirectionChoices(self,id):
        pass

    def LookAround(self,id):
        pass

    def ListObjectsInLocation(self,id):
        pass

class Object:
    """Objects in the DOD game"""
    def __init__(self,obj):
        self.ID = obj["OBJ_ID"]
        self.Desc = obj["OBJ_DESC"]
        self.Name = obj["OBJ_NAME"]
        self.Story = obj["OBJ_NARRATIVE"]     #Narrative when collected
        self.RequiredToWin = obj["OBJ_WIN"]
        self.inBackPack = False

class NPC:
    """Non Player Characters"""
    def __init__(self,n):
        self.ID = n["NPC_ID"]
        self.Name = n["NPC_NAME"]
        self.Desc = n["NPC_DESC"]
        self.ObjectID = n["NPC_OBJID"] #Kryptonite to this NPC
        self.CanMove = n["NPC_CAN_MOVE"]
        self.StartLocationID = n["NPC_START_LOC_ID"]
        self.CurrentLocationID = n["NPC_CURRENT_LOC_ID"]

class Genloc:
    """Arbitrary text for the game locations"""
    def __init__(self,gl):
        self.ID = gl["GEN_LOC_ID"]
        self.Story = gl["GEN_STORY"]
        self.Desc = gl["GEN_DESC"]

class Backpack:
    """The player's backpack, admittedly there's ONLY ONE per game"""
    def __init__(self,s=5):
        self.space = []
        for i in range(s):
            self.space.append('')

    def CheckInventory(self):
        pass

    def PickupObject(self,o):
        pass

    def DropObject(self,o):
        pass

def showInstructions():
    """Show Instructions How To Play"""
    pass

def loadLocations(LocFname):
    """Load Locations from CSV file and iterate through to create class objects"""
    try:
        locations = pd.read_csv(LocFname)
    except:
        raise Exception("Cannot open locations file within data folder.")
    try:
        loclist = []     # set up an empty object list
        for i, r in locations.iterrows():
            loclist.append(Location(r))  #create a NEW location, append to list
    except:
        raise Exception("Cannot create LOCATION list.")
    return loclist

def loadObjects(ObjFname):
    """Load Objects from CSV file and iterate through to create class objects"""
    try:
        objects = pd.read_csv(ObjFname)
    except:
        raise Exception("Cannot open objects file within data folder.")
    try:
        objlist = []
        for i, o in objects.iterrows():
            objlist.append(Object(o))   #create a NEW object, append to list
    except:
        raise Exception("Cannot create OBJECT list.")
    return objlist

def loadNPCs(NpcFname):
    """Load NPCs from CSV file and iterate through to create class objects"""
    try:
        npcs = pd.read_csv(NpcFname)
    except:
        raise Exception("Cannot open npcs file within data folder.")
    try:
        npclist = []
        for i, n in npcs.iterrows():
            npclist.append(NPC(n))      #create a NEW npc, append to list
    except:
        raise Exception("ERROR: Cannot create NPC list.")
    return npclist

def loadGenlocs(GenFname):
    """Load GenLocs from CSV file and iterate through to create class objects"""
    try:
        genlocs = pd.read_csv(GenFname)
    except:
        raise Exception("Cannot open genlocs file within data folder.")
    try:
        genloclist = []
        for i, gl in genlocs.iterrows():
            genloclist.append(Genloc(gl))
    except:
        raise Exception("Cannot create GENLOC list.")
    return genloclist

def move():
    """Move the player"""
    pass

def main_loop():
    while not GAMEOVER:
        #Get user input
        response = input("What now?")
        if response == 'Q':
            break
        elif response == 'q':
            break
        elif response =='quit':
            break
        elif response == 'Quit':
            break
        elif response == 'QUIT':
            break
        pass

def runGame():
    """Run the game if run as standalone program"""

    LocFname = 'data/locations.csv'
    ObjFname = 'data/objects.csv'
    NpcFname = 'data/npcs.csv'
    GenFname = 'data/genlocs.csv'

    location = loadLocations(LocFname)      #Load locations and create list
    object = loadObjects(ObjFname)          #Load objects and create list
    npc = loadNPCs(NpcFname)                #Load npc's and create list
    genloc = loadGenlocs(GenFname)          #Load genloc text and create list
    backpack = Backpack()                   #Create a backpack with 5 spaces (unless specified)

    showInstructions()                      #Display game rules

    if TESTMODE:
        #DUMMY TEST STUFF
        print(object[0].Desc)
        print(npc[0].Desc)
        print(genloc[0].Desc)
        print(location[0].Desc)  #how to access the location's value(s) by field
        print('backpack has ' + str(len(backpack.space)) + ' spaces')

    main_loop() #loop until GAME_OVER is True

# --------------------------------------------------------------------
# Call runGame() to get this party started!
# --------------------------------------------------------------------
if __name__ == "__main__":
    runGame()
