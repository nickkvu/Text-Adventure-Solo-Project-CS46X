"""
test_game.py — Full test suite for Text Adventure: Brawl Stars Edition

Run from the project directory:  python -m unittest test_game -v

Test categories:
  TestParser                 - Unit tests for command parser
  TestEntity                 - Unit tests for Entity base class
  TestPlayerMovement         - Black-box tests for grid navigation
  TestPlayerShootingBlaster  - Black-box tests for single-shot weapon
  TestPlayerShootingShotgun  - Black-box tests for spread-shot weapon
  TestBotTakeDamage          - Unit tests for bot damage and death
  TestBotChase               - White-box tests for bot chase AI
  TestBotPatrol              - White-box tests for bot patrol AI
  TestBotShoot               - White-box tests for bot directional scan
  TestItemPickup             - Black-box tests for item/weapon pickup
  TestRoomGeneration         - White-box tests for spawn and room state
  TestDataConfiguration      - Integrity tests for data.json
  TestMultiRoomProgression   - Integration tests for room advancement
"""

import sys
import os
import json
import random
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parser import parse
from entity import Entity
from item   import Item
from player import Player
from bot    import Bot
from room   import Room
from main   import bottom_spawn

# ─────────────────────────────────────────────────────────────────────────────
# Shared fixtures
# ─────────────────────────────────────────────────────────────────────────────

BOT_DATA = {
    "symbol": "E", "hp": 3, "shoot_range": 2, "damage": 1, "chase_range": 3
}
PLAYER_DATA = {"symbol": "@", "hp": 10}
BLASTER_DATA = {
    "symbol": "I", "name": "Blaster", "weapon_type": "blaster",
    "shoot_range": 4, "damage": 1
}
SHOTGUN_DATA = {
    "symbol": "G", "name": "Shotgun", "weapon_type": "shotgun",
    "shoot_range": 1, "damage": 2
}
ITEMS_DATA = {"blaster": BLASTER_DATA, "shotgun": SHOTGUN_DATA}

# 7×7 open arena — all inner cells are floor
OPEN_GRID = [
    "#######",
    "#.....#",
    "#.....#",
    "#.....#",
    "#.....#",
    "#.....#",
    "#######",
]

# 5×5 grid with an interior wall at (2,2)
OBSTACLE_GRID = [
    "#####",
    "#...#",
    "#.#.#",
    "#...#",
    "#####",
]

# 10×10 open room used for spawn tests
SPAWN_GRID = [
    "##########",
    "#........#",
    "#........#",
    "#........#",
    "#........#",
    "#........#",
    "#........#",
    "#........#",
    "#........#",
    "##########",
]

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")


def make_mock_room(grid_lines, bots=None, items=None):
    """Lightweight room namespace — no random spawning, full control over state."""
    room = types.SimpleNamespace()
    room.grid   = [list(row) for row in grid_lines]
    room.wall   = '#'
    room.floor  = '.'
    room.bots   = bots  if bots  is not None else []
    room.items  = items if items is not None else []
    room.height = len(room.grid)
    room.width  = len(room.grid[0])
    return room


