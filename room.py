"""
Room class - owns the grid, bots, and items for a single room
"""

import random
from bot import Bot
from item import Item


class Room:
    def __init__(self, room_data, bot_data, item_data):
        self.wall  = room_data["wall"]
        self.floor = room_data["floor"]
        self.grid  = self._build_grid(room_data["layout"])
        self.height = len(self.grid)
        self.width  = len(self.grid[0])

        # Spawn bots and items into random floor tiles
        occupied = set()
        self.bots  = self._spawn(Bot,  bot_data,  room_data["num_bots"],  occupied)
        self.items = self._spawn(Item, item_data, room_data["num_items"], occupied)

    ######################################
    # Build Grid From Layout
    ######################################
    def _build_grid(self, layout):
        return [list(row) for row in layout]

    ######################################
    # Spawn Entities Into Random Floor Tiles
    ######################################
    def _random_floor_tile(self, occupied):
        while True:
            row = random.randint(1, self.height - 2)
            col = random.randint(1, self.width  - 2)
            if (row, col) not in occupied and self.grid[row][col] == self.floor:
                return (row, col)

    def _spawn(self, cls, data, count, occupied):
        entities = []
        for _ in range(count):
            row, col = self._random_floor_tile(occupied)
            occupied.add((row, col))
            entities.append(cls(data, row, col))
        return entities

    ######################################
    # Win Condition
    ######################################
    def is_cleared(self):
        return all(not bot.alive for bot in self.bots)