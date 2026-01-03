import pygame
import json
import sys
import os

pygame.init()

# Constants
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 600
PANEL_WIDTH = 200
TILE_SIZE = 24

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Pygame Level Editor")

font = pygame.font.SysFont("Arial", 18)
background_image = pygame.image.load("assets/background/background.png").convert()
background_image = pygame.transform.scale(background_image, (WINDOW_WIDTH, WINDOW_HEIGHT))
# Load assets
img_folder_path = 'assets/'


def load_scaled(path, size):
    return pygame.transform.scale(pygame.image.load(path), size)


assets = {}

for filename in os.listdir(img_folder_path):
    file_path = os.path.join(img_folder_path, filename)

    if filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
        name = os.path.splitext(filename)[0]
        path = os.path.join(img_folder_path, f"{name}{os.path.splitext(filename)[1]}")
        assets[name] = load_scaled(path, (TILE_SIZE, TILE_SIZE))

# Scale images for panel display
asset_panel_items = []
y_offset = 10
x_offset = 10
for name, img in assets.items():
    rect = pygame.Rect(x_offset, y_offset, TILE_SIZE, TILE_SIZE)
    asset_panel_items.append((name, img, rect))
    y_offset += 30
    if y_offset >= WINDOW_HEIGHT:
        x_offset += 30
        y_offset = 10

selected_asset = None
delete_mode = False
placed_tiles = []  # [{asset:'grass_block', x:5, y:3}, ...]
LEVEL_FILE = "level_data.json"  # Use a constant for file name


def draw_panel():
    pygame.draw.rect(screen, (50, 50, 50), (0, 0, PANEL_WIDTH, WINDOW_HEIGHT))
    for name, icon, rect in asset_panel_items:
        screen.blit(icon, rect.topleft)
        if selected_asset == name:
            pygame.draw.rect(screen, (255, 255, 0), rect, 2)

    delete_text = font.render("DELETE MODE: ON (D)" if delete_mode else "DELETE MODE: OFF (D)", True, (255, 255, 255))
    screen.blit(delete_text, (20, WINDOW_HEIGHT - 60))
    save_text = font.render("Press S to Save Level", True, (255, 255, 255))
    screen.blit(save_text, (20, WINDOW_HEIGHT - 40))


def draw_grid():
    for x in range(PANEL_WIDTH, WINDOW_WIDTH, TILE_SIZE):
        pygame.draw.line(screen, (80, 80, 80), (x, 0), (x, WINDOW_HEIGHT))
    for y in range(0, WINDOW_HEIGHT, TILE_SIZE):
        pygame.draw.line(screen, (80, 80, 80), (PANEL_WIDTH, y), (WINDOW_WIDTH, y))


def draw_tiles():
    for tile in placed_tiles:
        img = assets[tile['asset']]
        screen.blit(img, (PANEL_WIDTH + tile['x'] * TILE_SIZE, tile['y'] * TILE_SIZE))


def save_level():
    global placed_tiles

    # 1. Format the current level data
    new_level_data = [
        {'asset': tile['asset'], 'x': tile['x'], 'y': tile['y']}
        for tile in placed_tiles
    ]

    # 2. Read existing levels from the file
    all_levels = []
    if os.path.exists(LEVEL_FILE) and os.path.getsize(LEVEL_FILE) > 0:
        try:
            with open(LEVEL_FILE, "r") as f:
                # Expect the file to contain a list of levels
                all_levels = json.load(f)
        except json.JSONDecodeError:
            print("Warning: Existing level_data.json is corrupt or empty. Starting new list.")
            all_levels = []

    if not isinstance(all_levels, list):
        print("Warning: JSON data is not a list. Starting new list.")
        all_levels = []

    # 3. Append the new level data
    all_levels.append(new_level_data)

    # 4. Write the entire list back
    with open(LEVEL_FILE, "w") as f:
        json.dump(all_levels, f, indent=4)

    print(f"Level {len(all_levels)} saved successfully to {LEVEL_FILE}.")
    # Clear placed tiles so the user can immediately start designing the next level
    placed_tiles = []
    print("Canvas cleared for next level.")


running = True
while running:
    screen.blit(background_image, (PANEL_WIDTH, 0))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Mouse click
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos

            # Click inside asset panel
            if mx < PANEL_WIDTH:
                for name, icon, rect in asset_panel_items:
                    if rect.collidepoint(mx, my):
                        selected_asset = name
                continue

            # Click inside canvas
            grid_x = (mx - PANEL_WIDTH) // TILE_SIZE
            grid_y = my // TILE_SIZE

            # Right-click = delete
            if event.button == 3 or delete_mode:
                placed_tiles = [
                    t for t in placed_tiles
                    if not (t['x'] == grid_x and t['y'] == grid_y)
                ]
            else:
                # Check if a tile already exists here (prevent overlapping)
                exists = any(t['x'] == grid_x and t['y'] == grid_y for t in placed_tiles)

                # if selected_asset and not exists:
                if selected_asset:
                    placed_tiles.append({'asset': selected_asset, 'x': grid_x, 'y': grid_y})

        # Key press
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                save_level()
            if event.key == pygame.K_d:
                delete_mode = not delete_mode

    draw_panel()
    draw_grid()
    draw_tiles()

    pygame.display.update()

pygame.quit()
sys.exit()