def make_real_room(grid_lines, num_bots=0, num_items=0,
                   item_type="blaster", difficulty="Test"):
    """Build an actual Room instance from controlled inline data."""
    room_data = {
        "wall": "#", "floor": ".",
        "layouts": [{
            "grid": grid_lines, "num_bots": num_bots,
            "num_items": num_items, "item_type": item_type,
            "difficulty": difficulty,
        }],
    }
    return Room(room_data, BOT_DATA, ITEMS_DATA, 0)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Parser — Unit Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestParser(unittest.TestCase):

    def test_shoot_north(self):
        self.assertEqual(parse("shoot north"), ("shoot", "north"))

    def test_shoot_south(self):
        self.assertEqual(parse("shoot south"), ("shoot", "south"))

    def test_shoot_east(self):
        self.assertEqual(parse("shoot east"), ("shoot", "east"))

    def test_shoot_west(self):
        self.assertEqual(parse("shoot west"), ("shoot", "west"))

    def test_move_west(self):
        self.assertEqual(parse("move west"), ("move", "west"))

    def test_go_north(self):
        self.assertEqual(parse("go north"), ("go", "north"))

    def test_single_movement_key(self):
        verb, noun = parse("w")
        self.assertEqual(verb, "w")
        self.assertIsNone(noun)

    def test_pickup_no_noun(self):
        verb, noun = parse("pickup")
        self.assertEqual(verb, "pickup")
        self.assertIsNone(noun)

    def test_empty_string_returns_none_none(self):
        self.assertEqual(parse(""), (None, None))

    def test_whitespace_only_returns_none_none(self):
        self.assertEqual(parse("   "), (None, None))

    def test_unrecognized_word_returns_none_none(self):
        self.assertEqual(parse("xyzabcdef"), (None, None))

    def test_shoot_without_direction(self):
        verb, noun = parse("shoot")
        self.assertEqual(verb, "shoot")
        self.assertIsNone(noun)

    def test_extra_words_ignored(self):
        verb, noun = parse("go west please hurry")
        self.assertEqual(verb, "go")
        self.assertEqual(noun, "west")

    def test_order_independent_verb_noun(self):
        # Parser finds verb and noun regardless of order
        verb, noun = parse("north shoot")
        self.assertEqual(verb, "shoot")
        self.assertEqual(noun, "north")

    def test_quit_command(self):
        verb, noun = parse("q")
        self.assertEqual(verb, "q")
        self.assertIsNone(noun)

    def test_help_command(self):
        verb, noun = parse("help")
        self.assertEqual(verb, "help")
        self.assertIsNone(noun)

    def test_case_insensitive(self):
        self.assertEqual(parse("SHOOT NORTH"), ("shoot", "north"))


# ─────────────────────────────────────────────────────────────────────────────
# 2. Entity — Unit Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestEntity(unittest.TestCase):

    def setUp(self):
        self.entity = Entity("@", 3, 4)

    def test_get_position_returns_tuple(self):
        self.assertEqual(self.entity.get_position(), (3, 4))

    def test_symbol_stored(self):
        self.assertEqual(self.entity.symbol, "@")

    def test_row_col_stored(self):
        self.assertEqual(self.entity.row, 3)
        self.assertEqual(self.entity.col, 4)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Player Movement — Black Box Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestPlayerMovement(unittest.TestCase):
    """
    Grid (OBSTACLE_GRID, 5×5):
      #####
      #...#   row 1: cols 1-3 are floor
      #.#.#   row 2: col 2 is interior wall
      #...#
      #####
    """

    def setUp(self):
        self.grid = [list(row) for row in OBSTACLE_GRID]
        self.player = Player(PLAYER_DATA, 1, 1)

    def test_move_south_updates_row(self):
        self.player.move('s', self.grid)
        self.assertEqual(self.player.row, 2)
        self.assertEqual(self.player.col, 1)

    def test_move_east_updates_col(self):
        self.player.move('d', self.grid)
        self.assertEqual(self.player.row, 1)
        self.assertEqual(self.player.col, 2)

    def test_move_north_updates_row(self):
        p = Player(PLAYER_DATA, 3, 1)
        p.move('w', self.grid)
        self.assertEqual(p.row, 2)

    def test_move_west_updates_col(self):
        p = Player(PLAYER_DATA, 1, 3)
        p.move('a', self.grid)
        self.assertEqual(p.col, 2)

    def test_successful_move_returns_empty_string(self):
        result = self.player.move('s', self.grid)
        self.assertEqual(result, "")

    def test_wall_north_blocked(self):
        # (1,1) north → (0,1) which is '#'
        result = self.player.move('w', self.grid)
        self.assertEqual(result, "You ran into a wall!")
        self.assertEqual(self.player.row, 1)

    def test_wall_west_blocked(self):
        result = self.player.move('a', self.grid)
        self.assertEqual(result, "You ran into a wall!")
        self.assertEqual(self.player.col, 1)

    def test_wall_south_blocked(self):
        p = Player(PLAYER_DATA, 3, 1)
        result = p.move('s', self.grid)
        self.assertEqual(result, "You ran into a wall!")
        self.assertEqual(p.row, 3)

    def test_wall_east_blocked(self):
        p = Player(PLAYER_DATA, 1, 3)
        result = p.move('d', self.grid)
        self.assertEqual(result, "You ran into a wall!")
        self.assertEqual(p.col, 3)

    def test_interior_wall_blocked(self):
        # (2,1) east → (2,2) which is '#' interior wall
        p = Player(PLAYER_DATA, 2, 1)
        result = p.move('d', self.grid)
        self.assertEqual(result, "You ran into a wall!")
        self.assertEqual(p.col, 1)

    def test_position_unchanged_after_wall_hit(self):
        start_row, start_col = self.player.row, self.player.col
        self.player.move('w', self.grid)  # hits north wall
        self.assertEqual(self.player.row, start_row)
        self.assertEqual(self.player.col, start_col)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Player Shooting — Blaster (Black Box Tests)
