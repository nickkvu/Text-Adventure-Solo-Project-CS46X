"""
Bot class - inherits from Entity
Passive for now. Will handle combat behavior in later stages
"""

import random
from entity import Entity

class Bot(Entity):
    def __init__(self, data, row, col):
        super().__init__(data["symbol"], row, col)
        self.hp = data["hp"]
        self.shoot_range = data["shoot_range"]
        self.damage = data["damage"]
        self.chase_range = data["chase_range"]
        self.alive = True

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            return "Direct hit! The bot has been destroyed!"
        return f"Direct hit! Bot HP: {self.hp}"

    def move(self, room, player):
        dr = player.row - self.row
        dc = player.col - self.col

        if abs(dr) + abs(dc) <= self.chase_range:
            steps = self._chase_steps(dr, dc)
        else:
            steps = self._patrol_steps()

        for d_row, d_col in steps:
            new_row = self.row + d_row
            new_col = self.col + d_col
            if room.grid[new_row][new_col] == room.floor:
                blocked = any(
                    b is not self and b.alive and b.row == new_row and b.col == new_col
                    for b in room.bots
                )
                if not blocked and not (new_row == player.row and new_col == player.col):
                    self.row, self.col = new_row, new_col
                    return

    def _chase_steps(self, dr, dc):
        steps = []
        if abs(dr) >= abs(dc):
            if dr != 0: steps.append((1 if dr > 0 else -1, 0))
            if dc != 0: steps.append((0, 1 if dc > 0 else -1))
        else:
            if dc != 0: steps.append((0, 1 if dc > 0 else -1))
            if dr != 0: steps.append((1 if dr > 0 else -1, 0))
        return steps

    def _patrol_steps(self):
        dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        random.shuffle(dirs)
        return dirs

    def shoot(self, player, room):
        DELTAS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for d_row, d_col in DELTAS:
            for dist in range(1, self.shoot_range + 1):
                r = self.row + d_row * dist
                c = self.col + d_col * dist
                if room.grid[r][c] == room.wall:
                    break
                if r == player.row and c == player.col:
                    player.hp -= self.damage
                    return f"A bot shot you! (-{self.damage} HP)"
        return ""


class BossBot(Bot):
    _DELTA_SYMS = {
        (-1,  0): 'bullet_n',
        ( 1,  0): 'bullet_s',
        ( 0, -1): 'bullet_w',
        ( 0,  1): 'bullet_e',
    }

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            return "*** BOSS DEFEATED! The arena falls silent... ***"
        return f"BOSS HIT! Boss HP remaining: {self.hp}"

    def shoot(self, player, room, on_step=None):
        DELTAS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        positions = {d: [self.row + d[0], self.col + d[1]] for d in DELTAS}
        stopped = {d: False for d in DELTAS}
        hit = False

        for _ in range(self.shoot_range):
            active = [
                (positions[d][0], positions[d][1], self._DELTA_SYMS[d])
                for d in DELTAS if not stopped[d]
            ]
            if on_step and active:
                on_step(active)

            for d in DELTAS:
                if stopped[d]:
                    continue
                r, c = positions[d]
                if room.grid[r][c] == room.wall:
                    stopped[d] = True
                    continue
                if r == player.row and c == player.col:
                    player.hp -= self.damage
                    hit = True
                    stopped[d] = True
                    continue
                positions[d][0] += d[0]
                positions[d][1] += d[1]

            if all(stopped.values()):
                break

        if hit:
            return f"*** BOSS fires a CROSS BLAST! You were hit! (-{self.damage} HP) ***"
        return "*** BOSS fires a CROSS BLAST! ***"