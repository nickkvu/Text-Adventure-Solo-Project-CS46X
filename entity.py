"""
Base class for all entities in the game world (Player, Bot, Item)
"""

class Entity:
    def __init__(self, symbol, row, col):
        self.symbol = symbol
        self.row = row
        self.col = col

    def get_position(self):
        return (self.row, self.col)