# ─────────────────────────────────────────────────────────────────────────────

class TestPlayerShootingBlaster(unittest.TestCase):
    """
    Open 7×7 arena, player at center (3,3).
    Bots placed at known positions to test directional shots.
    """

    def setUp(self):
        self.player = Player(PLAYER_DATA, 3, 3)
        self.player.weapon = Item(BLASTER_DATA, 0, 0)

    def _bot(self, row, col, hp=3):
        b = Bot(BOT_DATA, row, col)
        b.hp = hp
        return b

    def test_no_weapon_returns_message(self):
        self.player.weapon = None
        room = make_mock_room(OPEN_GRID)
        result = self.player.shoot('w', room)
        self.assertEqual(result, "You don't have a weapon! Pick one up first!")

    def test_shoot_north_hits_bot(self):
        bot = self._bot(1, 3)
        room = make_mock_room(OPEN_GRID, bots=[bot])
        result = self.player.shoot('w', room)
        self.assertIn("Direct hit", result)
        self.assertLess(bot.hp, 3)

    def test_shoot_south_hits_bot(self):
        bot = self._bot(5, 3)
        room = make_mock_room(OPEN_GRID, bots=[bot])
        self.assertIn("Direct hit", self.player.shoot('s', room))

    def test_shoot_east_hits_bot(self):
        bot = self._bot(3, 5)
        room = make_mock_room(OPEN_GRID, bots=[bot])
        self.assertIn("Direct hit", self.player.shoot('d', room))

    def test_shoot_west_hits_bot(self):
        bot = self._bot(3, 1)
        room = make_mock_room(OPEN_GRID, bots=[bot])
        self.assertIn("Direct hit", self.player.shoot('a', room))

    def test_range_one_misses_bot_two_tiles_away(self):
        short = Item({**BLASTER_DATA, "shoot_range": 1}, 0, 0)
        self.player.weapon = short
        bot = self._bot(1, 3)   # 2 tiles north of (3,3)
        room = make_mock_room(OPEN_GRID, bots=[bot])
        result = self.player.shoot('w', room)
        self.assertEqual(result, "Your shot didn't reach anything.")
        self.assertEqual(bot.hp, 3)

    def test_wall_stops_shot_before_bot(self):
        # Grid with wall at (3,3); player at (3,2), bot at (3,5)
        grid = [
            "#######",
            "#.....#",
            "#.....#",
            "#.#...#",   # wall at (3,2) — player shoots east from (3,1)
            "#.....#",
            "#.....#",
            "#######",
        ]
        player = Player(PLAYER_DATA, 3, 1)
        player.weapon = Item(BLASTER_DATA, 0, 0)
        bot = self._bot(3, 5)
        room = make_mock_room(grid, bots=[bot])
        result = player.shoot('d', room)
        self.assertEqual(result, "Your shot hit a wall!")
        self.assertEqual(bot.hp, 3)

    def test_kill_sets_bot_alive_false(self):
        bot = self._bot(3, 4, hp=1)   # 1 tile east, 1 HP
        room = make_mock_room(OPEN_GRID, bots=[bot])
        result = self.player.shoot('d', room)
        self.assertFalse(bot.alive)
        self.assertIn("destroyed", result)

    def test_empty_room_returns_miss_message(self):
        # shoot_range=2 so shot exhausts range before hitting the wall in a 7×7 grid
        self.player.weapon = Item({**BLASTER_DATA, "shoot_range": 2}, 0, 0)
        room = make_mock_room(OPEN_GRID, bots=[])
        result = self.player.shoot('w', room)
        self.assertEqual(result, "Your shot didn't reach anything.")


# ─────────────────────────────────────────────────────────────────────────────
# 5. Player Shooting — Shotgun (Black Box Tests)
# ─────────────────────────────────────────────────────────────────────────────

