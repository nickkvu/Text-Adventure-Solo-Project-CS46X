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
# Display Glyph Map (data symbol → terminal graphic)
######################################
GLYPH = {}  # populated from data["glyphs"] in run_game()

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
def display(room, player, status="", room_label=""):
    subprocess.run("cls" if os.name == "nt" else "clear", shell=True)
    label_suffix = f"  [{room_label}]" if room_label else ""
    print(f"=== TEXT ADVENTURE: BRAWL ==={label_suffix}")
    print("**Type [HELP] for commands**\n")

    _FALLBACK = ["?????"] * 5
    for row in range(room.height):
        sprites = []
        for col in range(room.width):
            # Check player
            if row == player.row and col == player.col:
                sprites.append(GLYPH.get(player.symbol, _FALLBACK))
            # Check bots
            elif any(b.alive and b.row == row and b.col == col for b in room.bots):
                sprites.append(GLYPH.get(room.bots[0].symbol, _FALLBACK))
            # Check dead bots
            elif any(not b.alive and b.row == row and b.col == col for b in room.bots):
                sprites.append(GLYPH["X"])
            # Check items
            elif any(not i.picked_up and i.row == row and i.col == col for i in room.items):
                sprites.append(GLYPH.get(room.items[0].symbol, _FALLBACK))
            # Default to grid tile
            else:
                sprites.append(GLYPH.get(room.grid[row][col], _FALLBACK))
        for sprite_row in range(5):
            print("".join(s[sprite_row] for s in sprites))

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
def display_help(help_data):
    subprocess.run("cls" if os.name == "nt" else "clear", shell=True)
    print("=== HELP ===\n")
    for section in help_data["sections"]:
        print(section["title"])
        for line in section["lines"]:
            print(line)
        print()
    input(help_data["prompt"])

######################################
# Win Screen
######################################
def win_screen(screen_data):
    subprocess.run("cls" if os.name == "nt" else "clear", shell=True)
    print("\n" * 3)
    for line in screen_data["lines"]:
        print(line)
    print()
    input(screen_data["prompt"])

######################################
# Game Over Screen
######################################
def game_over_screen(screen_data):
    subprocess.run("cls" if os.name == "nt" else "clear", shell=True)
    print("\n" * 3)
    for line in screen_data["lines"]:
        print(line)
    print()
    input(screen_data["prompt"])

######################################
# Bot Turn: Each Bot Shoots OR Moves
######################################
def bot_turn(room, player):
    messages = []
    for bot in room.bots:
        if not bot.alive:
            continue
        msg = bot.shoot(player, room)
        if msg:
            messages.append(msg)
        else:
            bot.move(room, player)
    return "\n".join(messages)

######################################
# Run The Game
######################################
def run_game():
    title_screen()

    data = load_data()
    GLYPH.update(data["glyphs"])
    DIRECTION_MAP = data["directions"]
    current_room_index = 0
    num_rooms = len(data["room"]["layouts"])

    # Build room — Room handles grid, bot spawns, item spawns
    room = Room(data["room"], data["bot"], data["item"], current_room_index)

    # Spawn player at center, making sure it's a floor tile
    player_row = room.height // 2
    player_col = room.width  // 2
    player = Player(data["player"], player_row, player_col)

    room_label = f"Room {current_room_index + 1}/{num_rooms}"
    display(room, player, room_label=room_label)

    while True:
        command = input("\n> ").strip().lower()
        verb, noun = parse(command)

        # --- Movement ---
        if verb in ('w', 'a', 's', 'd') or (verb in ('move', 'go') and noun in DIRECTION_MAP):
            direction = DIRECTION_MAP.get(noun or verb)
            status = player.move(direction, room.grid)
            bot_msg = bot_turn(room, player)
            display(room, player, "\n".join(filter(None, [status, bot_msg])), room_label)
            if player.hp <= 0:
                game_over_screen(data["screens"]["game_over"])
                break

        # --- Pick Up Item ---
        elif verb == 'pickup':
            picked = False
            for item in room.items:
                if not item.picked_up and item.row == player.row and item.col == player.col:
                    item.picked_up = True
                    player.weapon = item
                    picked = True
                    break
            bot_msg = bot_turn(room, player)
            pickup_msg = f"You picked up the {item.name}!" if picked else "There's nothing here to pick up."
            display(room, player, "\n".join(filter(None, [pickup_msg, bot_msg])), room_label)
            if player.hp <= 0:
                game_over_screen(data["screens"]["game_over"])
                break

        # --- Shooting ---
        elif verb == 'shoot':
            if noun not in DIRECTION_MAP:
                display(room, player, "Shoot which direction? Try: shoot north/south/east/west", room_label)
            else:
                direction = DIRECTION_MAP[noun]
                status = player.shoot(direction, room)

                if room.is_cleared():
                    display(room, player, status, room_label)
                    if current_room_index < num_rooms - 1:
                        input(data["ui"]["room_cleared_prompt"])
                        current_room_index += 1
                        room_label = f"Room {current_room_index + 1}/{num_rooms}"
                        room = Room(data["room"], data["bot"], data["item"], current_room_index)
                        player.row = room.height // 2
                        player.col = room.width  // 2
                        display(room, player, f"Entering Room {current_room_index + 1}...", room_label)
                    else:
                        win_screen(data["screens"]["win"])
                        break
                else:
                    bot_msg = bot_turn(room, player)
                    display(room, player, "\n".join(filter(None, [status, bot_msg])), room_label)
                    if player.hp <= 0:
                        game_over_screen(data["screens"]["game_over"])
                        break

        # --- Help HUD ---
        elif verb == 'help':
            display_help(data["help"])
            display(room, player, room_label=room_label)

        # --- Quit ---
        elif verb == 'q':
            print("LEAVING GAME, Thank you for playing!")
            break

        else:
            display(room, player, "Unknown command. Use [W, A, S, D] to move, 'shoot [direction]' to shoot, Q to quit.", room_label)

if __name__ == "__main__":
    run_game()