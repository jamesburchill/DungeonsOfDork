from pathlib import Path
from types import SimpleNamespace
import importlib.util


MODULE_PATH = Path(__file__).resolve().parents[1] / "src" / "DunDorkCore.py"
SPEC = importlib.util.spec_from_file_location("DunDorkCore", MODULE_PATH)
DunDork = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DunDork)


def make_player():
    locs = [
        SimpleNamespace(
            ID=1,
            N=0,
            S=2,
            E=0,
            W=0,
            Story="Room 1 story",
            Desc="Room 1",
            ObjectID=0,
            NpcID=0,
            Tag="safe",
            EventResolved=False,
            SecretSolved=False,
        ),
        SimpleNamespace(
            ID=2,
            N=1,
            S=0,
            E=0,
            W=0,
            Story="Room 2 story",
            Desc="Room 2",
            ObjectID=0,
            NpcID=0,
            Tag="safe",
            EventResolved=False,
            SecretSolved=False,
        ),
    ]
    objs = [SimpleNamespace(ID=1, Name="Torch", Desc="a torch", Story="")]
    npcs = [
        SimpleNamespace(
            ID=1,
            Name="Gump",
            Desc="a gruesome gump",
            ObjectID=0,
            CurrentLocationID=-1,
            Hostile=True,
            IsBoss=False,
            HP=40,
            MaxHP=40,
            Phase=1,
            Telegraph=None,
            Patrol=[],
        )
    ]
    return DunDork.Player(locs, objs, npcs)


def test_quit_empty_confirm_does_not_exit(monkeypatch):
    player = make_player()
    player.new_location = False
    responses = iter(["q", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))

    result = player.get_user_input()

    assert result is False
    assert player.game_over is False


def test_quit_yes_exits(monkeypatch):
    player = make_player()
    player.new_location = False
    responses = iter(["q", "y"])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))

    result = player.get_user_input()

    assert result is True
    assert player.game_over is True


def test_drop_object_rejects_out_of_range_slot(monkeypatch):
    player = make_player()
    player.backpack[0] = 1
    monkeypatch.setattr("builtins.input", lambda _: "5")

    result = player.drop_object()

    assert result is False
    assert player.backpack[0] == 1


def test_drop_object_empty_confirmation_does_not_crash(monkeypatch):
    player = make_player()
    player.backpack[0] = 1
    responses = iter(["0", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))

    result = player.drop_object()

    assert result is False
    assert player.backpack[0] == 1


def test_move_uses_instance_locations_without_global_locs():
    player = make_player()

    result = player.move("S")

    assert result is True
    assert player.current_loc == 2


def test_list_npcs_ignores_out_of_bounds_npc_id():
    player = make_player()
    player.locs[player.current_loc - 1].NpcID = 999

    player.list_npcs()


def test_powerstrike_uses_high_damage_for_non_boss():
    player = make_player()
    player.player_class = "fighter"
    npc = player.npcs[0]
    npc.CurrentLocationID = player.current_loc
    player.pending_encounter = npc

    result = player.class_powerstrike()

    assert result is True
    assert npc.HP == 16


def test_attack_without_weakness_still_damages_enemy():
    player = make_player()
    npc = player.npcs[0]
    npc.ObjectID = 99  # weakness item player does not carry
    npc.CurrentLocationID = player.current_loc
    player.pending_encounter = npc

    result = player.resolve_attack()

    assert result is True
    assert npc.HP == 28
    assert player.health == 92


def test_attack_can_defeat_enemy_without_weakness():
    player = make_player()
    npc = player.npcs[0]
    npc.ObjectID = 99
    npc.CurrentLocationID = player.current_loc
    npc.HP = 10
    player.pending_encounter = npc

    result = player.resolve_attack()

    assert result is True
    assert player.pending_encounter is None
    assert npc.ID in player.defeated_npcs


def test_boss_telegraph_lethal_damage_ends_game_without_extra_input(monkeypatch):
    player = make_player()
    boss = SimpleNamespace(
        ID=999,
        Name="Arch-Dork",
        Desc="boss",
        ObjectID=0,
        CurrentLocationID=player.current_loc,
        Hostile=True,
        IsBoss=True,
        HP=120,
        MaxHP=120,
        Phase=1,
        Telegraph={"name": "Cataclysmic Arc", "damage": 16},
        Patrol=[],
    )
    player.pending_encounter = boss
    player.health = 10

    def fail_input(_):
        raise AssertionError("combat input should not be requested after lethal damage")

    monkeypatch.setattr("builtins.input", fail_input)
    player.handle_encounter_turn()

    assert player.game_over is True
    assert player.health <= 0


def test_quit_works_during_combat(monkeypatch):
    player = make_player()
    npc = player.npcs[0]
    npc.CurrentLocationID = player.current_loc
    player.pending_encounter = npc
    responses = iter(["q", "y"])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))

    player.handle_encounter_turn()

    assert player.game_over is True