class TestPlayerShootingShotgun(unittest.TestCase):
    """
    Shotgun fires 3 pellets in a cone (center + 2 diagonals).
    shoot_range=1 so each pellet travels exactly 1 tile.
    Player at (3,3) in 7×7 open arena.
    """

    def setUp(self):
        self.player = Player(PLAYER_DATA, 3, 3)
        self.player.weapon = Item(SHOTGUN_DATA, 0, 0)

    def _bot(self, row, col):
        return Bot(BOT_DATA, row, col)

    def test_center_pellet_hits_bot_directly_ahead(self):
        # Shoot north — center pellet lands on (2,3)
        bot = self._bot(2, 3)
        room = make_mock_room(OPEN_GRID, bots=[bot])
        result = self.player.shoot('w', room)
        self.assertIn("Direct hit", result)

    def test_left_spread_pellet_hits_diagonal_bot(self):
        # Shoot north — left pellet lands on (2,2)
        bot = self._bot(2, 2)
        room = make_mock_room(OPEN_GRID, bots=[bot])
        result = self.player.shoot('w', room)
        self.assertIn("Direct hit", result)

    def test_right_spread_pellet_hits_diagonal_bot(self):
        # Shoot north — right pellet lands on (2,4)
        bot = self._bot(2, 4)
        room = make_mock_room(OPEN_GRID, bots=[bot])
        result = self.player.shoot('w', room)
        self.assertIn("Direct hit", result)

    def test_each_bot_hit_only_once(self):
        # Bot directly ahead; only center pellet reaches it — damage = 1×shotgun_damage
        bot = self._bot(2, 3)
        room = make_mock_room(OPEN_GRID, bots=[bot])
        self.player.shoot('w', room)
        self.assertEqual(bot.hp, BOT_DATA["hp"] - SHOTGUN_DATA["damage"])

    def test_east_spread_hits_up_and_down(self):
        # Shoot east: up-spread (-1,+1) lands on (2,4), down-spread (+1,+1) lands on (4,4)
        bot_up   = self._bot(2, 4)
        bot_down = self._bot(4, 4)
        room = make_mock_room(OPEN_GRID, bots=[bot_up, bot_down])
        self.player.shoot('d', room)
        self.assertTrue(bot_up.hp < BOT_DATA["hp"] or bot_down.hp < BOT_DATA["hp"])

    def test_no_bots_returns_miss_message(self):
        room = make_mock_room(OPEN_GRID, bots=[])
        result = self.player.shoot('w', room)
        self.assertIn("didn't hit anything", result)


# ─────────────────────────────────────────────────────────────────────────────
# 6. Bot Take Damage — Unit Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestBotTakeDamage(unittest.TestCase):

    def setUp(self):
        self.bot = Bot(BOT_DATA, 3, 3)

    def test_damage_reduces_hp(self):
        self.bot.take_damage(1)
        self.assertEqual(self.bot.hp, 2)

    def test_bot_alive_after_non_lethal_hit(self):
        self.bot.take_damage(2)
        self.assertTrue(self.bot.alive)

    def test_bot_dead_after_lethal_hit(self):
        self.bot.take_damage(3)
        self.assertFalse(self.bot.alive)

    def test_hp_clamped_to_zero_on_overkill(self):
        self.bot.take_damage(99)
        self.assertEqual(self.bot.hp, 0)

    def test_partial_damage_message_contains_hp(self):
        msg = self.bot.take_damage(1)
        self.assertIn("Direct hit", msg)
        self.assertIn("Bot HP: 2", msg)

    def test_kill_message_contains_destroyed(self):
        msg = self.bot.take_damage(3)
        self.assertIn("destroyed", msg)


