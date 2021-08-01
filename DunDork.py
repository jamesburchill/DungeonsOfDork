""" This is the MAIN file for Dungeons of Dork (Python Edition.)
    Copyright 2021 (c) JamesBurchil.com
    """

# Import required modules
from typing import List

import pandas as pd

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
    def __init__(self):
        self.ID = 0
        self.Name = ''
        self.Desc = ''
        self.ObjectID = 0 #Kryptonite to this NPC
        self.CanMove = False
        self.StartLocationID = 0
        self.CurrentLocationID = 0

class Backpack:
    """The player's backpack, admittedly there's ONLY ONE per game"""
    def __init__(self):
        self.storageSpace = [0, 0, 0, 0, 0]

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
        loclist: list[Location] = []     # set up an empty object list
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
        # set up object list
        for o in objects:
            pass
    except:
        raise Exception("Cannot create OBJECT list.")

def loadNPCs(NpcFname):
    """Load NPCs from CSV file and iterate through to create class objects"""
    try:
        npcs = pd.read_csv(NpcFname)
    except:
        raise Exception("Cannot open npcs file within data folder.")
    try:
        for x in npcs:
            pass
    except:
        raise Exception("ERROR: Cannot create NPC list.")

def loadGenlocs(GenFname):
    """Load GenLocs from CSV file and iterate through to create class objects"""
    try:
        genlocs = pd.read_csv(GenFname)
    except:
        raise Exception("Cannot open genlocs file within data folder.")
    try:
        for gl in genlocs:
            pass
    except:
        raise Exception("ERROR: Cannot create GENLOC list.")

def move():
    """Move the player"""
    pass

def runGame():
    """Run the game if run as standalone program"""

    LocFname = 'data/location.csv'
    ObjFname = 'data/objects.csv'
    NpcFname = 'data/npcs.csv'
    GenFname = 'data/genlocs.csv'

    location = loadLocations(LocFname)
    print(location[0].ID)  #how to access the location's value(s) by field

    object = loadObjects(ObjFname)
    print(object[0].ID)

    npc = loadNPCs(NpcFname)
    print(npc[0].ID)

    genloc = loadGenlocs(GenFname)
    print(genloc[0].ID)

    backpack = Backpack()
    print(backpack.storageSpace)

    showInstructions()


# --------------------------------------------------------------------
# Call runGame() to get this party started!
# --------------------------------------------------------------------
if __name__ == "__main__":
    runGame()
