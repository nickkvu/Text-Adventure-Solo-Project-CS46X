# Text Adventure - Capstone Solo Project
**A Brawl Stars Inspired Game**


## Overview 
A text-based adventure game that takes inspiration from my favorite game Brawl Stars. The player navigates a grid-based arena, picks up weapons, and defeats enemy bots to clear the room.


## How To Run
**Requirements:** Python 3.7 or later. No external libraries required for now, as this is currently one Sprint into developemnt. 

```bash
python main.py
```


## How To Play

### Movement
| Command | Action |
|---|---|
| `W` | Move up |
| `S` | Move down |
| `A` | Move left |
| `D` | Move right |
| `move north/south/east/west` | Move by direction |
| `go up/down/left/right` | Move by direction |

### Combat
| Command | Action |
|---|---|
| `pickup` | Pick up a weapon on your current tile |
| `shoot north/south/east/west` | Shoot in a direction |

### Other
| Command | Action |
|---|---|
| `help` | Display help screen |
| `q` | Quit the game |

### Game Objective
Navigate the arean, pick up the weapon, and shoot all enemy bots to clear the room. Note: Series of rooms will be present in future Sprints.



## Grid Symbols
| Symbol | Meaning |
|---|---|
| `@` | Player |
| `E` | Enemy bot |
| `X` | Defeated bot |
| `I` | Item / Weapon pickup |
| `#` | Wall |
| `.` | Floor |



## Game Data
All game values are configured in `data.json` — including room layout, player HP, bot HP, weapon range, and damage. No code changes are needed to adjust game balance.



## Sprint 1 -- Completed Features
- Grid-based area with custom layouts loaded from the JSON data file
- Player movement with WASD and natural language
- Random bot and item spawning in each game
- Two-word command parser
- Item interaction
- Title and help screens
- Class hierarchy: `Entity` → `Player`, `Bot`, `Item`, `Room`