# ─────────────────────────────────────────────────────────────────────────────
# 7. Bot Chase — White Box Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestBotChase(unittest.TestCase):
    """
    Chase triggers when abs(dr)+abs(dc) <= chase_range (3).
    All bots placed within distance 2 of player to guarantee chase branch.
    """

    def setUp(self):
        self.room = make_mock_room(OPEN_GRID)

    def _place_bot(self, row, col):
        bot = Bot(BOT_DATA, row, col)
        self.room.bots = [bot]
        return bot

    def test_bot_moves_south_toward_player_below(self):
        bot = self._place_bot(1, 3)
        player = Player(PLAYER_DATA, 3, 3)   # 2 rows below, within chase_range
        bot.move(self.room, player)
        self.assertGreater(bot.row, 1)

    def test_bot_moves_north_toward_player_above(self):
        bot = self._place_bot(5, 3)
        player = Player(PLAYER_DATA, 3, 3)
        bot.move(self.room, player)
        self.assertLess(bot.row, 5)

    def test_bot_moves_east_toward_player_right(self):
        bot = self._place_bot(3, 1)
        player = Player(PLAYER_DATA, 3, 3)
        bot.move(self.room, player)
        self.assertGreater(bot.col, 1)

    def test_bot_moves_west_toward_player_left(self):
        bot = self._place_bot(3, 5)
        player = Player(PLAYER_DATA, 3, 3)
        bot.move(self.room, player)
        self.assertLess(bot.col, 5)

    def test_bot_does_not_step_onto_player_tile(self):
        # Bot adjacent to player — should not land on player's tile
        bot = self._place_bot(3, 2)
        player = Player(PLAYER_DATA, 3, 3)
        bot.move(self.room, player)
        self.assertFalse(bot.row == player.row and bot.col == player.col)


# ─────────────────────────────────────────────────────────────────────────────
# 8. Bot Patrol — White Box Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestBotPatrol(unittest.TestCase):
    """
    Patrol triggers when abs(dr)+abs(dc) > chase_range (3).
    Player placed at (1,1), bot at (3,3): distance=4 > 3 → patrol guaranteed.
    Tests run across 50 random seeds to stress-test invariants.
    """

    def setUp(self):
        self.room = make_mock_room(OPEN_GRID)
        self.far_player = Player(PLAYER_DATA, 1, 1)

    def test_patrol_always_lands_on_floor_tile(self):
        bot = Bot(BOT_DATA, 3, 3)
        self.room.bots = [bot]
        for seed in range(50):
            random.seed(seed)
            bot.row, bot.col = 3, 3
            bot.move(self.room, self.far_player)
            cell = self.room.grid[bot.row][bot.col]
            self.assertEqual(cell, '.', f"Bot on non-floor tile at seed {seed}")

    def test_patrol_never_overlaps_other_bot(self):
        bot1 = Bot(BOT_DATA, 3, 3)
        bot2 = Bot(BOT_DATA, 3, 4)    # stationary blocker
        self.room.bots = [bot1, bot2]
        for seed in range(50):
            random.seed(seed)
            bot1.row, bot1.col = 3, 3
            bot1.move(self.room, self.far_player)
            overlap = (bot1.row == bot2.row and bot1.col == bot2.col)
            self.assertFalse(overlap, f"bot1 landed on bot2 at seed {seed}")

    def test_patrol_never_lands_on_player_tile(self):
        # Player at (3,4) — adjacent to bot's start, but also within chase_range=3
        # so use a player far away (patrol mode) whose tile happens to be reachable
        bot = Bot(BOT_DATA, 3, 3)
        self.room.bots = [bot]
        # Player at (1,1): distance=4>3 → patrol. Bot at (3,3) can move to (3,2),(3,4),(2,3),(4,3).
        # None of these is (1,1), so this also verifies the blocking code doesn't crash.
        for seed in range(50):
            random.seed(seed)
            bot.row, bot.col = 3, 3
            bot.move(self.room, self.far_player)
            on_player = (bot.row == self.far_player.row and bot.col == self.far_player.col)
            self.assertFalse(on_player, f"Bot landed on player at seed {seed}")


