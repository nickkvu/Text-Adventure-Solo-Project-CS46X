"""
Bot class - inherits from Entity
Passive for now. Will handle combat behavior in later stages
"""

from entity import Entity

class Bot(Entity):
    def __init__(self, data, row, col):
        super().__init__(data["symbol"], row, col)
        self.hp = data["hp"]
        self.alive = True

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            return "Direct hit! The bot has been destroyed!"
        return f"Direct hit! Bot HP: {self.hp}"