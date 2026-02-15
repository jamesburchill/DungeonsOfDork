"""Tkinter frontend for Dungeons of Dork."""

from __future__ import annotations

import random
import re
import tkinter as tk
import importlib.util
import subprocess
import shutil
import threading
import queue
from pathlib import Path
from tkinter import messagebox, scrolledtext, simpledialog, ttk

try:
    import DunDorkCore as core
except ModuleNotFoundError:
    module_path = Path(__file__).resolve().with_name("DunDorkCore.py")
    spec = importlib.util.spec_from_file_location("DunDorkCore", module_path)
    core = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(core)


ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


class DorkTkApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Dungeons of Dork - Tkinter")
        self.root.geometry("980x680")
        self.command_queue: list[str] = []
        self.show_room_ids = False
        self.closing = False
        self.map_x_offset = -12
        self.player_avatar = "🙂"
        self.emoji_theme = True
        self.voice_enabled = False
        self.voice_available = shutil.which("say") is not None
        self.voice_queue: queue.Queue[str | None] = queue.Queue()
        self.last_spoken = ""
        self.voice_thread = threading.Thread(target=self._voice_worker, daemon=True)
        self.voice_thread.start()

        self.base_dir = Path(__file__).resolve().parent
        self.data_dir = self.base_dir / "data"
        self.meta_path = self.data_dir / "meta.json"

        self._build_ui()
        self.player = self._build_player()
        self.player.style["color"] = False
        self.player.style["typewriter"] = False
        self.player_avatar = self._player_avatar_emoji(self.player.player_class)
        self.root.protocol("WM_DELETE_WINDOW", self._shutdown)

        self.player.play_game()
        self.refresh_views()

    def _build_player(self):
        meta = core.load_meta(self.meta_path)
        mutator = core.choose_mutator()
        unlocked = meta.get("unlocked_classes", ["adventurer"])
        default_class = meta.get("last_class", "adventurer")
        chosen = simpledialog.askstring(
            "Choose Class",
            f"Unlocked classes: {', '.join(unlocked)}\nEnter class:",
            initialvalue=default_class,
            parent=self.root,
        )
        player_class = (chosen or default_class).strip().lower()
        if player_class not in unlocked:
            player_class = default_class

        gens = core.genlocs_from_file(self.data_dir / "genlocs.csv")
        npcs = core.npcs_from_file(self.data_dir / "npcs.csv")
        objs = core.objects_from_file(self.data_dir / "objects.csv")
        locs = core.locations_from_file(self.data_dir / "locations.csv", gens)
        core.prepare_world(locs, objs, npcs)

        return core.Player(
            locs,
            objs,
            npcs,
            meta=meta,
            meta_path=self.meta_path,
            mutator=mutator,
            player_class=player_class,
            input_func=self._game_input,
            output_func=self._game_output,
            show_ascii_minimap=False,
            interface_mode="ui",
        )

    def _build_ui(self):
        self.root.columnconfigure(0, weight=2)
        self.root.columnconfigure(1, weight=3)
        self.root.rowconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=0)

        left = ttk.Frame(self.root, padding=8)
        right = ttk.Frame(self.root, padding=8)
        left.grid(row=0, column=0, sticky="nsew")
        right.grid(row=0, column=1, sticky="nsew")
        left.rowconfigure(1, weight=1)
        right.rowconfigure(1, weight=1)
        right.rowconfigure(2, weight=1)
        right.columnconfigure(0, weight=1)

        ttk.Label(left, text="Map View", font=("Helvetica", 13, "bold")).grid(row=0, column=0, sticky="w")
        self.canvas = tk.Canvas(left, width=420, height=420, bg="#2b2216", highlightthickness=0)
        self.canvas.grid(row=1, column=0, sticky="nsew", pady=(6, 0))
        self.canvas.bind("<Configure>", lambda _event: self._draw_minimap())
        self.legend_var = tk.StringVar(value="")
        ttk.Label(left, textvariable=self.legend_var, wraplength=400, justify="left").grid(
            row=2, column=0, sticky="w", pady=(8, 0)
        )

        status_frame = ttk.Frame(right)
        status_frame.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        status_frame.columnconfigure(0, weight=1)
        self.status_var = tk.StringVar(value="")
        ttk.Label(status_frame, textvariable=self.status_var, justify="left").grid(row=0, column=0, sticky="w")
        self.room_hint_var = tk.StringVar(value="")
        ttk.Label(status_frame, textvariable=self.room_hint_var, justify="left").grid(row=1, column=0, sticky="w", pady=(2, 0))

        self.log = scrolledtext.ScrolledText(right, wrap="word", height=20, state="disabled")
        self.log.grid(row=1, column=0, sticky="nsew", pady=(8, 8))
        self.log.tag_configure("user", foreground="#2fbf71")
        self.log.tag_configure("system", foreground="#000000")

        inv_frame = ttk.LabelFrame(right, text="Inventory", padding=8)
        inv_frame.grid(row=2, column=0, sticky="nsew")
        inv_frame.columnconfigure(0, weight=1)
        self.inventory_var = tk.StringVar(value="")
        ttk.Label(inv_frame, textvariable=self.inventory_var, justify="left").grid(row=0, column=0, sticky="w")

        bottom = ttk.Frame(self.root, padding=8)
        bottom.grid(row=1, column=0, columnspan=2, sticky="ew")
        bottom.columnconfigure(0, weight=1)
        self.command_entry = ttk.Entry(bottom)
        self.command_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.command_entry.bind("<Return>", self._on_submit)
        ttk.Button(bottom, text="Send", command=self._on_submit).grid(row=0, column=1, padx=(0, 6))
        ttk.Button(bottom, text="Help", command=lambda: self._send_command("help")).grid(row=0, column=2, padx=(0, 6))
        ttk.Button(bottom, text="Status", command=lambda: self._send_command("status")).grid(
            row=0, column=3, padx=(0, 6)
        )
        ttk.Button(bottom, text="Inventory", command=lambda: self._send_command("inventory")).grid(
            row=0, column=4, padx=(0, 6)
        )
        ttk.Button(bottom, text="Map", command=lambda: self._send_command("map")).grid(row=0, column=5)
        self.emoji_toggle_btn = ttk.Button(bottom, text="Emoji: On", command=self._toggle_emoji_theme)
        self.emoji_toggle_btn.grid(row=0, column=6, padx=(0, 6))
        voice_text = self._voice_button_text()
        self.voice_toggle_btn = ttk.Button(
            bottom,
            text=voice_text,
            command=self._toggle_voice,
            state=("normal" if self.voice_available else "disabled"),
        )
        self.voice_toggle_btn.grid(row=0, column=7, padx=(0, 6))

        action_frame = ttk.LabelFrame(bottom, text="Actions", padding=6)
        action_frame.grid(row=1, column=0, columnspan=6, sticky="ew", pady=(8, 0))
        for col in range(8):
            action_frame.columnconfigure(col, weight=1)

        self.action_buttons = {}
        action_defs = [
            ("N", "move_n", lambda: self._send_command("N")),
            ("S", "move_s", lambda: self._send_command("S")),
            ("E", "move_e", lambda: self._send_command("E")),
            ("W", "move_w", lambda: self._send_command("W")),
            ("Look", "look", lambda: self._send_command("look")),
            ("Pickup", "pickup", self._action_pickup),
            ("Drop", "drop", self._action_drop),
            ("Use", "use", self._action_use),
            ("Attack", "attack", lambda: self._send_command("attack")),
            ("Flee", "flee", lambda: self._send_command("flee")),
            ("Powerstrike", "powerstrike", lambda: self._send_command("powerstrike")),
            ("Analyze", "analyze", lambda: self._send_command("analyze")),
            ("Scan", "scan", lambda: self._send_command("scan")),
            ("Rune", "rune", self._action_rune),
            ("Quests", "quests", lambda: self._send_command("quests")),
            ("Quit", "quit", lambda: self._send_command("quit")),
        ]
        for idx, (label, key, callback) in enumerate(action_defs):
            btn = tk.Button(
                action_frame,
                text=label,
                command=callback,
                fg="#000000",
                disabledforeground="#9a9a9a",
                relief=tk.RAISED,
                bd=2,
                highlightthickness=1,
                highlightbackground="#8f8f8f",
                activebackground="#f7f7f7",
                padx=6,
                pady=4,
            )
            btn.grid(row=idx // 8, column=idx % 8, padx=2, pady=2, sticky="ew")
            self.action_buttons[key] = btn

        self.command_entry.focus_set()

    def _strip_ansi(self, text: str) -> str:
        return ANSI_RE.sub("", text)

    def _item_emoji(self, item_id: int) -> str:
        by_id = {
            1: "torch",
            2: "amulet",
            3: "dagger",
            4: "book",
            100: "map",
            101: "toolkit",
            102: "charm",
            103: "idol",
            104: "herb",
            105: "oil",
        }
        by_key = {
            "torch": "🔥",
            "amulet": "🧿",
            "dagger": "🗡️",
            "book": "📖",
            "map": "🗺️",
            "toolkit": "🧰",
            "charm": "🍀",
            "idol": "🗿",
            "herb": "🌿",
            "oil": "🧪",
        }
        key = by_id.get(item_id)
        if key:
            return by_key.get(key, "📦")

        # Fallback by item name for any custom data rows.
        obj = self.player.obj_by_id.get(item_id)
        name = (obj.Name.lower() if obj else "")
        if "torch" in name:
            return "🔥"
        if "amulet" in name:
            return "🧿"
        if "dagger" in name:
            return "🗡️"
        if "book" in name or "spell" in name:
            return "📖"
        if "map" in name:
            return "🗺️"
        if "tool" in name or "kit" in name:
            return "🧰"
        if "charm" in name or "lucky" in name:
            return "🍀"
        if "idol" in name:
            return "🗿"
        if "herb" in name:
            return "🌿"
        if "oil" in name or "flask" in name:
            return "🧪"
        return "📦"

    def _token_emoji(self, token: str, item_id: int = 0) -> str:
        if token == "@":
            return self.player_avatar
        if token == "!":
            return "👹"
        if token == "*":
            return self._item_emoji(item_id) if item_id else "🎁"
        if token == ".":
            return self._item_emoji(item_id) if item_id else "·"
        if token == "?":
            return "❔"
        if token == "#":
            return "🧱"
        return token

    def _player_avatar_emoji(self, player_class: str) -> str:
        role = (player_class or "").strip().lower()
        role_map = {
            "adventurer": random.choice(["👨", "👩"]),
            "fighter": "🛡️",
            "scout": "🏹",
            "scholar": "📚",
            "wizard": "🧙",
            "ninja": "🥷",
            "zombie": "🧟",
            "rogue": "🗡️",
            "paladin": "⚔️",
            "ranger": "🏹",
            "cleric": "🕯️",
            "bard": "🎵",
        }
        return role_map.get(role, "🙂")

    def _toggle_emoji_theme(self):
        self.emoji_theme = not self.emoji_theme
        self.emoji_toggle_btn.configure(text=f"Emoji: {'On' if self.emoji_theme else 'Off'}")
        self.refresh_views()

    def _voice_button_text(self):
        if not self.voice_available:
            return "Voice: N/A"
        return "Disable Voice" if self.voice_enabled else "Enable Voice"

    def _toggle_voice(self):
        if not self.voice_available:
            return
        self.voice_enabled = not self.voice_enabled
        self.voice_toggle_btn.configure(text=self._voice_button_text())
        state_text = "Voice feedback enabled." if self.voice_enabled else "Voice feedback disabled."
        self._game_output(state_text)

    def _voice_worker(self):
        while True:
            text = self.voice_queue.get()
            if text is None:
                break
            if not text:
                continue
            try:
                # Sequential speech prevents overlapping "double stream" audio.
                subprocess.run(["say", text], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass

    def _queue_voice(self, text: str):
        if not self.voice_available or not self.voice_enabled:
            return
        cleaned = text.strip()
        if not cleaned:
            return
        if cleaned.startswith("[UI]"):
            return
        if cleaned.startswith("Chronicle:") or cleaned.startswith("📜 Chronicle:"):
            return
        if len(cleaned) > 220:
            cleaned = cleaned[:220]
        # Avoid immediate duplicate reads.
        if cleaned == self.last_spoken:
            return
        self.last_spoken = cleaned
        self.voice_queue.put(cleaned)

    def _action_button_label(self, key: str) -> str:
        plain = {
            "move_n": "N",
            "move_s": "S",
            "move_e": "E",
            "move_w": "W",
            "look": "Look",
            "pickup": "Pickup",
            "drop": "Drop",
            "use": "Use",
            "attack": "Attack",
            "flee": "Flee",
            "powerstrike": "Powerstrike",
            "analyze": "Analyze",
            "scan": "Scan",
            "rune": "Rune",
            "quests": "Quests",
            "quit": "Quit",
        }
        if not self.emoji_theme:
            return plain.get(key, key)

        themed = {
            "move_n": "⬆️ N",
            "move_s": "⬇️ S",
            "move_e": "➡️ E",
            "move_w": "⬅️ W",
            "look": "👁️ Look",
            "pickup": "🫳 Pickup",
            "drop": "🫴 Drop",
            "use": "🧪 Use",
            "attack": "⚔️ Attack",
            "flee": "🏃 Flee",
            "powerstrike": "💥 Strike",
            "analyze": "🧠 Analyze",
            "scan": "🔎 Scan",
            "rune": "🔮 Rune",
            "quests": "📜 Quests",
            "quit": "🚪 Quit",
        }
        return themed.get(key, key)

    def _plain_action_label(self, key: str) -> str:
        plain = {
            "move_n": "N",
            "move_s": "S",
            "move_e": "E",
            "move_w": "W",
            "look": "Look",
            "pickup": "Pickup",
            "drop": "Drop",
            "use": "Use",
            "attack": "Attack",
            "flee": "Flee",
            "powerstrike": "Powerstrike",
            "analyze": "Analyze",
            "scan": "Scan",
            "rune": "Rune",
            "quests": "Quests",
            "quit": "Quit",
        }
        return plain.get(key, key)

    def _game_output(self, message, is_user=False):
        text = self._strip_ansi(str(message))
        if text and set(text) == {"-"} and len(text) > 50:
            text = "-" * 42
        if not hasattr(self, "log"):
            return
        formatted = text
        self.log.configure(state="normal")
        tag = "user" if is_user else "system"
        self.log.insert("end", formatted + "\n\n", tag)
        self.log.see("end")
        self.log.configure(state="disabled")
        if not is_user:
            self._queue_voice(formatted)

    def _game_input(self, prompt: str) -> str:
        if self.command_queue:
            return self.command_queue.pop(0)

        prompt = self._strip_ansi(prompt)
        lower = prompt.lower()
        if "y/n" in lower or "are you sure" in lower:
            return "Y" if messagebox.askyesno("Confirm", prompt, parent=self.root) else "N"

        answer = simpledialog.askstring("Input Needed", prompt, parent=self.root)
        return (answer or "").strip()

    def _on_submit(self, _event=None):
        text = self.command_entry.get().strip()
        if not text:
            return
        self.command_entry.delete(0, "end")
        self._send_command(text)

    def _prompt_and_send(self, title: str, prompt: str, prefix: str):
        answer = simpledialog.askstring(title, prompt, parent=self.root)
        if answer is None:
            return
        value = answer.strip()
        if not value:
            return
        self._send_command(f"{prefix} {value}")

    def _action_pickup(self):
        self._prompt_and_send("Pickup", "Pickup what item?", "pickup")

    def _action_drop(self):
        self._prompt_and_send("Drop", "Drop which item (name or slot)?", "drop")

    def _action_use(self):
        self._prompt_and_send("Use Item", "Use what? (example: torch or torch with oil flask)", "use")

    def _action_rune(self):
        self._prompt_and_send("Rune", "Enter rune word:", "rune")

    def _send_command(self, command: str):
        if self.player.game_over:
            return

        before = self._snapshot_state()
        self._game_output(command, is_user=True)
        util_cmd = command.strip().lower()

        if self.player.pending_encounter:
            if util_cmd in {"i", "inventory", "backpack"}:
                self._game_output("[UI] Inventory is shown in the panel on the right.")
                self.refresh_views()
                return
            if util_cmd == "status":
                self._game_output("[UI] Status is shown at the top of the right panel.")
                self.refresh_views()
                return
            if util_cmd in {"h", "help", "?"}:
                self.player.show_instructions()
                self.refresh_views()
                return

            self.command_queue.append(command)
            self.player.handle_encounter_turn()
        else:
            if util_cmd in {"i", "inventory", "backpack"}:
                self._game_output("[UI] Inventory is shown in the panel on the right.")
                self.refresh_views()
                return
            if util_cmd == "status":
                self._game_output("[UI] Status is shown at the top of the right panel.")
                self.refresh_views()
                return
            verb, args = self.player.parse_command(command)
            acted = self.player.execute_command(verb, args)
            if acted and not self.player.game_over:
                self.player.turn_count += 1
                self.player.spawn_timed_events()
                self.player.move_npcs()
                self.player.apply_end_of_turn_effects()
                self.player.check_player_death()
                if self.player.new_location and not self.player.game_over:
                    self.player.play_game()
            else:
                self.player.check_player_death()

        after = self._snapshot_state()
        self._emit_state_delta(before, after, command)
        self.refresh_views()

        if self.player.game_over:
            self._shutdown()

    def _shutdown(self):
        if self.closing:
            return
        self.closing = True
        if hasattr(self, "player") and not self.player.game_over:
            self.player.quit_game()
        try:
            self.voice_queue.put(None)
        except Exception:
            pass
        self.root.after(0, self.root.destroy)

    def _snapshot_state(self):
        return {
            "room": self.player.current_loc,
            "hp": self.player.health,
            "max_hp": self.player.max_health,
            "xp": self.player.xp,
            "inventory": {item_id for item_id in self.player.backpack if item_id is not None},
            "quests": sum(1 for q in self.player.quests if q["completed"]),
            "combat": bool(self.player.pending_encounter),
            "game_over": self.player.game_over,
        }

    def _emit_state_delta(self, before, after, command_text=""):
        changes = []

        if after["room"] != before["room"]:
            verb, args = self.player.parse_command(command_text or "")
            if verb == "MOVE" and args:
                direction_words = {"N": "north", "S": "south", "E": "east", "W": "west"}
                label = direction_words.get(args[0], args[0].lower())
                changes.append(f"You moved {label}.")
            else:
                changes.append("You moved to a new room.")

        hp_delta = after["hp"] - before["hp"]
        if hp_delta != 0:
            sign = "+" if hp_delta > 0 else ""
            changes.append(f"HP {sign}{hp_delta} ({after['hp']}/{after['max_hp']})")

        xp_delta = after["xp"] - before["xp"]
        if xp_delta != 0:
            sign = "+" if xp_delta > 0 else ""
            changes.append(f"XP {sign}{xp_delta} (total {after['xp']})")

        gained = after["inventory"] - before["inventory"]
        lost = before["inventory"] - after["inventory"]
        for item_id in sorted(gained):
            changes.append(f"Gained {self.player.obj_by_id[item_id].Name}")
        for item_id in sorted(lost):
            changes.append(f"Lost {self.player.obj_by_id[item_id].Name}")

        if after["quests"] != before["quests"]:
            changes.append(f"Quests completed {before['quests']} -> {after['quests']}")

        if before["combat"] != after["combat"]:
            changes.append("Encounter started" if after["combat"] else "Encounter ended")

        if not before["game_over"] and after["game_over"]:
            changes.append("Run ended")

        if changes:
            prefix = "📜 Chronicle:" if self.emoji_theme else "Chronicle:"
            self._game_output(prefix + " " + " | ".join(changes))

    def refresh_views(self):
        completed = sum(1 for q in self.player.quests if q["completed"])
        if self.emoji_theme:
            self.status_var.set(
                "📍 {room}    ❤️ {hp}/{max_hp}    ✨ {xp}    📜 {done}/3    🧭 {cls}    🌀 {mut}".format(
                    room=self.player.current_loc,
                    hp=self.player.health,
                    max_hp=self.player.max_health,
                    xp=self.player.xp,
                    done=completed,
                    cls=self.player.player_class,
                    mut=self.player.mutator["name"],
                )
            )
        else:
            self.status_var.set(
                "Room: {room}    HP: {hp}/{max_hp}    XP: {xp}    Quests: {done}/3    Class: {cls}    Mutator: {mut}".format(
                    room=self.player.current_loc,
                    hp=self.player.health,
                    max_hp=self.player.max_health,
                    xp=self.player.xp,
                    done=completed,
                    cls=self.player.player_class,
                    mut=self.player.mutator["name"],
                )
            )
        self._refresh_room_hint()

        items = [item_id for item_id in self.player.backpack if item_id is not None]
        if not items:
            self.inventory_var.set("Empty")
        elif self.emoji_theme:
            self.inventory_var.set(
                "\n".join(f"- {self._item_emoji(item_id)} {self.player.obj_by_id[item_id].Name}" for item_id in items)
            )
        else:
            self.inventory_var.set("\n".join(f"- {self.player.obj_by_id[item_id].Name}" for item_id in items))
        if self.emoji_theme:
            self.legend_var.set(
                "Legend: "
                f"{self.player_avatar} you, 👹 hostile, 🎁 item room, · explored, ❔ unknown, 🔒 sealed exit "
                "(missing directions are not drawn)"
            )
        else:
            self.legend_var.set("Legend: @ you, ! hostile, * item, . explored, ? unknown, sealed exit (missing directions hidden)")
        self._update_action_buttons()
        self._draw_minimap()

    def _refresh_room_hint(self):
        loc = self.player.location()
        parts = []

        if loc.ObjectID:
            obj = self.player.obj_by_id.get(loc.ObjectID)
            if obj:
                label = f"{self._item_emoji(obj.ID)} {obj.Name}" if self.emoji_theme else obj.Name
                parts.append(f"Here: {label}")

        npcs_here = [
            npc
            for npc in self.player.npcs
            if npc.CurrentLocationID == self.player.current_loc and npc.ID not in self.player.defeated_npcs
        ]
        if npcs_here:
            hostile = any(npc.Hostile for npc in npcs_here)
            if hostile:
                parts.append("Threat nearby")
            else:
                parts.append("Presence nearby")

        if not parts:
            parts.append("Here: nothing obvious")

        self.room_hint_var.set("   |   ".join(parts))

    def _set_button_state(self, key: str, enabled: bool):
        if key not in self.action_buttons:
            return
        state = tk.NORMAL if enabled else tk.DISABLED
        btn = self.action_buttons[key]
        label = self._action_button_label(key) if enabled else self._plain_action_label(key)
        if enabled:
            btn.configure(state=state, fg="#000000", bd=2, highlightthickness=1, text=label)
        else:
            btn.configure(state=state, fg="#9a9a9a", bd=1, highlightthickness=0, text=label)

    def _update_action_buttons(self):
        in_combat = bool(self.player.pending_encounter)
        game_over = self.player.game_over
        loc = self.player.location()
        blocked = self.player.get_blocked_direction()
        movement = {
            "move_n": bool(loc.N) and blocked != "N",
            "move_s": bool(loc.S) and blocked != "S",
            "move_e": bool(loc.E) and blocked != "E",
            "move_w": bool(loc.W) and blocked != "W",
        }

        for key, can_move in movement.items():
            self._set_button_state(key, can_move and not in_combat and not game_over)

        self._set_button_state("look", not game_over and not in_combat)
        self._set_button_state("pickup", not game_over and not in_combat)
        self._set_button_state("drop", not game_over and not in_combat)
        self._set_button_state("rune", not game_over and not in_combat)
        self._set_button_state("quests", not game_over and not in_combat)
        self._set_button_state("scan", not game_over and not in_combat and self.player.player_class == "scout")

        self._set_button_state("attack", not game_over and in_combat)
        self._set_button_state("flee", not game_over and in_combat)
        self._set_button_state("powerstrike", not game_over and in_combat and self.player.player_class == "fighter")
        self._set_button_state("analyze", not game_over and in_combat and self.player.player_class == "scholar")

        # Item usage is valid both in and out of combat.
        self._set_button_state("use", not game_over)
        self._set_button_state("quit", not game_over)

    def _room_kind(self, loc_id):
        if not loc_id:
            return "#"
        if loc_id == self.player.current_loc:
            return "@"
        if loc_id not in self.player.revealed_rooms:
            return "?"
        if any(
            npc.Hostile and npc.CurrentLocationID == loc_id and npc.ID not in self.player.defeated_npcs
            for npc in self.player.npcs
        ):
            return "!"
        loc = self.player.location(loc_id)
        if loc.ObjectID:
            return "*"
        if loc_id in self.player.revealed_rooms:
            return "."
        return "?"

    def _draw_cell(self, cx, cy, token, label, size):
        x1 = cx - size
        y1 = cy - size
        x2 = cx + size
        y2 = cy + size
        color = {
            "@": "#2fbf71",
            "!": "#d64545",
            "*": "#e0b437",
            ".": "#4f7fd8",
            "?": "#5d6d7a",
            "#": "#273043",
        }[token]
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#dbe5f0", width=2)
        if token == "#":
            # Fill wall tiles with a brick pattern so blocked rooms feel solid.
            cols = 3
            rows = 3
            x_step = (size * 2) / (cols + 1)
            y_step = (size * 2) / (rows + 1)
            start_x = cx - size + x_step
            start_y = cy - size + y_step
            for r in range(rows):
                for c in range(cols):
                    self.canvas.create_text(
                        start_x + (c * x_step),
                        start_y + (r * y_step),
                        text="🧱",
                        fill="white",
                        font=("Apple Color Emoji", 14),
                    )
            return
        loc = self.player.location(label) if label else None
        item_id = loc.ObjectID if loc else 0
        if self.emoji_theme:
            marker = self._token_emoji(token, item_id=item_id)
            self.canvas.create_text(cx, cy, text=marker, fill="white", font=("Apple Color Emoji", 24))
            if token == "@" and item_id:
                self.canvas.create_text(
                    cx + 26, cy - 26, text=self._item_emoji(item_id), fill="white", font=("Apple Color Emoji", 14)
                )
        elif token == "@":
            self.canvas.create_text(cx, cy, text=self.player_avatar, fill="white", font=("Apple Color Emoji", 24))
            if item_id:
                self.canvas.create_text(cx + 26, cy - 26, text=self._item_emoji(item_id), fill="white", font=("Apple Color Emoji", 14))
        elif item_id and token in {"*", "."}:
            item_emoji = self._item_emoji(item_id)
            self.canvas.create_text(cx, cy, text=item_emoji, fill="white", font=("Apple Color Emoji", 24))
        else:
            self.canvas.create_text(cx, cy, text=token, fill="white", font=("Courier", 22, "bold"))
        if self.show_room_ids:
            self.canvas.create_text(cx, cy + 20, text=f"{label:03d}", fill="#dbe5f0", font=("Courier", 9, "bold"))

    def _draw_minimap(self):
        if not hasattr(self, "player"):
            return
        self.canvas.delete("all")
        loc = self.player.location()
        blocked = self.player.get_blocked_direction()
        width = max(self.canvas.winfo_width(), 420)
        height = max(self.canvas.winfo_height(), 420)

        hpad = 24
        top_pad = 34
        bottom_pad = 46
        gap_between_tiles = 10
        tile_half = int(
            min(
                (width - (hpad * 2) - (gap_between_tiles * 2)) / 6,
                (height - top_pad - bottom_pad - (gap_between_tiles * 2)) / 6,
            )
        )
        tile_half = max(34, min(tile_half, 88))
        center_spacing = (tile_half * 2) + gap_between_tiles
        cx = (width // 2) + self.map_x_offset
        cy = (height - bottom_pad + top_pad) // 2

        neighbors = {
            "N": (cx, cy - center_spacing, loc.N),
            "W": (cx - center_spacing, cy, loc.W),
            "E": (cx + center_spacing, cy, loc.E),
            "S": (cx, cy + center_spacing, loc.S),
        }

        # Draw connectors only for accessible directions.
        connector_segments = {}
        if loc.N:
            connector_segments["N"] = (cx, cy - tile_half, cx, cy - center_spacing + tile_half)
        if loc.S:
            connector_segments["S"] = (cx, cy + tile_half, cx, cy + center_spacing - tile_half)
        if loc.W:
            connector_segments["W"] = (cx - tile_half, cy, cx - center_spacing + tile_half, cy)
        if loc.E:
            connector_segments["E"] = (cx + tile_half, cy, cx + center_spacing - tile_half, cy)

        for seg in connector_segments.values():
            self.canvas.create_line(*seg, fill="#dbe5f0", width=3)

        # Draw current room first.
        self._draw_cell(cx, cy, "@", self.player.current_loc, tile_half)

        for key, (x, y, room_id) in neighbors.items():
            if not room_id:
                continue
            token = self._room_kind(room_id)
            self._draw_cell(x, y, token, room_id or 0, tile_half)
            label_y = y + tile_half + 24 if key == "S" else y - tile_half - 22
            if blocked == key:
                label_text = f"{key} 🔒" if self.emoji_theme else f"{key} (sealed)"
            else:
                label_text = key
            label_color = "#ffcc66" if blocked == key else "#dbe5f0"
            self.canvas.create_text(x, label_y, text=label_text, fill=label_color, font=("Helvetica", 9, "bold"))

        if blocked in connector_segments:
            self.canvas.create_line(*connector_segments[blocked], fill="#ffcc66", width=5, dash=(6, 4))
            x1, y1, x2, y2 = connector_segments[blocked]
            lock_x = (x1 + x2) / 2
            lock_y = (y1 + y2) / 2
            lock_text = "🔒" if self.emoji_theme else "LOCK"
            lock_font = ("Apple Color Emoji", 14) if self.emoji_theme else ("Helvetica", 9, "bold")
            self.canvas.create_text(lock_x, lock_y, text=lock_text, fill="#ffcc66", font=lock_font)

        if blocked:
            self.canvas.create_text(
                cx,
                height - 16,
                text=f"Blocked direction: {blocked}",
                fill="#ffcc66",
                font=("Helvetica", 10, "bold"),
            )
        else:
            self.canvas.create_text(cx, height - 16, text="", fill="#dbe5f0", font=("Helvetica", 10, "bold"))


def main():
    random.seed()
    root = tk.Tk()
    DorkTkApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