# ─────────────────────────────────────────────────────────────────────────────
# 9. Bot Shoot — White Box Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestBotShoot(unittest.TestCase):
    """
    Bot at various positions relative to player (3,3) in 7×7 arena.
    shoot_range=2, so player must be within 2 tiles in a straight line.
    """

    def setUp(self):
        self.player = Player(PLAYER_DATA, 3, 3)

    def test_hits_player_to_east(self):
        # Bot at (3,1), player at (3,3): 2 tiles east, within range
        bot = Bot(BOT_DATA, 3, 1)
        room = make_mock_room(OPEN_GRID, bots=[bot])
        bot.shoot(self.player, room)
        self.assertLess(self.player.hp, PLAYER_DATA["hp"])

    def test_hits_player_to_west(self):
        bot = Bot(BOT_DATA, 3, 5)
        room = make_mock_room(OPEN_GRID, bots=[bot])
        bot.shoot(self.player, room)
        self.assertLess(self.player.hp, PLAYER_DATA["hp"])

    def test_hits_player_to_south(self):
        bot = Bot(BOT_DATA, 1, 3)
        room = make_mock_room(OPEN_GRID, bots=[bot])
        bot.shoot(self.player, room)
        self.assertLess(self.player.hp, PLAYER_DATA["hp"])

    def test_hits_player_to_north(self):
        bot = Bot(BOT_DATA, 5, 3)
        room = make_mock_room(OPEN_GRID, bots=[bot])
        bot.shoot(self.player, room)
        self.assertLess(self.player.hp, PLAYER_DATA["hp"])

    def test_wall_between_bot_and_player_blocks_shot(self):
        # Wall at (3,2): bot at (3,1) shoots east, hits wall before player at (3,3)
        grid = [
            "#######",
            "#.....#",
            "#.....#",
            "#.#...#",   # wall at (3,2)
            "#.....#",
            "#.....#",
            "#######",
        ]
        bot = Bot(BOT_DATA, 3, 1)
        room = make_mock_room(grid, bots=[bot])
        bot.shoot(self.player, room)
        self.assertEqual(self.player.hp, PLAYER_DATA["hp"])

    def test_player_out_of_range_no_damage(self):
        # Bot at (3,1), player at (3,4): distance=3 > shoot_range=2
        self.player = Player(PLAYER_DATA, 3, 4)
        bot = Bot(BOT_DATA, 3, 1)
        room = make_mock_room(OPEN_GRID, bots=[bot])
        bot.shoot(self.player, room)
        self.assertEqual(self.player.hp, PLAYER_DATA["hp"])

    def test_no_hit_returns_empty_string(self):
        # Bot and player both in corners far apart, no line-of-sight
        self.player = Player(PLAYER_DATA, 1, 1)
        bot = Bot(BOT_DATA, 5, 5)
        room = make_mock_room(OPEN_GRID, bots=[bot])
        result = bot.shoot(self.player, room)
        self.assertEqual(result, "")

    def test_damage_amount_matches_bot_data(self):
        bot = Bot(BOT_DATA, 3, 1)
        room = make_mock_room(OPEN_GRID, bots=[bot])
        bot.shoot(self.player, room)
        self.assertEqual(self.player.hp, PLAYER_DATA["hp"] - BOT_DATA["damage"])


# ─────────────────────────────────────────────────────────────────────────────
# 10. Item Pickup — Black Box Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestItemPickup(unittest.TestCase):

    def setUp(self):
        self.player = Player(PLAYER_DATA, 2, 2)

    def _do_pickup(self, player, items):
        """Mirrors the pickup logic in main.py for isolated testing."""
        picked = False
        for item in items:
            if not item.picked_up and item.row == player.row and item.col == player.col:
                item.picked_up = True
                player.weapon = item
                picked = True
                break
        return picked

    def test_pickup_succeeds_on_same_tile(self):
        item = Item(BLASTER_DATA, 2, 2)
        self.assertTrue(self._do_pickup(self.player, [item]))

    def test_pickup_assigns_weapon_to_player(self):
        item = Item(BLASTER_DATA, 2, 2)
        self._do_pickup(self.player, [item])
        self.assertIs(self.player.weapon, item)

    def test_pickup_marks_item_as_picked_up(self):
        item = Item(BLASTER_DATA, 2, 2)
        self._do_pickup(self.player, [item])
        self.assertTrue(item.picked_up)

    def test_pickup_fails_when_player_not_on_tile(self):
        item = Item(BLASTER_DATA, 1, 1)   # different tile
        picked = self._do_pickup(self.player, [item])
        self.assertFalse(picked)
        self.assertIsNone(self.player.weapon)

    def test_pickup_fails_if_already_picked_up(self):
        item = Item(BLASTER_DATA, 2, 2)
        item.picked_up = True
        picked = self._do_pickup(self.player, [item])
        self.assertFalse(picked)

    def test_weapon_damage_stat_matches_item_data(self):
        item = Item(BLASTER_DATA, 2, 2)
        self._do_pickup(self.player, [item])
        self.assertEqual(self.player.weapon.damage, BLASTER_DATA["damage"])

    def test_weapon_range_stat_matches_item_data(self):
        item = Item(BLASTER_DATA, 2, 2)
        self._do_pickup(self.player, [item])
        self.assertEqual(self.player.weapon.shoot_range, BLASTER_DATA["shoot_range"])

    def test_weapon_type_matches_item_data(self):
        item = Item(BLASTER_DATA, 2, 2)
        self._do_pickup(self.player, [item])
        self.assertEqual(self.player.weapon.weapon_type, BLASTER_DATA["weapon_type"])

    def test_empty_item_list_no_pickup(self):
        picked = self._do_pickup(self.player, [])
        self.assertFalse(picked)
        self.assertIsNone(self.player.weapon)


