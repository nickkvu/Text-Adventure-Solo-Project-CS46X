"""
Player class - inherits from Entity.
Handles movement and player-specific data
"""

from entity import Entity

DELTAS = {
    'w': (-1,  0),
    's': ( 1,  0),
    'a': ( 0, -1),
    'd': ( 0,  1)
}

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
        if self.weapon is None:
            return "You don't have a weapon! Pick one up first!"

        if direction not in DELTAS:
            return "Cannot Fire!"

        if self.weapon.weapon_type == 'shotgun':
            return self._shoot_shotgun(direction, room)
        else:
            return self._shoot_single(direction, room)

    def _shoot_single(self, direction, room):
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

    def _shoot_shotgun(self, direction, room):
        d_row, d_col = DELTAS[direction]

        # Three pellets: center ray + two spread rays perpendicular to travel axis
        if d_row != 0:  # firing north or south — spread left/right
            pellet_deltas = [(d_row, 0), (d_row, -1), (d_row, 1)]
        else:           # firing east or west — spread up/down
            pellet_deltas = [(0, d_col), (-1, d_col), (1, d_col)]

        messages = []
        hit_bots = set()

        for (pr, pc) in pellet_deltas:
            curr_row = self.row + pr
            curr_col = self.col + pc
            for _ in range(self.weapon.shoot_range):
                if room.grid[curr_row][curr_col] == room.wall:
                    break
                for bot in room.bots:
                    if bot.alive and bot.row == curr_row and bot.col == curr_col and id(bot) not in hit_bots:
                        hit_bots.add(id(bot))
                        messages.append(bot.take_damage(self.weapon.damage))
                        break
                curr_row += pr
                curr_col += pc

        if messages:
            return "\n".join(messages)
        return "Your shotgun blast didn't hit anything."
