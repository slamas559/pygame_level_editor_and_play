# Pygame Platformer with Level Editor

A 2D tile-based platformer game built with **Python** and **Pygame**, featuring enemies, shooting mechanics, health system, and a custom **level editor** that allows you to design levels visually and export them as JSON.

---

## 🎮 Game Features
- Tile-based platformer movement
- Gravity, jumping, and falling mechanics
- Player shooting with cooldown
- Enemies that patrol, shoot, and take damage
- Player & enemy health system
- Collision detection (tiles, enemies, bullets)
- Background image support
- JSON-based level loading

---

## 🛠 Level Editor Features
- Visual tile placement using mouse
- Asset selection panel
- Delete mode for removing tiles or press **d**
- Save levels to `level_data.json`
- Levels load directly into the main game

---

## 📁 Project Structure
.
├── assets/
│ ├── background/
│ ├── player/
│ ├── raw_assets/
│ └── used_currently_png_assets
├── level_data.json
├── main.py # Main game
├── level_editor.py # Level editor
└── README.md

---

## ▶️ How to Run

### 1. Install dependencies
```bash
pip install pygame
```

### 2. Run the Level Editor (optional)

- python level_editor.py
- Place tiles and enemies
- Press S to save the level you created

### 3.  Run the Game
- python main.py

### NOTE:

the only **enemy** in this game is the **enemy.png** image in the list of assets you can
change it if you dont like or keep it. only if you name it enemy will it
work has an enemy, you may work your way around to add more enemy, different knid that
is up to you feel free to work around it.
---
and also there is presaved level in the level_data.json but when you create a new
level and you pressed **s** which saves it, it overwrite the former level on the 
level_data.json files you can make it accept many levels so you can switch between levels without clearing the others 