# ─────────────────────────────────────────────────────────────────────────────
# 11. Room Generation — White Box Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestRoomGeneration(unittest.TestCase):

    def test_bots_spawn_on_floor_tiles(self):
        room = make_real_room(SPAWN_GRID, num_bots=3)
        for bot in room.bots:
            self.assertEqual(room.grid[bot.row][bot.col], '.')

    def test_items_spawn_on_floor_tiles(self):
        room = make_real_room(SPAWN_GRID, num_items=1)
        for item in room.items:
            self.assertEqual(room.grid[item.row][item.col], '.')

    def test_no_two_bots_share_a_tile(self):
        room = make_real_room(SPAWN_GRID, num_bots=4)
        positions = [(b.row, b.col) for b in room.bots]
        self.assertEqual(len(positions), len(set(positions)))

    def test_no_bot_and_item_share_a_tile(self):
        room = make_real_room(SPAWN_GRID, num_bots=3, num_items=1)
        bot_pos  = {(b.row, b.col) for b in room.bots}
        item_pos = {(i.row, i.col) for i in room.items}
        self.assertEqual(len(bot_pos & item_pos), 0)

    def test_room_height_matches_grid(self):
        room = make_real_room(SPAWN_GRID)
        self.assertEqual(room.height, len(SPAWN_GRID))

    def test_room_width_matches_grid(self):
        room = make_real_room(SPAWN_GRID)
        self.assertEqual(room.width, len(SPAWN_GRID[0]))

    def test_is_cleared_true_when_all_bots_dead(self):
        room = make_real_room(SPAWN_GRID, num_bots=2)
        for bot in room.bots:
            bot.alive = False
        self.assertTrue(room.is_cleared())

    def test_is_cleared_false_when_any_bot_alive(self):
        room = make_real_room(SPAWN_GRID, num_bots=2)
        room.bots[0].alive = False
        room.bots[1].alive = True
        self.assertFalse(room.is_cleared())

    def test_zero_items_produces_empty_list(self):
        room = make_real_room(SPAWN_GRID, num_items=0)
        self.assertEqual(room.items, [])

    def test_difficulty_stored_correctly(self):
        room = make_real_room(SPAWN_GRID, difficulty="Hard")
        self.assertEqual(room.difficulty, "Hard")

    def test_spawn_invariants_hold_across_random_seeds(self):
        for seed in range(20):
            random.seed(seed)
            room = make_real_room(SPAWN_GRID, num_bots=4, num_items=1)
            positions = [(b.row, b.col) for b in room.bots]
            self.assertEqual(len(positions), len(set(positions)),
                             f"Bot overlap at seed {seed}")
            for bot in room.bots:
                self.assertEqual(room.grid[bot.row][bot.col], '.',
                                 f"Bot on wall at seed {seed}")


