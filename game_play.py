import pygame
import json
import sys
import os
import math
import random

pygame.init()

# -----------------------
# CONFIG
# -----------------------
WINDOW_WIDTH = 790
WINDOW_HEIGHT = 600
TILE_SIZE = 24
FPS = 60

# Player config
PLAYER_SPEED = 4
JUMP_POWER = 12
GRAVITY = 0.7
MAX_FALL_SPEED = 12
PLAYER_MAX_HEALTH = 20
PLAYER_INVULN_FRAMES = 60 
PLAYER_SHOOT_COOLDOWN = 20
PLAYER_BULLET_SPEED = 8
PLAYER_BULLET_DAMAGE = 1
PLAYER_BULLET_COLOR = (255, 0, 0) 

# Enemy config
ENEMY_SPEED = 1.2
ENEMY_SHOOT_RANGE = 100
ENEMY_SHOOT_COOLDOWN = 90 
ENEMY_BULLET_SPEED = 6
ENEMY_DAMAGE = 1
PLAYER_TOUCH_DAMAGE = 1
ENEMY_MAX_HEALTH = 3 
BULLET_SIZE = 6

# ... (existing globals like player_invuln, etc.)

# --- NEW LEVEL MANAGEMENT VARIABLES ---
LEVEL_FILE = "level_data.json"
ALL_LEVELS = [] # List to hold all level data from JSON
CURRENT_LEVEL_INDEX = 0

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Platformer with Enemies & Health")
clock = pygame.time.Clock()

# bg_path = "assets/background/background.png"
bg_path = "assets/background/BG.png"
if os.path.exists(bg_path):
    background_image = pygame.image.load(bg_path).convert()
    background_image = pygame.transform.scale(background_image, (WINDOW_WIDTH, WINDOW_HEIGHT))
else:
    background_image = None

# Load images from assets folder and scale to tile size
img_folder_path = "assets/"


def load_scaled(path, size):
    return pygame.transform.scale(pygame.image.load(path).convert_alpha(), size)


assets = {}
if os.path.isdir(img_folder_path):
    for filename in os.listdir(img_folder_path):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            name = os.path.splitext(filename)[0]
            try:
                assets[name] = load_scaled(os.path.join(img_folder_path, filename), (TILE_SIZE, TILE_SIZE))
            except Exception as e:
                print("Failed to load", filename, e)



