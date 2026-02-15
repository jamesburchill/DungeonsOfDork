"""This is the MAIN file for Dungeons of Dork (Python Edition.)
Copyright 2021 (c) JamesBurchill.com
"""

import csv
import json
import random
import time
from collections import deque
from pathlib import Path


DIRECTION_ALIASES = {
    "N": "N",
    "NORTH": "N",
    "S": "S",
    "SOUTH": "S",
    "E": "E",
    "EAST": "E",
    "W": "W",
    "WEST": "W",
}

COLORS = {
    "reset": "\033[0m",
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "cyan": "\033[96m",
}


def isna(value):
    if value is None:
        return True
    return str(value).strip() == ""


def to_int(value, default=0):
    if isna(value):
        return default
    return int(value)


def normalize(text):
    return " ".join(text.strip().lower().split())


def rows_from_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def load_meta(meta_path):
    default = {
        "wins": 0,
        "total_xp": 0,
        "unlocked_classes": ["adventurer"],
        "last_class": "adventurer",
        "best_ending": "",
    }
    if not meta_path.exists():
        return default
    try:
        with open(meta_path, "r", encoding="utf-8") as handle:
            saved = json.load(handle)
            default.update(saved)
    except (OSError, json.JSONDecodeError):
        pass
    return default


def save_meta(meta_path, data):
    try:
        with open(meta_path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
    except OSError:
        pass


class Player:
    """Main protagonist in the game."""

    def __init__(
        self,
        loc_list,
        obj_list,
        npc_list,
        meta=None,
        meta_path=None,
        mutator=None,
        player_class=None,
        input_func=input,
        output_func=print,
        show_ascii_minimap=True,
        interface_mode="cli",
    ):
        self.locs = loc_list
        self.loc_by_id = {l.ID: l for l in loc_list}
        self.objs = obj_list
        self.obj_by_id = {o.ID: o for o in obj_list}
        self.npcs = npc_list
        self.npc_by_id = {n.ID: n for n in npc_list}

        self.meta = meta or {
            "wins": 0,
            "total_xp": 0,
            "unlocked_classes": ["adventurer"],
            "last_class": "adventurer",
            "best_ending": "",
        }
        self.meta_path = meta_path
        self.input_func = input_func
        self.output_func = output_func
        self.show_ascii_minimap = show_ascii_minimap
        self.interface_mode = interface_mode

        self.player_class = player_class or self.meta.get("last_class", "adventurer")
        if self.player_class not in self.meta.get("unlocked_classes", ["adventurer"]):
            self.player_class = "adventurer"

        self.backpack = [None, None, None, None, None]
        self.current_loc = 1
        self.previous_loc = 1
        self.health = 100
        self.max_health = 100
        self.game_over = False
        self.new_location = True
        self.valid_command = True
        self.told_story = False

        self.xp = 0
        self.perks = {
            "trap_detection": False,
            "extra_slot": False,
            "extra_move_on_map": False,
        }
        self.map_boost_active = False
        self.required_artifacts = {2, 3, 4}

        self.lore_seen = set()
        self.lore_snippets = [
            "A scratched inscription reads: 'Only wit outlives steel.'",
            "You find initials carved in stone: 'E.B. made it this far.'",
            "A brittle note says: 'The east gate answers to relics.'",
            "A mural depicts three relics held aloft before a sunlit door.",
            "A faded warning says: 'Never trust the quiet room.'",
        ]

        self.pending_encounter = None
        self.defeated_npcs = set()
        self.turn_count = 0
        self.combat_log = []

        self.reputation = {"scholars": 0, "outcasts": 0}

        self.revealed_rooms = {self.current_loc}
        self.secret_room = 33
        self.secret_keyword = "dork"
        self.secret_shortcut_target = 89

        self.hunter_id = 998
        self.hunter_awake = False
        self.timed_block = {"loc": None, "dir": None, "ttl": 0}

        self.style = {
            "color": True,
            "typewriter": False,
            "delay": 0.008,
        }

        self.mutator = mutator or {
            "name": "None",
            "desc": "Standard dungeon conditions.",
            "enemy_damage_bonus": 0,
            "fog": False,
            "extra_traps": False,
            "rich_loot": False,
        }

        self.quests = [
            {
                "id": "q_torch",
                "title": "Light the Scriptorium",
                "giver": "Old Cartographer",
                "faction": "scholars",
                "room": 39,
                "required_item": 1,
                "reward_item": 100,
                "reward_xp": 20,
                "accepted": False,
                "completed": False,
                "description": "Bring a Torch to the Old Cartographer.",
            },
            {
                "id": "q_amulet",
                "title": "Proof of Courage",
                "giver": "Trapped Scholar",
                "faction": "scholars",
                "room": 61,
                "required_item": 2,
                "reward_item": 101,
                "reward_xp": 20,
                "accepted": False,
                "completed": False,
                "description": "Show the Amulet to the Trapped Scholar.",
            },
            {
                "id": "q_book",
                "title": "Last Lesson",
                "giver": "Lost Knight",
                "faction": "outcasts",
                "room": 75,
                "required_item": 4,
                "reward_item": 102,
                "reward_xp": 25,
                "accepted": False,
                "completed": False,
                "description": "Bring the Book of Spells to the Lost Knight.",
            },
        ]

        self.instructions = (
            "----------------------------------------------------------------------------------\n"
            "Escape the Dungeons, but first collect 3 relics: Amulet, Dagger, Book of Spells.\n"
            "Move: N/S/E/W or north/south/east/west.\n"
            "Core: look, pickup <item>, drop <item>, inventory, map, quests, status, quit.\n"
            "Combat: attack, flee, use <item>, powerstrike (fighter), analyze (scholar), scan (scout).\n"
            "World: rune <word>, style color, style type, log\n"
            "----------------------------------------------------------------------------------"
        )

        self._normalize_entities()
        self._apply_class_modifiers()
        self._apply_mutator_modifiers()

        if self.interface_mode == "cli":
            self.say(self.instructions)
        self.say(f"Class: {self.player_class} | Mutator: {self.mutator['name']} - {self.mutator['desc']}")

    def _normalize_entities(self):
        for loc in self.locs:
            if not hasattr(loc, "Tag"):
                loc.Tag = "safe"
            if not hasattr(loc, "EventResolved"):
                loc.EventResolved = False
            if not hasattr(loc, "SecretSolved"):
                loc.SecretSolved = False
        for obj in self.objs:
            if not hasattr(obj, "Story"):
                obj.Story = ""
        for npc in self.npcs:
            if not hasattr(npc, "Hostile"):
                npc.Hostile = True
            if not hasattr(npc, "Patrol"):
                npc.Patrol = []
            if not hasattr(npc, "IsBoss"):
                npc.IsBoss = False
            if not hasattr(npc, "HP"):
                npc.HP = 40
            if not hasattr(npc, "MaxHP"):
                npc.MaxHP = npc.HP
            if not hasattr(npc, "Phase"):
                npc.Phase = 1
            if not hasattr(npc, "Telegraph"):
                npc.Telegraph = None

    def _apply_class_modifiers(self):
        if self.player_class == "fighter":
            self.max_health += 15
            self.health = self.max_health
        elif self.player_class == "scout":
            self.perks["trap_detection"] = True
        elif self.player_class == "scholar":
            self.add_xp(10, "scholar training")

    def _apply_mutator_modifiers(self):
        if self.mutator["name"] == "Ironman":
            self.max_health = max(60, self.max_health - 20)
            self.health = min(self.health, self.max_health)

    def colorize(self, text, color):
        if not self.style["color"]:
            return text
        return f"{COLORS.get(color, '')}{text}{COLORS['reset']}"

    def prompt(self, text):
        return self.input_func(text)

    def say(self, text, color=None, log=False):
        msg = self.colorize(str(text), color) if color else str(text)
        if self.style["typewriter"] and self.output_func is print:
            for ch in msg:
                print(ch, end="", flush=True)
                time.sleep(self.style["delay"])
            print()
        else:
            self.output_func(msg)
        if log:
            self.combat_log.append(str(text))
            self.combat_log = self.combat_log[-25:]

    def play_game(self):
        if self.pending_encounter:
            self.handle_encounter_turn()
            return self.game_over

        if self.new_location:
            self.report_location_status()
            self.handle_room_event()
            self.handle_quests_in_room()
            self.check_for_encounter()
        else:
            self.valid_command = self.get_user_input()

        self.check_player_death()
        return self.game_over

    def check_player_death(self):
        if self.health > 0:
            return False
        if not self.game_over:
            self.game_over = True
            self.pending_encounter = None
            self.say("You collapse in the dungeon. Game over.", "red")
        return True

    def report_location_status(self):
        self.revealed_rooms.add(self.current_loc)
        self.look_around()
        if self.interface_mode == "ui":
            self.list_objects()
            self.list_npcs()
            return
        self.list_directions()
        if self.show_ascii_minimap:
            self.render_ascii_minimap()
        self.list_objects()
        self.list_npcs()

    def found_exit(self):
        self.game_over = True
        completed = sum(1 for q in self.quests if q["completed"])
        lore = len(self.lore_seen)
        defeated = len(self.defeated_npcs)

        if completed >= 3 and lore >= 3:
            ending = "Scholar's Escape"
            detail = "You leave with hard-won knowledge and every promise fulfilled."
        elif defeated >= 3:
            ending = "Warrior's Escape"
            detail = "You force your way out, scarred but unstoppable."
        else:
            ending = "Narrow Escape"
            detail = "You barely outrun the dungeon, but you made it."

        self.say("Congratulations, you escaped the Dungeons of Dork!", "green")
        self.say(f"Ending: {ending}")
        self.say(detail)
        self.say(f"Summary: XP {self.xp}, Quests {completed}/3, Lore {lore}, Defeated NPCs {defeated}")

        self.meta["wins"] = int(self.meta.get("wins", 0)) + 1
        self.meta["total_xp"] = int(self.meta.get("total_xp", 0)) + self.xp
        self.meta["best_ending"] = ending
        self.meta["last_class"] = self.player_class
        unlocks = set(self.meta.get("unlocked_classes", ["adventurer"]))
        if self.meta["wins"] >= 1:
            unlocks.add("fighter")
        if self.meta["wins"] >= 2:
            unlocks.add("scout")
        if self.meta["wins"] >= 3:
            unlocks.add("scholar")
        self.meta["unlocked_classes"] = sorted(unlocks)
        if self.meta_path:
            save_meta(self.meta_path, self.meta)
        return self.game_over

    def location(self, loc_id=None):
        if loc_id is None:
            loc_id = self.current_loc
        return self.loc_by_id[loc_id]

    def has_item(self, item_id):
        return any(slot == item_id for slot in self.backpack)

    def add_item(self, item_id):
        for idx, slot in enumerate(self.backpack):
            if slot is None:
                self.backpack[idx] = item_id
                return True
        return False

    def remove_item(self, item_id):
        for idx, slot in enumerate(self.backpack):
            if slot == item_id:
                self.backpack[idx] = None
                return True
        return False

    def get_available_directions(self, loc_id=None):
        loc = self.location(loc_id)
        dirs = []
        if loc.N:
            dirs.append("N")
        if loc.S:
            dirs.append("S")
        if loc.E:
            dirs.append("E")
        if loc.W:
            dirs.append("W")
        return dirs

    def get_blocked_direction(self):
        if self.timed_block["ttl"] > 0 and self.timed_block["loc"] == self.current_loc:
            return self.timed_block["dir"]

        active_npcs = self.active_hostile_npcs_here()
        if not active_npcs:
            return None
        dirs = self.get_available_directions()
        if not dirs:
            return None
        blocker = active_npcs[0]
        return dirs[(blocker.ID + self.current_loc) % len(dirs)]

    def move(self, direction, allow_bonus=True):
        direction = DIRECTION_ALIASES.get(direction, direction)
        blocked = self.get_blocked_direction()
        if blocked == direction:
            self.say(f"The way {direction} is blocked.", "yellow")
            return False

        loc = self.location()
        next_loc = 0
        if direction == "N":
            next_loc = loc.N
        elif direction == "S":
            next_loc = loc.S
        elif direction == "E":
            next_loc = loc.E
        elif direction == "W":
            next_loc = loc.W

        if not next_loc:
            self.say("You cannot go that way. Try again.", "yellow")
            return False

        if next_loc == 90 and not self.required_artifacts.issubset(self.backpack):
            missing_ids = [i for i in sorted(self.required_artifacts) if i not in self.backpack]
            missing_names = [self.obj_by_id[i].Name for i in missing_ids]
            self.say("The exit gate rejects you. Missing relics: " + ", ".join(missing_names), "yellow")
            return False

        self.previous_loc = self.current_loc
        self.current_loc = next_loc
        self.told_story = False
        self.new_location = True

        if self.current_loc == 90:
            self.found_exit()
            return True

        if allow_bonus and self.map_boost_active and self.perks["extra_move_on_map"]:
            self.map_boost_active = False
            bonus = self.prompt("Map insight grants a bonus move (N/S/E/W or skip) > ").strip().upper()
            if bonus and bonus[0] in {"N", "S", "E", "W"}:
                self.move(bonus[0], allow_bonus=False)

        return True

    def look_around(self):
        self.new_location = False
        loc = self.location()
        if self.told_story:
            self.say(loc.Desc)
        else:
            self.say(loc.Story)
            self.told_story = True
        return True

    def list_directions(self):
        directions = self.get_available_directions()
        blocked = self.get_blocked_direction()
        if blocked:
            self.say(f"You may go {directions} (but {blocked} is blocked)")
        else:
            self.say(f"You may go {directions}")
        return True

    def find_item_id_by_name(self, text):
        wanted = normalize(text)
        if not wanted:
            return None
        for item in self.objs:
            if normalize(item.Name) == wanted:
                return item.ID
        return None

    def drop_object(self, selection=None):
        carried = [slot for slot in self.backpack if slot is not None]
        if not carried:
            self.say("Your backpack is empty.")
            return False

        target_item_id = None
        if selection:
            if selection.isdigit():
                idx = int(selection)
                if 0 <= idx < len(self.backpack):
                    target_item_id = self.backpack[idx]
            else:
                target_item_id = self.find_item_id_by_name(selection)
                if target_item_id not in carried:
                    target_item_id = None
        else:
            for i, item_id in enumerate(self.backpack):
                if item_id is not None:
                    self.say(f"[{i}] {self.obj_by_id[item_id].Name}")
            drop = self.prompt("Which object do you wish to drop? Type number or name > ").strip()
            return self.drop_object(drop)

        if target_item_id is None:
            self.say("Please choose a valid object number or name.")
            return False

        if self.location().ObjectID:
            self.say("There is already something on the ground here.")
            return False

        confirm = self.prompt(f"Drop {self.obj_by_id[target_item_id].Name}? Y/N > ").strip().upper()
        if not (confirm and confirm[0] == "Y"):
            return False

        self.location().ObjectID = target_item_id
        self.remove_item(target_item_id)
        self.say(f"Dropped {self.obj_by_id[target_item_id].Name}")
        return True

    def pickup_object(self, wanted_name=""):
        oid = self.location().ObjectID
        if not oid:
            self.say("There is nothing to pick up here.")
            return False

        obj = self.obj_by_id.get(oid)
        if obj is None:
            self.say("That object data is invalid.")
            return False

        if wanted_name and normalize(obj.Name) != normalize(wanted_name):
            self.say(f"You do not see '{wanted_name}' here.")
            return False

        if not self.add_item(oid):
            self.say("Your backpack is full.")
            return False

        self.location().ObjectID = 0
        self.say(f"You pick up {obj.Name}", "green")
        if getattr(obj, "Story", ""):
            self.say(obj.Story)

        if oid == 103:
            self.say("The Cursed Idol chills your hands. Carry it too long and it will drain you.", "yellow")
        return True

    def look_in_backpack(self):
        items = [self.obj_by_id[item_id].Name for item_id in self.backpack if item_id is not None]
        if not items:
            self.say("Your backpack is empty.")
            return False
        self.say("Backpack: " + ", ".join(items))
        return True

    def show_status(self):
        completed = sum(1 for q in self.quests if q["completed"])
        self.say(
            f"Health: {self.health}/{self.max_health} | XP: {self.xp} | Quests: {completed}/3 | "
            f"Lore: {len(self.lore_seen)} | Rep S:{self.reputation['scholars']} O:{self.reputation['outcasts']}"
        )
        self.say("Perks: " + (", ".join(k for k, v in self.perks.items() if v) or "none"))
        return True

    def show_quests(self):
        for q in self.quests:
            state = "completed" if q["completed"] else "active" if q["accepted"] else "not started"
            self.say(f"- {q['title']} ({state}): {q['description']}")
        return True

    def show_log(self):
        if not self.combat_log:
            self.say("Combat log is empty.")
            return False
        self.say("Recent combat log:", "cyan")
        for line in self.combat_log[-8:]:
            self.say(f"- {line}")
        return True

    def quit_game(self):
        self.game_over = True
        self.meta["last_class"] = self.player_class
        if self.meta_path:
            save_meta(self.meta_path, self.meta)
        return True

    def show_instructions(self):
        if self.interface_mode == "ui":
            self.say("Commands: N/S/E/W, look, pickup <item>, drop <item>, map, quests, status, help, quit")
            self.say("Combat: attack, flee, use <item>, powerstrike (fighter), analyze (scholar), scan (scout)")
            self.say("World: rune <word>, style color, style type, log")
            return True
        self.say(self.instructions)
        self.say("Examples: 'go north', 'pickup torch', 'drop dagger', 'use amulet', 'rune dork', 'style color'", "cyan")
        return True

    def list_objects(self):
        oid = self.location().ObjectID
        if oid:
            self.say(f"There is {self.obj_by_id[oid].Desc} here.")

    def active_hostile_npcs_here(self):
        active = []
        for npc in self.npcs:
            if npc.Hostile and npc.CurrentLocationID == self.current_loc and npc.ID not in self.defeated_npcs:
                active.append(npc)
        return active

    def list_npcs(self):
        for npc in self.npcs:
            if npc.CurrentLocationID == self.current_loc and npc.ID not in self.defeated_npcs:
                mood = "hostile" if npc.Hostile else "friendly"
                label = "BOSS" if npc.IsBoss else mood
                self.say(f"There is {npc.Desc} here. ({label})")

    def add_xp(self, amount, reason):
        if amount <= 0:
            return
        self.xp += amount
        self.say(f"+{amount} XP ({reason})", "green")
        self.check_level_rewards()

    def check_level_rewards(self):
        if self.xp >= 20 and not self.perks["trap_detection"]:
            self.perks["trap_detection"] = True
            self.say("Perk unlocked: trap_detection", "green")

        if self.xp >= 40 and not self.perks["extra_slot"]:
            self.perks["extra_slot"] = True
            self.backpack.append(None)
            self.say("Perk unlocked: extra_slot (+1 backpack slot)", "green")

        if self.xp >= 60 and not self.perks["extra_move_on_map"]:
            self.perks["extra_move_on_map"] = True
            self.say("Perk unlocked: extra_move_on_map (after using map)", "green")

    def apply_end_of_turn_effects(self):
        if self.has_item(103):
            drain = 1 if self.perks.get("idol_dampened") else 2
            self.health -= drain
            self.say(f"The Cursed Idol drains {drain} health.", "yellow")

        if self.timed_block["ttl"] > 0:
            self.timed_block["ttl"] -= 1
            if self.timed_block["ttl"] == 0:
                self.say("A sealed corridor grinds open again.", "cyan")

    def spawn_timed_events(self):
        if self.turn_count > 0 and self.turn_count % 12 == 0:
            dirs = self.get_available_directions()
            if dirs:
                self.timed_block = {"loc": self.current_loc, "dir": random.choice(dirs), "ttl": 3}
                self.say(f"Stone plates slam shut. Direction {self.timed_block['dir']} is sealed briefly.", "yellow")

        if self.turn_count >= 15 and not self.hunter_awake and self.hunter_id in self.npc_by_id:
            self.hunter_awake = True
            self.npc_by_id[self.hunter_id].Hostile = True
            self.say("A distant horn echoes. The Hunter has entered the maze.", "red")

    def get_user_input(self):
        text = self.prompt("What now? > ").strip()
        if not text:
            return False

        verb, args = self.parse_command(text)
        acted = self.execute_command(verb, args)
        if acted and not self.game_over:
            self.turn_count += 1
            self.spawn_timed_events()
            self.move_npcs()
            self.apply_end_of_turn_effects()
        return acted

    def parse_command(self, text):
        words = text.strip().split()
        if not words:
            return "", []
        first = words[0].upper()

        if first in DIRECTION_ALIASES:
            return "MOVE", [DIRECTION_ALIASES[first]]

        cmd = normalize(words[0])
        rest = words[1:]

        if cmd in {"go", "move"} and rest:
            d = DIRECTION_ALIASES.get(rest[0].upper())
            if d:
                return "MOVE", [d]
        if cmd in {"look", "l"}:
            return "LOOK", []
        if cmd in {"i", "inventory", "backpack"}:
            return "INVENTORY", []
        if cmd in {"u", "pickup", "pick", "take", "grab"}:
            return "PICKUP", [" ".join(rest)]
        if cmd in {"d", "drop"}:
            return "DROP", [" ".join(rest)]
        if cmd in {"h", "help", "?"}:
            return "HELP", []
        if cmd in {"m", "moves"}:
            return "MOVES", []
        if cmd in {"q", "quit", "exit"}:
            return "QUIT", []
        if cmd in {"attack", "a"}:
            return "ATTACK", []
        if cmd in {"flee", "run"}:
            return "FLEE", []
        if cmd == "use":
            return "USE", [" ".join(rest)]
        if cmd == "quests":
            return "QUESTS", []
        if cmd == "status":
            return "STATUS", []
        if cmd == "map":
            return "MAP", []
        if cmd == "rune":
            return "RUNE", [" ".join(rest)]
        if cmd == "scan":
            return "SCAN", []
        if cmd == "analyze":
            return "ANALYZE", []
        if cmd == "powerstrike":
            return "POWERSTRIKE", []
        if cmd == "style":
            return "STYLE", [" ".join(rest)]
        if cmd == "log":
            return "LOG", []
        if cmd == "class":
            return "CLASS", []
        return "UNKNOWN", []

    def execute_command(self, verb, args):
        if verb == "MOVE":
            return self.move(args[0])
        if verb == "LOOK":
            self.report_location_status()
            return True
        if verb == "INVENTORY":
            return self.look_in_backpack()
        if verb == "PICKUP":
            return self.pickup_object(args[0] if args else "")
        if verb == "DROP":
            return self.drop_object(args[0] if args else "")
        if verb == "HELP":
            return self.show_instructions()
        if verb == "MOVES":
            return self.list_directions()
        if verb == "QUIT":
            confirm = self.prompt("Are you sure? Y/N > ").strip().upper()
            if confirm and confirm[0] == "Y":
                return self.quit_game()
            return False
        if verb == "ATTACK":
            if self.pending_encounter:
                return self.resolve_attack()
            self.say("There is nothing to attack right now.")
            return False
        if verb == "FLEE":
            if self.pending_encounter:
                return self.resolve_flee()
            self.say("You are not in combat.")
            return False
        if verb == "USE":
            item_name = args[0] if args else ""
            if not item_name:
                self.say("Use what?")
                return False
            if self.pending_encounter:
                return self.resolve_use_in_combat(item_name)
            return self.resolve_use_utility(item_name)
        if verb == "QUESTS":
            return self.show_quests()
        if verb == "STATUS":
            return self.show_status()
        if verb == "MAP":
            return self.use_map()
        if verb == "RUNE":
            return self.solve_rune(args[0] if args else "")
        if verb == "SCAN":
            return self.class_scan()
        if verb == "ANALYZE":
            return self.class_analyze()
        if verb == "POWERSTRIKE":
            return self.class_powerstrike()
        if verb == "STYLE":
            return self.toggle_style(args[0] if args else "")
        if verb == "LOG":
            return self.show_log()
        if verb == "CLASS":
            self.say(f"Current class: {self.player_class} | Unlocked: {', '.join(self.meta.get('unlocked_classes', []))}")
            return True

        self.say("Sorry, I do not understand that instruction. Press 'H' for help.")
        return False

    def toggle_style(self, arg):
        token = normalize(arg)
        if token in {"color", "colour"}:
            self.style["color"] = not self.style["color"]
            self.say(f"Color output: {'on' if self.style['color'] else 'off'}")
            return True
        if token in {"type", "typewriter"}:
            self.style["typewriter"] = not self.style["typewriter"]
            self.say(f"Typewriter: {'on' if self.style['typewriter'] else 'off'}")
            return True
        self.say("Usage: style color | style type")
        return False

    def check_for_encounter(self):
        self.apply_faction_tension()
        hostiles = self.active_hostile_npcs_here()
        if hostiles:
            self.pending_encounter = hostiles[0]
            if self.pending_encounter.IsBoss:
                self.say(f"{self.pending_encounter.Name} emerges from shadow. Final battle begins.", "red")
            else:
                self.say(f"{self.pending_encounter.Name} confronts you! (attack / flee / use <item>)", "red")

    def apply_faction_tension(self):
        """Faction reputation can cool or inflame specific enemies."""
        for npc in self.npcs:
            name = normalize(npc.Name)
            if "librarian" in name:
                npc.Hostile = self.reputation["scholars"] < 2
            elif "hunter" in name:
                npc.Hostile = self.hunter_awake

    def handle_encounter_turn(self):
        npc = self.pending_encounter
        if npc is None:
            return

        if npc.IsBoss and npc.Telegraph:
            dmg = npc.Telegraph["damage"] + self.mutator.get("enemy_damage_bonus", 0)
            self.health -= dmg
            self.say(f"Boss attack lands: {npc.Telegraph['name']} hits for {dmg}.", "red", log=True)
            npc.Telegraph = None
            if self.check_player_death():
                return

        if npc.IsBoss:
            self.say(f"Boss HP {npc.HP}/{npc.MaxHP} | Your HP {self.health}/{self.max_health}", "yellow")
        else:
            self.say(f"Combat with {npc.Name}. Health {self.health}/{self.max_health}", "yellow")

        command = self.prompt("Combat > ").strip()
        verb, args = self.parse_command(command)
        if verb == "ATTACK":
            self.resolve_attack()
        elif verb == "FLEE":
            self.resolve_flee()
        elif verb == "USE":
            self.resolve_use_in_combat(args[0] if args else "")
        elif verb == "POWERSTRIKE":
            self.class_powerstrike()
        elif verb == "ANALYZE":
            self.class_analyze()
        elif verb == "QUIT":
            confirm = self.prompt("Are you sure? Y/N > ").strip().upper()
            if confirm and confirm[0] == "Y":
                self.quit_game()
        else:
            self.say("Combat commands: attack, flee, use <item>, powerstrike, analyze")

        if self.check_player_death():
            return

        if self.pending_encounter and self.pending_encounter.IsBoss:
            self.set_boss_telegraph(self.pending_encounter)

    def set_boss_telegraph(self, npc):
        if npc.Phase == 1:
            npc.Telegraph = {"name": "Shadow Lance", "damage": 8}
        elif npc.Phase == 2:
            npc.Telegraph = {"name": "Rift Wave", "damage": 12}
        else:
            npc.Telegraph = {"name": "Cataclysmic Arc", "damage": 16}
        self.say(f"Telegraph: {npc.Name} begins charging {npc.Telegraph['name']}.", "yellow", log=True)

    def resolve_attack(self):
        npc = self.pending_encounter
        if npc is None:
            return False

        base_damage = 18 if self.player_class == "fighter" else 12
        if self.has_item(2) and self.has_item(102):
            base_damage += 4
            self.say("Synergy: Amulet + Lucky Charm empower your strike.", "cyan", log=True)

        if npc.IsBoss:
            npc.HP -= base_damage
            self.say(f"You strike {npc.Name} for {base_damage} damage.", "green", log=True)
            self.advance_boss_phase(npc)
            if npc.HP <= 0:
                return self.defeat_npc(npc)
            return True

        weakness = npc.ObjectID
        if weakness and self.has_item(weakness):
            boosted = base_damage + 16
            npc.HP -= boosted
            self.say(
                f"You exploit {npc.Name}'s weakness using {self.obj_by_id[weakness].Name} "
                f"for {boosted} damage.",
                "green",
                log=True,
            )
            if npc.HP <= 0:
                return self.defeat_npc(npc)
            return True

        npc.HP -= base_damage
        self.say(f"You hit {npc.Name} for {base_damage} damage.", "green", log=True)
        if npc.HP <= 0:
            return self.defeat_npc(npc)

        dmg = 8 + self.mutator.get("enemy_damage_bonus", 0)
        if self.perks.get("aura_shield"):
            dmg = max(0, dmg - 4)
            self.perks["aura_shield"] = False
            self.say("Your protective aura absorbs part of the retaliation.", "cyan", log=True)
        self.health -= dmg
        self.say(f"{npc.Name} retaliates. You lose {dmg} health.", "red", log=True)
        return True

    def advance_boss_phase(self, npc):
        threshold2 = int(npc.MaxHP * 0.66)
        threshold3 = int(npc.MaxHP * 0.33)
        if npc.Phase == 1 and npc.HP <= threshold2:
            npc.Phase = 2
            self.say(f"{npc.Name} enters phase 2. The room distorts.", "red", log=True)
        if npc.Phase == 2 and npc.HP <= threshold3:
            npc.Phase = 3
            self.say(f"{npc.Name} enters phase 3. The air crackles.", "red", log=True)

    def resolve_flee(self):
        npc = self.pending_encounter
        if npc is None:
            return False
        if npc.IsBoss:
            self.say("No escape. The boss seals the chamber.", "red")
            return False
        self.health -= 5
        self.current_loc = self.previous_loc
        self.new_location = True
        self.pending_encounter = None
        self.say(f"You flee from {npc.Name}. You lose 5 health.", "yellow", log=True)
        return True

    def resolve_use_in_combat(self, item_name):
        npc = self.pending_encounter
        if npc is None:
            return False

        parsed = normalize(item_name)
        if " with " in parsed:
            left, right = [p.strip() for p in parsed.split(" with ", 1)]
            return self.resolve_synergy_use(left, right, in_combat=True)

        item_id = self.find_item_id_by_name(item_name)
        if item_id is None or not self.has_item(item_id):
            self.say("You are not carrying that item.")
            return False

        if item_id == npc.ObjectID:
            self.say(f"{npc.Name} recoils from {self.obj_by_id[item_id].Name}.", "green", log=True)
            if npc.IsBoss:
                npc.HP -= 25
                self.advance_boss_phase(npc)
                if npc.HP <= 0:
                    return self.defeat_npc(npc)
                return True
            return self.defeat_npc(npc)

        if item_id == 104:
            self.health = min(self.max_health, self.health + 20)
            self.remove_item(104)
            self.say("You use a Healing Herb and recover 20 health.", "green", log=True)
            return True

        dmg = 10 + self.mutator.get("enemy_damage_bonus", 0)
        self.health -= dmg
        self.say(f"That item has no effect. The enemy hits you for {dmg} health.", "red", log=True)
        return True

    def resolve_synergy_use(self, left_name, right_name, in_combat=False):
        left_id = self.find_item_id_by_name(left_name)
        right_id = self.find_item_id_by_name(right_name)
        if left_id is None or right_id is None or not self.has_item(left_id) or not self.has_item(right_id):
            self.say("You need both items for that combo.")
            return False

        pair = {left_id, right_id}
        if pair == {1, 105}:  # Torch + Oil
            self.remove_item(105)
            self.say("Synergy: You coat the torch with oil. Next attack deals bonus damage.", "green")
            self.add_xp(5, "item synergy")
            self.perks["oil_torch_boost"] = True
            return True
        if pair == {2, 102}:  # Amulet + Lucky Charm
            self.say("Synergy: Protective aura surrounds you for this encounter.", "green")
            self.perks["aura_shield"] = True
            return True
        if pair == {101, 103}:  # Toolkit + Cursed Idol
            self.say("Synergy: Toolkit vents curse pressure. Idol drain reduced this run.", "green")
            self.perks["idol_dampened"] = True
            return True

        if in_combat:
            self.say("That combo fizzles in combat.")
        else:
            self.say("Nothing useful happens.")
        return False

    def defeat_npc(self, npc):
        npc.CurrentLocationID = -1
        self.defeated_npcs.add(npc.ID)
        self.pending_encounter = None
        self.add_xp(15 if not npc.IsBoss else 40, f"defeated {npc.Name}")
        self.say(f"{npc.Name} is defeated.", "green", log=True)
        if npc.IsBoss:
            self.reputation["outcasts"] += 1
        return True

    def resolve_use_utility(self, item_name):
        parsed = normalize(item_name)
        if " with " in parsed:
            left, right = [p.strip() for p in parsed.split(" with ", 1)]
            return self.resolve_synergy_use(left, right, in_combat=False)

        item_id = self.find_item_id_by_name(item_name)
        if item_id is None or not self.has_item(item_id):
            self.say("You are not carrying that item.")
            return False

        if item_id == 100:
            return self.use_map()
        if item_id == 104:
            self.health = min(self.max_health, self.health + 20)
            self.remove_item(104)
            self.say("You use a Healing Herb and recover 20 health.", "green")
            return True
        if item_id == 101:
            self.say("The Engineer Toolkit sharpens your awareness.", "green")
            self.perks["trap_detection"] = True
            return True

        self.say("You cannot use that item right now.")
        return False

    def shortest_path_step(self, start, target):
        queue = deque([start])
        came_from = {start: None}

        while queue:
            loc_id = queue.popleft()
            if loc_id == target:
                break
            for d, nxt in self.neighbors(loc_id):
                if nxt and nxt not in came_from:
                    came_from[nxt] = (loc_id, d)
                    queue.append(nxt)

        if target not in came_from:
            return None, 999

        cur = target
        path = []
        while came_from[cur] is not None:
            parent, direction = came_from[cur]
            path.append((parent, cur, direction))
            cur = parent
        path.reverse()
        if not path:
            return None, 0
        return path[0][2], len(path)

    def shortest_next_step_to_exit(self):
        step, _ = self.shortest_path_step(self.current_loc, 90)
        return step

    def use_map(self):
        if not self.has_item(100):
            self.say("You do not have a map.")
            return False
        hint = self.shortest_next_step_to_exit()
        if hint:
            if self.mutator.get("fog") and random.random() < 0.35:
                hint = random.choice(["N", "S", "E", "W"])
                self.say("Fog mutator distorts the map...")
            self.say(f"Map hint: safest route points {hint}")
        else:
            self.say("The map is too damaged to read here.")

        if self.perks["extra_move_on_map"]:
            self.map_boost_active = True
            self.say("Map momentum active: your next move can chain into a bonus move.")

        self.render_revealed_map()
        return True

    def render_revealed_map(self):
        nearby = []
        for d, nxt in self.neighbors(self.current_loc):
            if nxt:
                marker = "*" if nxt in self.revealed_rooms else "?"
                nearby.append(f"{d}:{nxt}{marker}")
        self.say(f"Map reveal: discovered {len(self.revealed_rooms)} rooms. Adjacent -> {' '.join(nearby)}")

    def room_visual_token(self, loc_id):
        if not loc_id:
            return "#####"
        if loc_id == self.current_loc:
            return f"@{loc_id:03d}"
        if any(
            npc.Hostile and npc.CurrentLocationID == loc_id and npc.ID not in self.defeated_npcs
            for npc in self.npcs
        ):
            return f"!{loc_id:03d}"
        loc = self.location(loc_id)
        if loc.ObjectID:
            return f"*{loc_id:03d}"
        if loc_id in self.revealed_rooms:
            return f".{loc_id:03d}"
        return f"?{loc_id:03d}"

    def format_visual_token(self, token):
        if token == "#####":
            return token
        marker = token[0]
        room = token[1:]
        color_map = {
            "@": "green",
            "!": "red",
            "*": "yellow",
            ".": "blue",
            "?": "cyan",
        }
        if self.style["color"] and marker in color_map:
            marker = self.colorize(marker, color_map[marker])
        return f"{marker}{room}"

    def render_ascii_minimap(self):
        loc = self.location()
        n = loc.N
        s = loc.S
        e = loc.E
        w = loc.W

        n_tok = self.room_visual_token(n)
        s_tok = self.room_visual_token(s)
        e_tok = self.room_visual_token(e)
        w_tok = self.room_visual_token(w)
        c_tok = self.room_visual_token(self.current_loc)
        blocked = self.get_blocked_direction()

        self.say("Mini-map (local):")
        self.say("                 [N]")
        self.say("              +-------+")
        self.say(f"              | {self.format_visual_token(n_tok):<5} |")
        self.say("              +---+---+")
        self.say("[W] +-------+ |       | +-------+ [E]")
        self.say(
            f"    | {self.format_visual_token(w_tok):<5} |-| {self.format_visual_token(c_tok):<5} |-| {self.format_visual_token(e_tok):<5} |"
        )
        self.say("    +-------+ +---+---+ +-------+")
        self.say("              |       |")
        self.say(f"              | {self.format_visual_token(s_tok):<5} |")
        self.say("              +-------+")
        if blocked:
            self.say(f"Map alert: direction {blocked} is currently blocked.", "yellow")
        self.say("Legend: @ you, ! hostile, * item, . explored, ? unknown, ##### wall")

    def neighbors(self, loc_id):
        loc = self.location(loc_id)
        return [("N", loc.N), ("S", loc.S), ("E", loc.E), ("W", loc.W)]

    def move_npcs(self):
        relic_rooms = [l.ID for l in self.locs if l.ObjectID in self.required_artifacts]

        for npc in self.npcs:
            if npc.ID in self.defeated_npcs or not npc.Hostile:
                continue
            if npc.CurrentLocationID <= 0:
                continue

            # Hunter aggressively chases player once awakened.
            if npc.ID == self.hunter_id and not self.hunter_awake:
                continue

            target = None
            if npc.ID == self.hunter_id:
                target = self.current_loc
            else:
                best_dist = 999
                for rr in relic_rooms:
                    _, dist = self.shortest_path_step(npc.CurrentLocationID, rr)
                    if dist < best_dist:
                        best_dist = dist
                        target = rr
                # Ambush flank: if close to player, prioritize player.
                _, pdist = self.shortest_path_step(npc.CurrentLocationID, self.current_loc)
                if pdist <= 3:
                    target = self.current_loc

            if target and target != npc.CurrentLocationID:
                step, _ = self.shortest_path_step(npc.CurrentLocationID, target)
                if step:
                    loc = self.location(npc.CurrentLocationID)
                    if step == "N" and loc.N:
                        npc.CurrentLocationID = loc.N
                    elif step == "S" and loc.S:
                        npc.CurrentLocationID = loc.S
                    elif step == "E" and loc.E:
                        npc.CurrentLocationID = loc.E
                    elif step == "W" and loc.W:
                        npc.CurrentLocationID = loc.W
                    continue

            if len(npc.Patrol) >= 2 and random.random() < 0.5:
                npc.CurrentLocationID = npc.Patrol[1] if npc.CurrentLocationID == npc.Patrol[0] else npc.Patrol[0]

    def handle_room_event(self):
        loc = self.location()
        if loc.EventResolved:
            return

        loc.EventResolved = True
        tag = loc.Tag

        if tag == "trap":
            if self.perks["trap_detection"]:
                self.say("You detect and avoid a trap.", "green")
                self.add_xp(5, "trap avoided")
                if self.has_item(101):
                    self.say("Toolkit synergy: salvaged parts become a Healing Herb.", "green")
                    if not self.has_item(104):
                        self.add_item(104)
            else:
                dmg = 12 if self.mutator.get("extra_traps") else 10
                self.health -= dmg
                self.say(f"A floor trap snaps shut. You lose {dmg} health.", "red")
                if random.random() < 0.35 and not loc.ObjectID:
                    loc.ObjectID = 103
                    self.say("The trap chamber hides a Cursed Idol. Risk and reward.", "yellow")

        elif tag == "treasure":
            chance = 0.85 if self.mutator.get("rich_loot") else 0.7
            if not loc.ObjectID and random.random() < chance:
                loc.ObjectID = random.choice([102, 104, 105])
            self.say("This side room feels rewarding. Keep searching.", "green")

        elif tag == "lore":
            snippet = random.choice(self.lore_snippets)
            if snippet not in self.lore_seen:
                self.lore_seen.add(snippet)
                self.say("Lore: " + snippet, "cyan")
                self.add_xp(5, "lore discovered")

        elif tag == "dark":
            if not self.has_item(1) and not self.has_item(2):
                self.health -= 3
                self.say("The darkness disorients you. You lose 3 health.", "yellow")
            else:
                self.say("Your light source keeps the darkness at bay.")

    def handle_quests_in_room(self):
        for q in self.quests:
            if q["room"] != self.current_loc or q["completed"]:
                continue

            if not q["accepted"]:
                q["accepted"] = True
                self.say(f"{q['giver']} offers quest: {q['title']}", "cyan")
                self.say(q["description"])

            if self.has_item(q["required_item"]):
                q["completed"] = True
                self.say(f"Quest complete: {q['title']}", "green")
                self.add_xp(q["reward_xp"], q["title"])
                self.reputation[q["faction"]] += 1
                reward_item = q["reward_item"]
                if reward_item and not self.has_item(reward_item):
                    if self.add_item(reward_item):
                        self.say("Reward received: " + self.obj_by_id[reward_item].Name, "green")
                    elif not self.location().ObjectID:
                        self.location().ObjectID = reward_item
                        self.say("Reward dropped at your feet: " + self.obj_by_id[reward_item].Name)

    def solve_rune(self, word):
        if self.current_loc != self.secret_room:
            self.say("No runes react here.")
            return False
        loc = self.location()
        if loc.SecretSolved:
            self.say("The rune mechanism is already solved.")
            return False
        if normalize(word) == self.secret_keyword:
            loc.SecretSolved = True
            loc.E = self.secret_shortcut_target
            self.say("Runes flare. A hidden eastern passage grinds open.", "green")
            self.add_xp(10, "secret solved")
            return True
        self.say("The runes remain silent.", "yellow")
        return False

    def class_scan(self):
        if self.player_class != "scout":
            self.say("Only scouts can use scan.")
            return False
        details = []
        for d, nxt in self.neighbors(self.current_loc):
            if nxt:
                nloc = self.location(nxt)
                details.append(f"{d}->{nxt}:{nloc.Tag}")
                self.revealed_rooms.add(nxt)
        self.say("Scout scan: " + (", ".join(details) if details else "no exits"), "cyan")
        self.add_xp(3, "scout scan")
        return True

    def class_analyze(self):
        if self.player_class != "scholar":
            self.say("Only scholars can use analyze.")
            return False
        if self.pending_encounter:
            npc = self.pending_encounter
            item = self.obj_by_id.get(npc.ObjectID)
            weak = item.Name if item else "unknown"
            self.say(f"Analyze: {npc.Name} weakness appears to be {weak}.", "cyan", log=True)
            self.add_xp(2, "combat analysis")
            return True
        snippet = random.choice(self.lore_snippets)
        if snippet not in self.lore_seen:
            self.lore_seen.add(snippet)
            self.say("Analyze uncovers lore: " + snippet, "cyan")
            self.add_xp(4, "scholar analysis")
            return True
        self.say("Analyze finds nothing new.")
        return False

    def class_powerstrike(self):
        if self.player_class != "fighter":
            self.say("Only fighters can use powerstrike.")
            return False
        if not self.pending_encounter:
            self.say("You can only powerstrike in combat.")
            return False
        npc = self.pending_encounter
        dmg = 24
        if self.perks.get("oil_torch_boost"):
            dmg += 8
            self.perks["oil_torch_boost"] = False
        if npc.IsBoss:
            npc.HP -= dmg
            self.say(f"Powerstrike hits {npc.Name} for {dmg} damage!", "green", log=True)
            self.advance_boss_phase(npc)
            if npc.HP <= 0:
                return self.defeat_npc(npc)
            return True

        npc.HP -= dmg
        self.say(f"Powerstrike hits {npc.Name} for {dmg} damage!", "green", log=True)
        if npc.HP <= 0:
            return self.defeat_npc(npc)

        retaliation = 8 + self.mutator.get("enemy_damage_bonus", 0)
        self.health -= retaliation
        self.say(f"{npc.Name} retaliates for {retaliation} damage.", "red", log=True)
        return True


class Location:
    """Locations in the game."""

    def __init__(self, loc, gen_text):
        rint = random.randint(0, len(gen_text) - 1)
        self.ID = to_int(loc["LOC_ID"])
        self.N = to_int(loc["LOC_N"])
        self.S = to_int(loc["LOC_S"])
        self.W = to_int(loc["LOC_W"])
        self.E = to_int(loc["LOC_E"])
        self.IsDark = to_int(loc.get("LOC_IS_DARK", 0))
        self.Story = gen_text[rint].Story if isna(loc["LOC_STORY"]) else loc["LOC_STORY"]
        self.Desc = gen_text[rint].Desc if isna(loc["LOC_DESC"]) else loc["LOC_DESC"]
        self.ObjectID = to_int(loc["LOC_OBJ_ID"])
        self.NpcID = to_int(loc["LOC_NPC_ID"])
        self.Tag = "safe"
        self.EventResolved = False
        self.SecretSolved = False


class Object:
    """Objects in the game."""

    def __init__(self, obj):
        self.ID = to_int(obj["OBJ_ID"])
        self.Desc = obj["OBJ_DESC"]
        self.Name = obj["OBJ_NAME"]
        self.Story = obj["OBJ_NARRATIVE"]
        self.RequiredToWin = obj["OBJ_WIN"]


class NPC:
    """Non-player characters."""

    def __init__(self, n):
        self.ID = to_int(n["NPC_ID"])
        self.Name = n["NPC_NAME"]
        self.Desc = n["NPC_DESC"]
        self.ObjectID = to_int(n["NPC_OBJID"])
        self.CanMove = n.get("NPC_CAN_MOVE", "")
        self.StartLocationID = to_int(n.get("NPC_START_LOC_ID", 0))
        self.CurrentLocationID = to_int(n.get("NPC_CURRENT_LOC_ID", 0))
        self.Hostile = True
        self.Patrol = []
        self.IsBoss = False
        self.HP = 40
        self.MaxHP = 40
        self.Phase = 1
        self.Telegraph = None


class Genloc:
    """Arbitrary text for game locations."""

    def __init__(self, gl):
        self.ID = to_int(gl["GEN_LOC_ID"])
        self.Story = gl["GEN_STORY"]
        self.Desc = gl["GEN_DESC"]


def locations_from_file(fname, g):
    try:
        rows = rows_from_csv(fname)
    except FileNotFoundError as exc:
        raise Exception("Cannot open locations file within data folder.") from exc
    try:
        return [Location(r, g) for r in rows]
    except Exception as exc:
        raise Exception("Cannot create LOCATION list.") from exc


def objects_from_file(fname):
    try:
        rows = rows_from_csv(fname)
    except FileNotFoundError as exc:
        raise Exception("Cannot open objects file within data folder.") from exc
    try:
        return [Object(o) for o in rows]
    except Exception as exc:
        raise Exception("Cannot create OBJECT list.") from exc


def npcs_from_file(fname):
    try:
        rows = rows_from_csv(fname)
    except FileNotFoundError as exc:
        raise Exception("Cannot open npcs file within data folder.") from exc
    try:
        return [NPC(n) for n in rows]
    except Exception as exc:
        raise Exception("ERROR: Cannot create NPC list.") from exc


def genlocs_from_file(file):
    try:
        rows = rows_from_csv(file)
    except FileNotFoundError as exc:
        raise Exception("Cannot open genlocs file within data folder.") from exc
    try:
        return [Genloc(gl) for gl in rows]
    except Exception as exc:
        raise Exception("Cannot create GENLOC list.") from exc


def add_bonus_objects(objs):
    bonus = [
        {
            "OBJ_ID": 100,
            "OBJ_NAME": "Explorer's Map",
            "OBJ_DESC": "an explorer's map",
            "OBJ_WIN": "",
            "OBJ_NARRATIVE": "You unfold the map and old routes shimmer into focus.",
        },
        {
            "OBJ_ID": 101,
            "OBJ_NAME": "Engineer Toolkit",
            "OBJ_DESC": "an engineer toolkit",
            "OBJ_WIN": "",
            "OBJ_NARRATIVE": "Tools clink together. You feel more prepared.",
        },
        {
            "OBJ_ID": 102,
            "OBJ_NAME": "Lucky Charm",
            "OBJ_DESC": "a lucky charm",
            "OBJ_WIN": "",
            "OBJ_NARRATIVE": "A small charm warms in your hand.",
        },
        {
            "OBJ_ID": 103,
            "OBJ_NAME": "Cursed Idol",
            "OBJ_DESC": "a cursed idol",
            "OBJ_WIN": "",
            "OBJ_NARRATIVE": "The idol hums with a dangerous pulse.",
        },
        {
            "OBJ_ID": 104,
            "OBJ_NAME": "Healing Herb",
            "OBJ_DESC": "a bundle of healing herb",
            "OBJ_WIN": "",
            "OBJ_NARRATIVE": "A sharp scent promises recovery.",
        },
        {
            "OBJ_ID": 105,
            "OBJ_NAME": "Oil Flask",
            "OBJ_DESC": "an oil flask",
            "OBJ_WIN": "",
            "OBJ_NARRATIVE": "The flask smells strongly of lamp oil.",
        },
    ]
    existing = {o.ID for o in objs}
    for row in bonus:
        if row["OBJ_ID"] not in existing:
            objs.append(Object(row))


def neighbors(loc):
    return [v for v in [loc.N, loc.S, loc.E, loc.W] if v]


def choose_mutator():
    options = [
        {
            "name": "None",
            "desc": "Standard dungeon conditions.",
            "enemy_damage_bonus": 0,
            "fog": False,
            "extra_traps": False,
            "rich_loot": False,
        },
        {
            "name": "Ironman",
            "desc": "Lower max health, no mercy.",
            "enemy_damage_bonus": 2,
            "fog": False,
            "extra_traps": False,
            "rich_loot": False,
        },
        {
            "name": "Fog of War",
            "desc": "Map hints can lie.",
            "enemy_damage_bonus": 0,
            "fog": True,
            "extra_traps": False,
            "rich_loot": False,
        },
        {
            "name": "Relentless Foes",
            "desc": "Enemies hit harder.",
            "enemy_damage_bonus": 5,
            "fog": False,
            "extra_traps": False,
            "rich_loot": False,
        },
        {
            "name": "Rich Vaults",
            "desc": "Treasure rooms are more generous.",
            "enemy_damage_bonus": 0,
            "fog": False,
            "extra_traps": False,
            "rich_loot": True,
        },
        {
            "name": "Hazard Floors",
            "desc": "Trap rooms hurt more.",
            "enemy_damage_bonus": 0,
            "fog": False,
            "extra_traps": True,
            "rich_loot": False,
        },
    ]
    return random.choice(options)


def assign_room_tags(locs):
    for loc in locs:
        if loc.ID in {1, 90}:
            loc.Tag = "safe"
            continue
        exits = len(neighbors(loc))
        roll = random.random()
        if loc.IsDark:
            loc.Tag = "dark"
        elif exits <= 1 and roll < 0.65:
            loc.Tag = "treasure"
        elif roll < 0.20:
            loc.Tag = "trap"
        elif roll < 0.35:
            loc.Tag = "lore"
        elif roll < 0.50:
            loc.Tag = "dark"
        else:
            loc.Tag = "safe"


def place_items_for_replayability(locs):
    loc_by_id = {l.ID: l for l in locs}
    for loc in locs:
        loc.ObjectID = 0

    valid_ids = [l.ID for l in locs if l.ID not in {1, 90}]
    random.shuffle(valid_ids)

    required = [2, 3, 4]
    for rid in required:
        if valid_ids:
            loc_by_id[valid_ids.pop()].ObjectID = rid

    bonus_pool = [1, 103, 104, 104, 105]
    for oid in bonus_pool:
        if valid_ids:
            loc_by_id[valid_ids.pop()].ObjectID = oid


def ensure_minimum_npcs(npcs):
    if len(npcs) >= 4:
        return
    next_id = max([n.ID for n in npcs], default=0) + 1
    templates = [
        {"NPC_NAME": "Gate Warden", "NPC_DESC": "a stern gate warden", "NPC_OBJID": 2},
        {"NPC_NAME": "Bone Duelist", "NPC_DESC": "a rattling bone duelist", "NPC_OBJID": 3},
        {"NPC_NAME": "Hex Librarian", "NPC_DESC": "a whispering hex librarian", "NPC_OBJID": 4},
        {"NPC_NAME": "The Hunter", "NPC_DESC": "a relentless hunter", "NPC_OBJID": 2},
    ]
    for tpl in templates:
        if len(npcs) >= 4:
            break
        npcs.append(
            NPC(
                {
                    "NPC_ID": next_id,
                    "NPC_NAME": tpl["NPC_NAME"],
                    "NPC_DESC": tpl["NPC_DESC"],
                    "NPC_OBJID": tpl["NPC_OBJID"],
                    "NPC_CAN_MOVE": "Y",
                    "NPC_START_LOC_ID": 0,
                    "NPC_CURRENT_LOC_ID": 0,
                }
            )
        )
        next_id += 1


def place_npcs_for_replayability(locs, npcs):
    loc_by_id = {l.ID: l for l in locs}
    spawnable = [l.ID for l in locs if l.ID not in {1, 90} and neighbors(l)]
    if not spawnable:
        return

    for npc in npcs:
        random.shuffle(spawnable)
        base = spawnable[0]
        nbs = neighbors(loc_by_id[base])
        patrol_to = random.choice(nbs) if nbs else base
        npc.StartLocationID = base
        npc.CurrentLocationID = base
        npc.Patrol = [base, patrol_to]
        npc.Hostile = True

        if normalize(npc.Name) == "the hunter":
            npc.ID = 998
            npc.Hostile = False


def add_boss_npc(npcs):
    boss = NPC(
        {
            "NPC_ID": 999,
            "NPC_NAME": "Arch-Dork",
            "NPC_DESC": "the Arch-Dork, master of the labyrinth",
            "NPC_OBJID": 4,
            "NPC_CAN_MOVE": "N",
            "NPC_START_LOC_ID": 89,
            "NPC_CURRENT_LOC_ID": 89,
        }
    )
    boss.IsBoss = True
    boss.HP = 120
    boss.MaxHP = 120
    boss.Phase = 1
    npcs.append(boss)


def choose_class(meta):
    unlocked = meta.get("unlocked_classes", ["adventurer"])
    default = meta.get("last_class", "adventurer")
    print(f"Unlocked classes: {', '.join(unlocked)}")
    choice = input(f"Choose class [{default}] > ").strip().lower()
    if not choice:
        return default
    if choice not in unlocked:
        print("Class not unlocked yet. Using default.")
        return default
    return choice


def prepare_world(locs, objs, npcs):
    add_bonus_objects(objs)
    assign_room_tags(locs)
    place_items_for_replayability(locs)
    ensure_minimum_npcs(npcs)
    place_npcs_for_replayability(locs, npcs)
    add_boss_npc(npcs)


if __name__ == "__main__":
    print("Run src/DunDork.py to launch the UI version.")