# ─────────────────────────────────────────────────────────────────────────────
# 12. Data Configuration — Integrity Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestDataConfiguration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(DATA_PATH, "r") as f:
            cls.data = json.load(f)

    def test_file_loads_without_error(self):
        self.assertIsInstance(self.data, dict)

    def test_all_top_level_keys_present(self):
        for key in ("room", "player", "bot", "items", "directions", "glyphs", "screens", "help", "ui"):
            self.assertIn(key, self.data, f"Missing top-level key '{key}'")

    def test_room_has_at_least_one_layout(self):
        self.assertGreater(len(self.data["room"]["layouts"]), 0)

    def test_each_layout_has_required_fields(self):
        required = {"grid", "num_bots", "num_items", "difficulty"}
        for i, layout in enumerate(self.data["room"]["layouts"]):
            for field in required:
                self.assertIn(field, layout, f"Layout {i} missing '{field}'")

    def test_layouts_with_items_have_item_type(self):
        for i, layout in enumerate(self.data["room"]["layouts"]):
            if layout["num_items"] > 0:
                self.assertIn("item_type", layout,
                              f"Layout {i} has items but no 'item_type'")

    def test_all_grid_rows_are_consistent_width(self):
        for i, layout in enumerate(self.data["room"]["layouts"]):
            widths = {len(row) for row in layout["grid"]}
            self.assertEqual(len(widths), 1,
                             f"Layout {i} has inconsistent row widths: {widths}")

    def test_player_has_required_fields(self):
        for field in ("symbol", "hp"):
            self.assertIn(field, self.data["player"])

    def test_bot_has_required_fields(self):
        for field in ("symbol", "hp", "shoot_range", "damage", "chase_range"):
            self.assertIn(field, self.data["bot"])

    def test_items_has_blaster_and_shotgun(self):
        self.assertIn("blaster", self.data["items"])
        self.assertIn("shotgun", self.data["items"])

    def test_each_weapon_has_required_fields(self):
        required = {"symbol", "name", "weapon_type", "shoot_range", "damage"}
        for key, weapon in self.data["items"].items():
            for field in required:
                self.assertIn(field, weapon, f"Weapon '{key}' missing '{field}'")

    def test_directions_map_covers_all_aliases(self):
        for alias in ("north", "south", "east", "west", "w", "a", "s", "d"):
            self.assertIn(alias, self.data["directions"])

    def test_screens_has_win_and_game_over(self):
        self.assertIn("win",       self.data["screens"])
        self.assertIn("game_over", self.data["screens"])

    def test_all_room_spawn_points_are_floor(self):
        for i, layout in enumerate(self.data["room"]["layouts"]):
            room = make_real_room(
                layout["grid"], layout["num_bots"], layout["num_items"],
                layout.get("item_type", "blaster"), layout["difficulty"]
            )
            row, col = bottom_spawn(room)
            self.assertEqual(room.grid[row][col], '.',
                             f"Layout {i} spawn point is not a floor tile")


# ─────────────────────────────────────────────────────────────────────────────
# 13. Multi-Room Progression — Integration Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestMultiRoomProgression(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(DATA_PATH, "r") as f:
            cls.data = json.load(f)

    def _room(self, index):
        return Room(self.data["room"], self.data["bot"], self.data["items"], index)

    def test_room_not_cleared_at_start(self):
        self.assertFalse(self._room(0).is_cleared())

    def test_room_cleared_after_all_bots_killed(self):
        room = self._room(0)
        for bot in room.bots:
            bot.alive = False
        self.assertTrue(room.is_cleared())

    def test_new_room_has_correct_bot_count(self):
        for i, layout in enumerate(self.data["room"]["layouts"]):
            room = self._room(i)
            self.assertEqual(len(room.bots), layout["num_bots"],
                             f"Room {i+1} bot count mismatch")

    def test_player_spawn_is_floor_in_every_room(self):
        for i in range(len(self.data["room"]["layouts"])):
            room = self._room(i)
            row, col = bottom_spawn(room)
            self.assertEqual(room.grid[row][col], '.',
                             f"Room {i+1} spawn is not floor")

    def test_room1_has_blaster(self):
        room = self._room(0)
        self.assertEqual(len(room.items), 1)
        self.assertEqual(room.items[0].weapon_type, "blaster")

    def test_room2_has_shotgun(self):
        room = self._room(1)
        self.assertEqual(len(room.items), 1)
        self.assertEqual(room.items[0].weapon_type, "shotgun")

    def test_rooms_3_and_4_have_no_items(self):
        for i in (2, 3):
            self.assertEqual(len(self._room(i).items), 0,
                             f"Room {i+1} should have no items")

    def test_player_without_weapon_shoot_returns_message(self):
        # Simulates entering a room with no weapon (e.g. Rooms 3/4 before pickup)
        player = Player(self.data["player"], 3, 3)
        self.assertIsNone(player.weapon)
        room = self._room(2)
        result = player.shoot('w', room)
        self.assertEqual(result, "You don't have a weapon! Pick one up first!")

    def test_room_bots_are_independent_between_rooms(self):
        room1 = self._room(0)
        room2 = self._room(1)
        for b in room1.bots:
            b.alive = False
        # Killing room1 bots must not affect room2 bots
        self.assertTrue(any(b.alive for b in room2.bots))

    def test_all_rooms_load_without_exception(self):
        for i in range(len(self.data["room"]["layouts"])):
            try:
                room = self._room(i)
                self.assertIsNotNone(room)
            except Exception as e:
                self.fail(f"Room {i+1} raised an exception on load: {e}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
