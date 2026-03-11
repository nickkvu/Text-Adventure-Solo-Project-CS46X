"""
Player class - inherits from Entity.
Handles movement and player-specific data
"""

from entity import Entity

class Player(Entity) : 
    def __init__(self, data, row, col) : 
        super().__init__(data["symbol"], row, col)
        self.hp = data["hp"]
        self.weapon = None

    def move(self, command, grid) : 
        new_row, new_col = self.row, self.col

        if command == 'w':
            new_row -= 1
        elif command == 's':
            new_row += 1
        elif command == 'a':
            new_col -= 1
        elif command == 'd':
            new_col += 1

        if grid[new_row][new_col] != '#':
            self.row, self.col = new_row, new_col
            return ""
        else:
            return "You ran into a wall!"
            
    def shoot(self, direction, room):
        DELTAS = {
            'w': (-1,  0),
            's': (1,  0),
            'a': (0, -1),
            'd': (0,  1)
        }

        if self.weapon is None:
            return "You don't have a weapon! Pick one up first!"

        if direction not in DELTAS:
            return "Cannot Fire!"

        d_row, d_col = DELTAS[direction]
        curr_row = self.row + d_row
        curr_col = self.col + d_col

        for _ in range(self.weapon.shoot_range):
            if room.grid[curr_row][curr_col] == room.wall:
                return "Your shot hit a wall!"

            for bot in room.bots:
                if bot.alive and bot.row == curr_row and bot.col == curr_col:
                    return bot.take_damage(self.weapon.damage)

            curr_row += d_row
            curr_col += d_col

        return "Your shot didn't reach anything."
