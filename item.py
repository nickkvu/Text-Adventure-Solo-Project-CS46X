"""
Item class - inherits from Entity
Represents a pickup in the game world
"""

from entity import Entity

class Item(Entity):
    def __init__(self, data, row, col):
        super().__init__(data["symbol"], row, col)
        self.name = data["name"]
        self.shoot_range = data["shoot_range"]
        self.damage = data["damage"]
        self.picked_up = False