class Enemy:
    def __init__(self, x, y, image=None):
        # x,y are in pixels (tile coords * TILE_SIZE)
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.image = image
        self.dir = -1 if random.random() < 0.5 else 1  # start left or right
        self.speed = ENEMY_SPEED
        self.shoot_cd = random.randint(0, ENEMY_SHOOT_COOLDOWN)  # start with random cooldown
        self.alive = True
        # --- NEW ENEMY ATTRIBUTES ---
        self.health = ENEMY_MAX_HEALTH
        self.max_health = ENEMY_MAX_HEALTH

    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.alive = False

    def update_patrol(self, tiles):
        # Horizontal movement and reversing on wall collision or edge of platform
        self.rect.x += int(self.dir * self.speed)

        collided = False
        for tile_rect, _ in tiles:
            if self.rect.colliderect(tile_rect):
                collided = True
                # roll back
                if self.dir > 0:
                    self.rect.right = tile_rect.left
                else:
                    self.rect.left = tile_rect.right
                self.dir *= -1
                break

        if not collided:
            # check for edge: look slightly ahead at feet
            ahead_x = self.rect.centerx + self.dir * (self.rect.width // 2 + 1)
            foot_check_rect = pygame.Rect(ahead_x, self.rect.bottom + 1, 2, 2)
            supported = False
            for tile_rect, _ in tiles:
                if foot_check_rect.colliderect(tile_rect):
                    supported = True
                    break
            if not supported:
                # reverse to avoid falling off platform
                self.dir *= -1

    def try_shoot(self, player_center, bullets):
        # cooldown
        if self.shoot_cd > 0:
            self.shoot_cd -= 1
            return

        # shoot if player is within horizontal range
        dist = abs(player_center[0] - self.rect.centerx)
        # print(dist)
        if dist <= ENEMY_SHOOT_RANGE:
            # fire bullet toward player
            dx = player_center[0] - self.rect.centerx
            dy = player_center[1] - self.rect.centery
            angle = math.atan2(dy, dx)
            vx = math.cos(angle) * ENEMY_BULLET_SPEED
            vy = math.sin(angle) * ENEMY_BULLET_SPEED

            bullets.append({
                "x": self.rect.centerx,
                "y": self.rect.centery,
                "vx": vx,
                "vy": vy,
                "rect": pygame.Rect(self.rect.centerx, self.rect.centery, BULLET_SIZE, BULLET_SIZE),
                "owner": "enemy"
            })
            self.shoot_cd = ENEMY_SHOOT_COOLDOWN

    def draw(self, surf):
        if self.image:
            surf.blit(self.image, self.rect)
        else:
            pygame.draw.rect(surf, (200, 0, 0), self.rect)

        # Draw health bar above enemy head
        if self.health < self.max_health:
            bar_w = TILE_SIZE + 4
            bar_h = 4
            bar_x = self.rect.x - 2
            bar_y = self.rect.y - 8

            # Draw background and border
            pygame.draw.rect(surf, (0, 0, 0), (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2))
            pygame.draw.rect(surf, (100, 100, 100), (bar_x, bar_y, bar_w, bar_h))

            # Draw health fill
            fill_w = int((self.health / self.max_health) * bar_w)
            pygame.draw.rect(surf, (0, 255, 0), (bar_x, bar_y, fill_w, bar_h))


# -----------------------
# LEVEL LOADING (MODIFIED)
# -----------------------

def load_all_levels():
    global ALL_LEVELS
    if not os.path.exists(LEVEL_FILE) or os.path.getsize(LEVEL_FILE) == 0:
        print("Level file not found or empty:", LEVEL_FILE)
        return False
    try:
        with open(LEVEL_FILE, "r") as f:
            ALL_LEVELS = json.load(f)
            if not isinstance(ALL_LEVELS, list) or not ALL_LEVELS:
                print("Error: Level data is not a list or is empty.")
                ALL_LEVELS = []
                return False
            print(f"Loaded {len(ALL_LEVELS)} levels.")
            return True
    except json.JSONDecodeError:
        print("Error: Could not decode level_data.json.")
        return False


def load_current_level():
    global CURRENT_LEVEL_INDEX
    if not ALL_LEVELS:
        print("No levels loaded. Cannot start game.")
        return [], []

    if CURRENT_LEVEL_INDEX >= len(ALL_LEVELS):
        print("Game finished! All levels completed.")
        return [], []

    print(f"Loading Level {CURRENT_LEVEL_INDEX + 1}...")
    level_data = ALL_LEVELS[CURRENT_LEVEL_INDEX]

    tiles = []
    enemies = []

    for t in level_data:
        asset_name = t.get("asset")
        tx = t.get("x", 0)
        ty = t.get("y", 0)
        px = int(tx * TILE_SIZE)
        py = int(ty * TILE_SIZE)

        if asset_name == "enemy":
            img = assets.get("enemy")
            enemies.append(Enemy(px, py, image=img))
        else:
            img = assets.get(asset_name)
            rect = pygame.Rect(px, py, TILE_SIZE, TILE_SIZE)
            tiles.append((rect, img))

    return tiles, enemies


# Initial load of all level data
load_all_levels()
tiles, enemies = load_current_level()
# ... (rest of your initialization)

bullets = []  # list of dicts {x,y,vx,vy,rect,owner}

player = pygame.Rect(200, 100, TILE_SIZE, TILE_SIZE)
player_color = (100, 200, 10)

# movement
moving_l = moving_r = False
jump_pressed = False
shoot_pressed = False  # NEW: Shoot input
on_ground = False
vel_y = 0.0
player_shoot_cd = 0  # NEW: Player shoot cooldown
player_direction = 1  # NEW: 1 for right, -1 for left (default right)

# player health
player_health = PLAYER_MAX_HEALTH
player_invuln = 0  # frames remaining invulnerability


def rects_collide(rect, rect_list):
    for r in rect_list:
        if rect.colliderect(r):
            return True
    return False


def handle_collision(rect, tiles, dx, dy):
    # Move horizontally
    rect.x += int(dx)
    for tile_rect, _ in tiles:
        if rect.colliderect(tile_rect):
            if dx > 0:
                rect.right = tile_rect.left
            elif dx < 0:
                rect.left = tile_rect.right

    # Move vertically
    rect.y += int(dy)
    hit_ground = False
    for tile_rect, _ in tiles:
        if rect.colliderect(tile_rect):
            if dy > 0:
                rect.bottom = tile_rect.top
                hit_ground = True
            elif dy < 0:
                rect.top = tile_rect.bottom

    return rect, hit_ground


def draw_health_bar(surf, x, y, w, h, current, maximum):
    # Border
    pygame.draw.rect(surf, (0, 0, 0), (x - 2, y - 2, w + 4, h + 4))
    # background
    pygame.draw.rect(surf, (100, 100, 100), (x, y, w, h))
    # filled
    fill_w = int((current / maximum) * w)
    pygame.draw.rect(surf, (200, 30, 30), (x, y, fill_w, h))


# -----------------------
# MAIN LOOP
# -----------------------
running = True
while running:
    dt = clock.tick(FPS) / 16

    # Decrease player shoot cooldown
    if player_shoot_cd > 0:
        player_shoot_cd -= 1

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Input
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                moving_l = True
            if event.key == pygame.K_RIGHT:
                moving_r = True
            if event.key == pygame.K_UP:
                jump_pressed = True
            if event.key == pygame.K_SPACE:
                shoot_pressed = True

            if event.key == pygame.K_r:
                # reload level and reset
                tiles, enemies = load_current_level()
                bullets.clear()
                player.x, player.y = 200, 100
                vel_y = 0
                player_health = PLAYER_MAX_HEALTH
                player_invuln = 0
                player_shoot_cd = 0
                player_direction = 1  # reset direction

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                moving_l = False
            if event.key == pygame.K_RIGHT:
                moving_r = False
            if event.key == pygame.K_UP:
                jump_pressed = False
            if event.key == pygame.K_SPACE:
                shoot_pressed = False

    # Draw background
    if background_image:
        screen.blit(background_image, (0, 0))
    else:
        screen.fill((120, 180, 255))

    # --- UPDATE PLAYER DIRECTION BASED ON MOVEMENT ---
    if moving_r and not moving_l:
        player_direction = 1
    elif moving_l and not moving_r:
        player_direction = -1
    # Note: If moving both directions or neither, player_direction remains the last direction faced.

    # --- PLAYER SHOOTING LOGIC ---
    if shoot_pressed and player_shoot_cd == 0:
        # Use player_direction for shooting
        shoot_vx = PLAYER_BULLET_SPEED * player_direction

        bullets.append({
            "x": player.centerx,
            "y": player.centery,
            "vx": shoot_vx,
            "vy": 0,
            "rect": pygame.Rect(player.centerx, player.centery, BULLET_SIZE, BULLET_SIZE),
            "owner": "player",
            "damage": PLAYER_BULLET_DAMAGE
        })
        player_shoot_cd = PLAYER_SHOOT_COOLDOWN

    # Player input -> movement
    dx = 0
    if moving_l:
        dx -= PLAYER_SPEED * dt
    if moving_r:
        dx += PLAYER_SPEED * dt

    # Jumping
    if jump_pressed and on_ground:
        vel_y = -JUMP_POWER
        on_ground = False

    # Gravity
    vel_y += GRAVITY
    if vel_y > MAX_FALL_SPEED:
        vel_y = MAX_FALL_SPEED
    dy = vel_y * dt

    # Apply collisions
    player, landed = handle_collision(player, tiles, dx, dy)
    if landed:
        vel_y = 0
        on_ground = True
    else:
        on_ground = False

    # --- SCREEN BOUNDARY CHECK ---
    # Horizontal boundary check
    if player.left < 0:
        player.left = 0
    if player.right > WINDOW_WIDTH:
        player.right = WINDOW_WIDTH

    # Vertical boundary check
    if player.bottom > WINDOW_HEIGHT:
        player.bottom = WINDOW_HEIGHT
        vel_y = 0
        on_ground = True
    if player.top < 0:
        player.top = 0
        vel_y = 0
        # --- END OF SCREEN BOUNDARY CHECK ---

    # -----------------------
    # UPDATE ENEMIES
    # -----------------------
    for enemy in enemies:
        if not enemy.alive:
            continue

        # simple gravity for enemy (so they stay on platforms)
        enemy.rect.y += 1  # small nudge to detect ground below
        on_ground_enemy = False
        for tile_rect, _ in tiles:
            if enemy.rect.colliderect(tile_rect):
                # if overlapping after nudge, revert and mark on ground
                enemy.rect.bottom = tile_rect.top
                on_ground_enemy = True
                break
        if not on_ground_enemy:
            enemy.rect.y -= 1  # revert if not on ground

        enemy.update_patrol(tiles)

        # shooting
        enemy.try_shoot(player.center, bullets)

    for b in bullets:
        b['x'] += b['vx']
        b['y'] += b['vy']
        b['rect'].x = int(b['x'])
        b['rect'].y = int(b['y'])

    # Bullet collisions with tiles & entities
    bullets_to_remove = []
    enemies_to_remove = []  # NEW: for enemies that die this frame

    for i, b in enumerate(bullets):
        # remove if out of screen
        if b['x'] < -50 or b['x'] > WINDOW_WIDTH + 50 or b['y'] < -50 or b['y'] > WINDOW_HEIGHT + 50:
            bullets_to_remove.append(i)
            continue

        # tile collisions
        for tile_rect, _ in tiles:
            if b['rect'].colliderect(tile_rect):
                bullets_to_remove.append(i)
                break

        # skip remaining checks if already marked for removal by tile collision
        if i in bullets_to_remove:
            continue

        # entity collisions (Player or Enemy)
        if b['owner'] == 'enemy':
            if player.colliderect(b['rect']):
                # damage player if not invulnerable
                if player_invuln == 0:
                    player_health -= ENEMY_DAMAGE
                    player_invuln = PLAYER_INVULN_FRAMES
                    # small knockback
                    if b['vx'] > 0:
                        player.x += 6
                    else:
                        player.x -= 6
                bullets_to_remove.append(i)

        # Player bullet hits enemy
        elif b['owner'] == 'player':
            for j, enemy in enumerate(enemies):
                if enemy.alive and enemy.rect.colliderect(b['rect']):
                    enemy.take_damage(b['damage'])
                    bullets_to_remove.append(i)
                    if not enemy.alive:
                        enemies_to_remove.append(j)
                    break

    # Clean bullets in reverse order
    for idx in sorted(set(bullets_to_remove), reverse=True):
        if 0 <= idx < len(bullets):
            bullets.pop(idx)

    # Clean up dead enemies (in reverse order to avoid index issues)
    for idx in sorted(set(enemies_to_remove), reverse=True):
        if 0 <= idx < len(enemies):
            enemies.pop(idx)

    # ... (after updating and cleaning up enemies/bullets)

    # -----------------------
    # LEVEL PROGRESSION CHECK
    # -----------------------
    if len(enemies) == 0 and ALL_LEVELS:
        if CURRENT_LEVEL_INDEX + 1 < len(ALL_LEVELS):
            # Move to the next level
            CURRENT_LEVEL_INDEX += 1
            bullets.clear()

            # Reset player to starting position (assuming a default start)
            player.x, player.y = 200, 100
            player_health = PLAYER_MAX_HEALTH
            vel_y = 0

            tiles, enemies = load_current_level()
            print(f"Moving to Level {CURRENT_LEVEL_INDEX + 1}!")

        elif CURRENT_LEVEL_INDEX + 1 == len(ALL_LEVELS):
            # All levels completed!
            fontbig = pygame.font.SysFont("Arial", 48)
            t = fontbig.render("GAME COMPLETE!", True, (0, 255, 0))
            screen.blit(t, (WINDOW_WIDTH // 2 - t.get_width() // 2, WINDOW_HEIGHT // 2 - t.get_height() // 2))

            # Freeze the screen on "Game Complete"
            pygame.display.update()
            pygame.time.wait(3000)  # wait 3 seconds
            running = False  # Or prompt user to restart
            continue

    # ... (continue with DRAW TILES, ENEMIES, etc.)
    # -----------------------
    # PLAYER ↔ ENEMY TOUCH DAMAGE
    # -----------------------
    for enemy in enemies:
        if not enemy.alive:
            continue
        if player.colliderect(enemy.rect):
            if player_invuln == 0:
                player_health -= PLAYER_TOUCH_DAMAGE
                player_invuln = PLAYER_INVULN_FRAMES
                # small knockback away from enemy
                if player.centerx >= enemy.rect.centerx:
                    player.x += 12
                else:
                    player.x -= 12

    # Decrease invulnerability timer
    if player_invuln > 0:
        player_invuln -= 1

    # -----------------------
    # DRAW TILES, ENEMIES, BULLETS, PLAYER, HUD
    # -----------------------
    # Draw tiles
    for rect, img in tiles:
        if img:
            screen.blit(img, rect)
        else:
            pygame.draw.rect(screen, (100, 100, 100), rect)

    # Draw enemies
    for enemy in enemies:
        if enemy.alive:
            enemy.draw(screen)

    # Draw bullets
    for b in bullets:
        color = (255, 200, 30) if b['owner'] == 'enemy' else PLAYER_BULLET_COLOR  # Use the config color
        pygame.draw.rect(screen, color, b['rect'])

    # Draw player (flash while invuln)
    if player_invuln > 0 and (player_invuln // 6) % 2 == 0:
        # skip draw (flash)
        pass
    else:
        # Draw player rectangle
        pygame.draw.rect(screen, player_color, player)

        # NEW: Draw the "eye" dot to show direction
        # Calculate eye position based on player_direction
        eye_offset_x = player.width // 4 * player_direction
        eye_center_x = player.centerx + eye_offset_x
        eye_center_y = player.centery - player.height // 4

        # Draw the eye (small black circle)
        pygame.draw.circle(screen, (0, 0, 0), (eye_center_x, eye_center_y), 2)

    # Draw HUD: health
    draw_health_bar(screen, 10, 10, 120, 16, player_health, PLAYER_MAX_HEALTH)
    # health text
    font = pygame.font.SysFont("Arial", 14)
    text = font.render(f"HP: {player_health}/{PLAYER_MAX_HEALTH}  (R to reset)", True, (255, 255, 255))
    screen.blit(text, (10, 30))

    # Check for death
    if player_health <= 0:
        fontbig = pygame.font.SysFont("Arial", 36)
        t = fontbig.render("YOU DIED - Press R to Restart", True, (255, 10, 10))
        screen.blit(t, (WINDOW_WIDTH // 2 - t.get_width() // 2, WINDOW_HEIGHT // 2 - t.get_height() // 2))
        # Freeze game updates except for restart input; continue loop so R works.
        pygame.display.update()
        # consume events until R
        waiting = True
        while waiting:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    waiting = False
                    running = False
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_r:
                    waiting = False
                    # reset state
                    tiles, enemies = load_current_level()
                    bullets.clear()
                    player.x, player.y = 200, 100
                    vel_y = 0
                    player_health = PLAYER_MAX_HEALTH
                    player_invuln = 0
                    moving_l = moving_r = False
                    player_shoot_cd = 0
                    player_direction = 1  # reset direction
            clock.tick(15)
        continue

    pygame.display.update()

pygame.quit()
sys.exit()