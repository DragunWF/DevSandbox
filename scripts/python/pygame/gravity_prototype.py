import pygame
import math
import random

# --- CONFIGURATION (Zero Magic Numbers) ---
FPS = 60
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800
WORLD_WIDTH = 2000
WORLD_HEIGHT = 2000

# Colors
BG_COLOR = (15, 15, 25)
PLAYER_COLOR = (100, 200, 255)
ENEMY_COLOR = (220, 50, 50)
WALL_SPIKE_COLOR = (150, 150, 150)
PULL_WELL_COLOR = (150, 50, 200, 100) 
PUSH_WELL_COLOR = (200, 180, 50, 100) 

# Mechanics
PLAYER_ACCEL = 0.5
PLAYER_FRICTION = 0.85
PLAYER_RADIUS = 15

ENEMY_SPAWN_RATE = 45 
ENEMY_ACCEL = 0.25      # Increased base speed so they track better
ENEMY_FRICTION = 0.90
ENEMY_MAX_HP = 100
WALL_DAMAGE = 50

WELL_RADIUS = 250
WELL_FORCE = 1.2
WELL_LIFETIME = 90 

# --- CLASSES ---
class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0

    def update(self, keys):
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  self.vx -= PLAYER_ACCEL
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: self.vx += PLAYER_ACCEL
        if keys[pygame.K_w] or keys[pygame.K_UP]:    self.vy -= PLAYER_ACCEL
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:  self.vy += PLAYER_ACCEL

        self.vx *= PLAYER_FRICTION
        self.vy *= PLAYER_FRICTION
        
        self.x += self.vx
        self.y += self.vy

        # Clamp to world bounds
        self.x = max(PLAYER_RADIUS, min(self.x, WORLD_WIDTH - PLAYER_RADIUS))
        self.y = max(PLAYER_RADIUS, min(self.y, WORLD_HEIGHT - PLAYER_RADIUS))

class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.hp = ENEMY_MAX_HP
        self.radius = 12

    def update(self, player_x, player_y, wells):
        # 1. Base movement: Accelerate towards player
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.hypot(dx, dy)
        
        if dist > 0:
            self.vx += (dx / dist) * ENEMY_ACCEL
            self.vy += (dy / dist) * ENEMY_ACCEL

        # 2. Gravity Well forces
        for well in wells:
            wdx = well.x - self.x
            wdy = well.y - self.y
            wdist = math.hypot(wdx, wdy)
            
            if 0 < wdist < well.radius:
                force = WELL_FORCE * (1 - (wdist / well.radius))
                direction = 1 if well.is_pull else -1
                self.vx += (wdx / wdist) * force * direction
                self.vy += (wdy / wdist) * force * direction

        # 3. Apply friction and move
        self.vx *= ENEMY_FRICTION
        self.vy *= ENEMY_FRICTION
        self.x += self.vx
        self.y += self.vy

        # 4. Wall Collisions
        if self.x <= self.radius or self.x >= WORLD_WIDTH - self.radius:
            self.vx *= -1.5
            self.x = max(self.radius, min(self.x, WORLD_WIDTH - self.radius))
            self.hp -= WALL_DAMAGE
            
        if self.y <= self.radius or self.y >= WORLD_HEIGHT - self.radius:
            self.vy *= -1.5 
            self.y = max(self.radius, min(self.y, WORLD_HEIGHT - self.radius))
            self.hp -= WALL_DAMAGE

    def draw(self, surface, cam_x, cam_y):
        color = ENEMY_COLOR if self.hp > 50 else (150, 0, 0)
        draw_x = int(self.x - cam_x - self.radius)
        draw_y = int(self.y - cam_y - self.radius)
        pygame.draw.rect(surface, color, (draw_x, draw_y, self.radius*2, self.radius*2))

