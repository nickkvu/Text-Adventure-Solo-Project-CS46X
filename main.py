"""
Text Adventure Game
Main Game Application (Entry Point)
"""

import os
import subprocess
import json

from player import Player
from room import Room
from parser import parse

######################################
# Load Game Data
######################################
def load_data():
    with open("data.json", "r") as f:
        return json.load(f)
    
######################################
# Display Initial Title Scrren
######################################
def title_screen():
    subprocess.run("cls" if os.name == "nt" else "clear", shell=True)
    title = """
     _____         _        _       _                 _                  
    |_   _|____  _| |_     / \   __| |_   _____ _ __ | |_ _   _ _ __ ___ 
      | |/ _ \ \/ / __|   / _ \ / _` \ \ / / _ \ '_ \| __| | | | '__/ _ \\
      | |  __/>  <| |_   / ___ \ (_| |\ V /  __/ | | | |_| |_| | | |  __/
      |_|\___/_/\_\\__|  /_/   \_\__,_| \_/ \___|_| |_|\__|\__,_|_|  \\___|

             B R A W L   S T A R S   :   T E X T   E D I T I O N
    """
    print(title)
    input("                         Press [ENTER] to Start!")

######################################
# Display Grid + HUD
######################################
def display(room, player, status=""):
    subprocess.run("cls" if os.name == "nt" else "clear", shell=True)
    print("=== TEXT ADVENTURE: BRAWL ===")
    print("**Type [HELP] for commands**\n")

    for row in range(room.height):
        row_display = ""
        for col in range(room.width):
            # Check player
            if row == player.row and col == player.col:
                row_display += player.symbol + " "
            # Check bots
            elif any(b.alive and b.row == row and b.col == col for b in room.bots):
                row_display += room.bots[0].symbol + " "
            # Check dead bots
            elif any(not b.alive and b.row == row and b.col == col for b in room.bots):
                row_display += "X "
            # Check items
            elif any(not i.picked_up and i.row == row and i.col == col for i in room.items):
                row_display += room.items[0].symbol + " "
            # Default to grid tile
            else:
                row_display += room.grid[row][col] + " "
        print(row_display)

    # HUD
    bot_hp_display = ", ".join(
        str(b.hp) if b.alive else "DEAD" for b in room.bots
    )
    print("\nMove: W A S D  |  Shoot: shoot [direction]  |  Quit: Q")

    weapon_display = player.weapon.name if player.weapon else "None"
    print(f"\nPlayer HP: {player.hp}  |  Bot HP: {bot_hp_display}  |  Weapon: {weapon_display}")

    print(f"Position: ({player.row}, {player.col})")

    if status:
        print(f"\n{status}")

######################################
# Help HUD
######################################
def display_help():
    subprocess.run("cls" if os.name == "nt" else "clear", shell=True)
    print("=== HELP ===\n")
    print("MOVEMENT")
    print("W / move north / go up      - Move up")
    print("S / move south / go down    - Move down")
    print("A / move west  / go left    - Move left")
    print("D / move east  / go right   - Move right\n")
    print("COMBAT")
    print("shoot north/south/east/west  - Shoot in a direction")
    print("pickup                       - Pick up item on your tile\n")
    print("SYMBOLS")
    print("@  - You (the player)")
    print("E  - Enemy bot")
    print("X  - Defeated bot")
    print("I  - Item / Weapon pickup")
    print("#  - Wall")
    print(".  - Floor\n")
    print("GOAL")
    print("Pick up a weapon and defeat all bots to clear the room!\n")
    input("Press [ENTER] to return to game...")

######################################
# Move All Living Bots Toward Player
######################################
def move_bots(room, player):
    for bot in room.bots:
        if bot.alive:
            bot.move(room, player)

######################################
# Run The Game
######################################
def run_game():
    title_screen()

    data = load_data()
    DIRECTION_MAP = data["directions"]
    current_room_index = 0
    num_rooms = len(data["room"]["layouts"])

    # Build room — Room handles grid, bot spawns, item spawns
    room = Room(data["room"], data["bot"], data["item"], current_room_index)

    # Spawn player at center, making sure it's a floor tile
    player_row = room.height // 2
    player_col = room.width  // 2
    player = Player(data["player"], player_row, player_col)

    display(room, player)

    while True:
        command = input("\n> ").strip().lower()
        verb, noun = parse(command)

        # --- Movement ---
        if verb in ('w', 'a', 's', 'd') or (verb in ('move', 'go') and noun in DIRECTION_MAP):
            direction = DIRECTION_MAP.get(noun or verb)
            status = player.move(direction, room.grid)
            move_bots(room, player)
            display(room, player, status)

        # --- Pick Up Item ---
        elif verb == 'pickup':
            picked = False
            for item in room.items:
                if not item.picked_up and item.row == player.row and item.col == player.col:
                    item.picked_up = True
                    player.weapon = item
                    picked = True
                    break
            move_bots(room, player)
            status = f"You picked up the {item.name}!" if picked else "There's nothing here to pick up."
            display(room, player, status)

        # --- Shooting ---
        elif verb == 'shoot':
            if noun not in DIRECTION_MAP:
                display(room, player, "Shoot which direction? Try: shoot north/south/east/west")
            else:
                direction = DIRECTION_MAP[noun]
                status = player.shoot(direction, room)

                if room.is_cleared():
                    display(room, player, status)
                    if current_room_index < num_rooms - 1:
                        input("\n*** ROOM CLEARED! Press [ENTER] to advance... ***")
                        current_room_index += 1
                        room = Room(data["room"], data["bot"], data["item"], current_room_index)
                        player.row = room.height // 2
                        player.col = room.width  // 2
                        display(room, player, f"Entering Room {current_room_index + 1}...")
                    else:
                        display(room, player, "*** ALL ROOMS CLEARED! YOU WIN! ***")
                        break
                else:
                    move_bots(room, player)
                    display(room, player, status)
        
        # --- Help HUD ---
        elif verb == 'help':
            display_help()
            display(room, player)

        # --- Quit ---
        elif verb == 'q':
            print("LEAVING GAME, Thank you for playing!")
            break

        else:
            display(room, player, "Unknown command. Use [W, A, S, D] to move, 'shoot [direction]' to shoot, Q to quit.")

if __name__ == "__main__":
    run_game()