class GravityWell:
    def __init__(self, x, y, is_pull):
        self.x = x
        self.y = y
        self.is_pull = is_pull
        self.radius = WELL_RADIUS
        self.life = WELL_LIFETIME

    def update(self):
        self.life -= 1

    def draw(self, surface, cam_x, cam_y):
        alpha_surface = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        color = PULL_WELL_COLOR if self.is_pull else PUSH_WELL_COLOR
        
        alpha = int(255 * (self.life / WELL_LIFETIME))
        mod_color = (*color[:3], min(color[3], alpha))
        
        pygame.draw.circle(alpha_surface, mod_color, (self.radius, self.radius), self.radius)
        draw_x = int(self.x - cam_x - self.radius)
        draw_y = int(self.y - cam_y - self.radius)
        surface.blit(alpha_surface, (draw_x, draw_y))

def draw_parallax_background(surface, cam_x, cam_y):
    # Generates a pseudo-random starfield on the fly based on camera position using modulo
    # Near stars (move faster)
    for i in range(100):
        sx = (hash(str(i) + "x1") + cam_x * -0.5) % SCREEN_WIDTH
        sy = (hash(str(i) + "y1") + cam_y * -0.5) % SCREEN_HEIGHT
        pygame.draw.circle(surface, (100, 100, 120), (int(sx), int(sy)), 2)
        
    # Far stars (move slower)
    for i in range(150):
        sx = (hash(str(i) + "x2") + cam_x * -0.2) % SCREEN_WIDTH
        sy = (hash(str(i) + "y2") + cam_y * -0.2) % SCREEN_HEIGHT
        pygame.draw.circle(surface, (60, 60, 80), (int(sx), int(sy)), 1)

# --- ENGINE SETUP ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Prototype: Singularity (Movable)")
clock = pygame.time.Clock()

player = Player(WORLD_WIDTH // 2, WORLD_HEIGHT // 2)
enemies = []
wells = []
frames = 0
running = True

# --- GAME LOOP ---
while running:
    # 1. Input & Events
    keys = pygame.key.get_pressed()
    
    # Camera Logic (centered on player, clamped to world bounds)
    cam_x = max(0, min(player.x - SCREEN_WIDTH // 2, WORLD_WIDTH - SCREEN_WIDTH))
    cam_y = max(0, min(player.y - SCREEN_HEIGHT // 2, WORLD_HEIGHT - SCREEN_HEIGHT))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            # Convert screen space click to world space coordinates
            world_mouse_x = mouse_x + cam_x
            world_mouse_y = mouse_y + cam_y
            
            if event.button == 1:
                wells.append(GravityWell(world_mouse_x, world_mouse_y, is_pull=True))
            elif event.button == 3:
                wells.append(GravityWell(world_mouse_x, world_mouse_y, is_pull=False))

    # 2. Spawning Logic
    frames += 1
    if frames % ENEMY_SPAWN_RATE == 0:
        # Fix: Spawn slightly inside the world bounds to prevent instant wall-bounce trap
        padding = 20
        if random.choice([True, False]):
            ex = random.choice([padding, WORLD_WIDTH - padding])
            ey = random.randint(padding, WORLD_HEIGHT - padding)
        else:
            ex = random.randint(padding, WORLD_WIDTH - padding)
            ey = random.choice([padding, WORLD_HEIGHT - padding])
        enemies.append(Enemy(ex, ey))

    # 3. Updates
    player.update(keys)

    for well in wells[:]:
        well.update()
        if well.life <= 0:
            wells.remove(well)

    for enemy in enemies[:]:
        enemy.update(player.x, player.y, wells)
        if enemy.hp <= 0:
            enemies.remove(enemy)

    # 4. Drawing
    screen.fill(BG_COLOR)
    draw_parallax_background(screen, cam_x, cam_y)
    
    # Draw spiked walls boundary relative to camera
    wall_rect = pygame.Rect(-cam_x, -cam_y, WORLD_WIDTH, WORLD_HEIGHT)
    pygame.draw.rect(screen, WALL_SPIKE_COLOR, wall_rect, 5)

    for well in wells:
        well.draw(screen, cam_x, cam_y)

    for enemy in enemies:
        enemy.draw(screen, cam_x, cam_y)

    # Draw Player
    player_draw_x = int(player.x - cam_x)
    player_draw_y = int(player.y - cam_y)
    pygame.draw.circle(screen, PLAYER_COLOR, (player_draw_x, player_draw_y), PLAYER_RADIUS)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()