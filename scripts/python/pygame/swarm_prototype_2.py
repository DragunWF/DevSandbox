import pygame
import random
import math
import time

# --- Configuration & Constants ---
WIDTH, HEIGHT = 1000, 700
FPS = 60

# Colors
BG_COLOR = (25, 25, 30)         
BOID_COLOR = (100, 150, 255)    
RESOURCE_COLOR = (50, 255, 100) 
GRUNT_COLOR = (150, 150, 150)   
BOOMER_COLOR = (255, 150, 50)   
LASER_COLOR = (255, 50, 50)     
TEXT_COLOR = (255, 255, 255)
UI_BG_COLOR = (0, 0, 0, 150)

# Boid / Swarm Settings
START_BOIDS = 100
MAX_SPEED = 4.5
MAX_FORCE = 0.2
PERCEPTION_RADIUS = 50          
PERCEPTION_SQ = PERCEPTION_RADIUS ** 2 

# Spatial Partitioning (Grid size for optimization)
GRID_SIZE = 50 

# Base Behavior Weights
W_ALIGNMENT = 1.0
W_COHESION = 1.0
W_SEPARATION = 1.8
W_MOUSE = 1.0

# "Dense" State Weights (Left Click)
W_DENSE_COHESION = 7.0          
W_DENSE_MOUSE = 5.0             
W_DENSE_SEPARATION = 0.4        

# "Scatter" State Weights (Right Click)
W_SCATTER_MOUSE = -6.0          
SCATTER_DURATION = 0.3          
SCATTER_COOLDOWN = 3.0          

class SpatialHash:
    """Optimizes distance checks by grouping entities into grid cells."""
    def __init__(self, cell_size):
        self.cell_size = cell_size
        self.grid = {}

    def clear(self):
        self.grid = {}

    def insert(self, boid):
        cell = (int(boid.pos.x // self.cell_size), int(boid.pos.y // self.cell_size))
        if cell not in self.grid:
            self.grid[cell] = []
        self.grid[cell].append(boid)

    def get_neighbors(self, boid):
        cell_x, cell_y = int(boid.pos.x // self.cell_size), int(boid.pos.y // self.cell_size)
        neighbors = []
        # Check the 9 surrounding cells
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                cell = (cell_x + dx, cell_y + dy)
                if cell in self.grid:
                    neighbors.extend(self.grid[cell])
        return neighbors

class Particle:
    def __init__(self, pos, color, speed_mult=1.0):
        self.pos = pygame.math.Vector2(pos)
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(1.0, 4.0) * speed_mult
        self.vel = pygame.math.Vector2(math.cos(angle), math.sin(angle)) * speed
        self.color = color
        self.life = 255
        self.decay = random.uniform(8, 15)
        self.size = random.uniform(2, 5)

    def update(self):
        self.pos += self.vel
        self.life -= self.decay

    def draw(self, surface):
        if self.life > 0:
            # Shrink particle as it dies to simulate fading without expensive alpha blending
            current_size = max(0.1, self.size * (self.life / 255.0))
            pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), int(current_size))

def spawn_particles(pos, color, count, particle_list, speed_mult=1.0):
    for _ in range(count):
        particle_list.append(Particle(pos, color, speed_mult))

class Boid:
    def __init__(self, x, y):
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
        if self.vel.length_squared() > 0:
            self.vel.scale_to_length(MAX_SPEED)
        self.acc = pygame.math.Vector2(0, 0)
        self.size = 6

    def steer(self, desired):
        """Calculates steering force required to reach desired velocity."""
        if desired.length_squared() > 0:
            desired.scale_to_length(MAX_SPEED)
            steer_force = desired - self.vel
            if steer_force.length_squared() > MAX_FORCE ** 2:
                steer_force.scale_to_length(MAX_FORCE)
            return steer_force
        return pygame.math.Vector2(0, 0)

    def apply_behaviors(self, neighbors, mouse_pos, is_dense, is_scatter):
        """Calculates Boids AI rules: Cohesion, Alignment, Separation, Target Attraction."""
        alignment = pygame.math.Vector2(0, 0)
        cohesion = pygame.math.Vector2(0, 0)
        separation = pygame.math.Vector2(0, 0)
        total = 0

        # Iterate through local neighbors for Boid Rules
        for other in neighbors:
            if other is not self:
                dist_sq = self.pos.distance_squared_to(other.pos)
                if dist_sq < PERCEPTION_SQ:
                    alignment += other.vel
                    cohesion += other.pos
                    # Separation: Steer away, weighted inversely by distance
                    diff = self.pos - other.pos
                    if dist_sq > 0:
                        diff /= (dist_sq ** 0.5) 
                    separation += diff
                    total += 1

        if total > 0:
            alignment = self.steer(alignment / total)
            cohesion = self.steer((cohesion / total) - self.pos)
            separation = self.steer(separation / total)
        else:
            alignment = cohesion = separation = pygame.math.Vector2(0, 0)

        # Target (Cursor) Attraction
        mouse_steer = self.steer(mouse_pos - self.pos)

        # Apply state toggles
        if is_scatter:
            # Reverses mouse pull to create a violent scatter effect
            self.acc += separation * W_SEPARATION * 2.0
            self.acc += mouse_steer * W_SCATTER_MOUSE
        elif is_dense:
            # Pulls swarm tightly together and sharply towards mouse
            self.acc += alignment * W_ALIGNMENT
            self.acc += cohesion * W_DENSE_COHESION
            self.acc += separation * W_DENSE_SEPARATION
            self.acc += mouse_steer * W_DENSE_MOUSE
        else:
            # Fluid / Standard behavior
            self.acc += alignment * W_ALIGNMENT
            self.acc += cohesion * W_COHESION
            self.acc += separation * W_SEPARATION
            self.acc += mouse_steer * W_MOUSE

    def update(self, is_scatter):
        self.vel += self.acc
        current_max = MAX_SPEED * 1.5 if is_scatter else MAX_SPEED
        if self.vel.length_squared() > current_max ** 2:
            self.vel.scale_to_length(current_max)
        
        self.pos += self.vel
        self.acc *= 0 

        # Screen Wrap
        self.pos.x = self.pos.x % WIDTH
        self.pos.y = self.pos.y % HEIGHT

    def draw(self, surface):
        angle = math.atan2(self.vel.y, self.vel.x)
        p1 = self.pos + pygame.math.Vector2(math.cos(angle), math.sin(angle)) * self.size * 1.5
        p2 = self.pos + pygame.math.Vector2(math.cos(angle + 2.5), math.sin(angle + 2.5)) * self.size
        p3 = self.pos + pygame.math.Vector2(math.cos(angle - 2.5), math.sin(angle - 2.5)) * self.size
        pygame.draw.polygon(surface, BOID_COLOR, [p1, p2, p3])

# --- Game Entities ---
class Resource:
    def __init__(self):
        self.pos = pygame.math.Vector2(random.randint(50, WIDTH-50), random.randint(50, HEIGHT-50))
        self.radius = 10
        self.reward = random.randint(5, 10)

    def draw(self, surface):
        pygame.draw.circle(surface, RESOURCE_COLOR, (int(self.pos.x), int(self.pos.y)), self.radius)

class Grunt:
    def __init__(self, target_pos):
        self.pos = self._spawn_edge()
        self.speed = random.uniform(1.5, 2.5)
        self.size = 12

    def _spawn_edge(self):
        if random.random() < 0.5:
            return pygame.math.Vector2(random.choice([-20, WIDTH + 20]), random.randint(0, HEIGHT))
        return pygame.math.Vector2(random.randint(0, WIDTH), random.choice([-20, HEIGHT + 20]))

    def update(self, mouse_pos):
        # Grunts simply track the mouse (commander)
        dir = mouse_pos - self.pos
        if dir.length_squared() > 0:
            dir.normalize_ip()
        self.pos += dir * self.speed

    def draw(self, surface):
        rect = pygame.Rect(self.pos.x - self.size//2, self.pos.y - self.size//2, self.size, self.size)
        pygame.draw.rect(surface, GRUNT_COLOR, rect)

class Boomer:
    def __init__(self):
        self.pos = pygame.math.Vector2(random.choice([-20, WIDTH + 20]), random.randint(0, HEIGHT))
        self.speed = 1.0
        self.radius = 14
        self.blast_radius = 100

    def update(self, mouse_pos):
        dir = mouse_pos - self.pos
        if dir.length_squared() > 0:
            dir.normalize_ip()
        self.pos += dir * self.speed

    def draw(self, surface):
        pygame.draw.circle(surface, BOOMER_COLOR, (int(self.pos.x), int(self.pos.y)), self.radius)
        # Draw danger zone
        pygame.draw.circle(surface, BOOMER_COLOR, (int(self.pos.x), int(self.pos.y)), self.blast_radius, 1)

class Explosion:
    def __init__(self, pos, radius):
        self.pos = pos
        self.max_radius = radius
        self.radius = 5
        self.life = 15
        self.max_life = 15

    def update(self):
        self.radius += (self.max_radius - self.radius) * 0.2
        self.life -= 1

    def draw(self, surface):
        alpha = int(255 * (self.life / self.max_life))
        color = (*BOOMER_COLOR, alpha)
        surf = pygame.Surface((self.max_radius*2, self.max_radius*2), pygame.SRCALPHA)
        pygame.draw.circle(surf, color, (self.max_radius, self.max_radius), int(self.radius))
        surface.blit(surf, (self.pos.x - self.max_radius, self.pos.y - self.max_radius))

class LaserDrone:
    def __init__(self):
        self.pos = pygame.math.Vector2(random.randint(50, WIDTH-50), random.choice([-20, HEIGHT + 20]))
        self.state = "AIMING" # AIMING -> FIRING
        self.timer = 120 # 2 seconds to aim
        self.target = pygame.math.Vector2(0, 0)
        self.line_end = pygame.math.Vector2(0, 0)
        self.radius = 16

    def update(self, mouse_pos):
        if self.state == "AIMING":
            self.target = pygame.math.Vector2(mouse_pos)
            self.timer -= 1
            if self.timer <= 0:
                self.state = "FIRING"
                self.timer = 30 # Fire duration
        elif self.state == "FIRING":
            self.timer -= 1
            if self.timer <= 0:
                self.state = "DONE"

        # Calculate laser line
        dir = self.target - self.pos
        if dir.length_squared() > 0:
            dir.normalize_ip()
        self.line_end = self.pos + dir * 1500

    def draw(self, surface):
        pygame.draw.circle(surface, LASER_COLOR, (int(self.pos.x), int(self.pos.y)), self.radius)
        if self.state == "AIMING":
            pygame.draw.line(surface, LASER_COLOR, self.pos, self.line_end, 1)
        elif self.state == "FIRING":
            pygame.draw.line(surface, LASER_COLOR, self.pos, self.line_end, 20)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Fluid Swarm Commander: Survival")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 28)
    large_font = pygame.font.SysFont(None, 64)

    # Initialize State
    boids = [Boid(WIDTH//2 + random.randint(-50,50), HEIGHT//2 + random.randint(-50,50)) for _ in range(START_BOIDS)]
    spatial_hash = SpatialHash(GRID_SIZE)
    
    resources = []
    enemies = []
    explosions = []
    particles = []
    
    start_time = time.time()
    last_scatter_time = -SCATTER_COOLDOWN

    resource_timer = 0
    enemy_timer = 0
    game_over = False
    survival_time = 0

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and game_over:
                if event.key == pygame.K_r:
                    # Restart
                    main()
                    return

        if game_over:
            screen.fill(BG_COLOR)
            go_text = large_font.render(f"GAME OVER", True, LASER_COLOR)
            time_text = font.render(f"Survived for: {int(survival_time)} seconds", True, TEXT_COLOR)
            restart_text = font.render("Press 'R' to Restart", True, TEXT_COLOR)
            screen.blit(go_text, (WIDTH//2 - go_text.get_width()//2, HEIGHT//2 - 50))
            screen.blit(time_text, (WIDTH//2 - time_text.get_width()//2, HEIGHT//2 + 20))
            screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT//2 + 60))
            pygame.display.flip()
            continue

        survival_time = time.time() - start_time
        mouse_x, mouse_y = pygame.mouse.get_pos()
        mouse_pos = pygame.math.Vector2(mouse_x, mouse_y)

        # Input State Toggles
        mouse_btns = pygame.mouse.get_pressed()
        is_dense = mouse_btns[0]
        is_scatter = False
        
        # Scatter Mechanics
        current_time = time.time()
        if mouse_btns[2] and current_time - last_scatter_time >= SCATTER_COOLDOWN:
            last_scatter_time = current_time
        
        if current_time - last_scatter_time < SCATTER_DURATION:
            is_scatter = True

        # --- Difficulty Scaling ---
        res_spawn_rate = max(180, int(300 - survival_time * 2)) 
        enemy_spawn_rate = max(15, int(60 - survival_time))

        resource_timer += 1
        if resource_timer > res_spawn_rate:
            resources.append(Resource())
            resource_timer = 0

        enemy_timer += 1
        if enemy_timer > enemy_spawn_rate:
            rand_val = random.random()
            if rand_val < 0.60:
                enemies.append(Grunt(mouse_pos))
            elif rand_val < 0.85:
                enemies.append(Boomer())
            else:
                enemies.append(LaserDrone())
            enemy_timer = 0

        # --- Updates & Spatial Partitioning ---
        spatial_hash.clear()
        for b in boids:
            spatial_hash.insert(b)

        for b in boids:
            neighbors = spatial_hash.get_neighbors(b)
            b.apply_behaviors(neighbors, mouse_pos, is_dense, is_scatter)
            b.update(is_scatter)

        # Update Enemies, Explosions, Particles
        for e in explosions:
            e.update()
        explosions = [e for e in explosions if e.life > 0]

        for p in particles:
            p.update()
        particles = [p for p in particles if p.life > 0]

        for e in enemies:
            e.update(mouse_pos)

        # --- Collision Logic ---
        boids_to_remove = set()
        enemies_to_remove = set()
        resources_to_remove = set()

        # 1. Boids vs Resources
        for r in resources:
            for b in boids:
                if b.pos.distance_squared_to(r.pos) < r.radius ** 2:
                    resources_to_remove.add(r)
                    for _ in range(r.reward):
                        boids.append(Boid(b.pos.x + random.uniform(-10, 10), b.pos.y + random.uniform(-10, 10)))
                    break 

        # 2. Boids vs Enemies
        for e in enemies:
            if type(e) == Grunt:
                for b in boids:
                    if b not in boids_to_remove:
                        if abs(b.pos.x - e.pos.x) < e.size and abs(b.pos.y - e.pos.y) < e.size:
                            boids_to_remove.add(b)
                            enemies_to_remove.add(e)
                            # Particle effects for popping
                            spawn_particles(b.pos, BOID_COLOR, 6, particles)
                            spawn_particles(e.pos, GRUNT_COLOR, 10, particles)
                            break 
            
            elif type(e) == Boomer:
                for b in boids:
                    if b.pos.distance_squared_to(e.pos) < e.radius ** 2:
                        enemies_to_remove.add(e)
                        explosions.append(Explosion(e.pos, e.blast_radius))
                        # Boomer popping effect
                        spawn_particles(e.pos, BOOMER_COLOR, 20, particles, speed_mult=1.5)
                        break 

            elif type(e) == LaserDrone:
                if e.state == "FIRING":
                    line_vec = e.line_end - e.pos
                    line_len = line_vec.length()
                    if line_len > 0:
                        unit_line = line_vec / line_len
                        for b in boids:
                            b_vec = b.pos - e.pos
                            proj = b_vec.dot(unit_line)
                            if 0 < proj < line_len:
                                closest_point = e.pos + unit_line * proj
                                if b.pos.distance_squared_to(closest_point) < 10**2: 
                                    if b not in boids_to_remove:
                                        boids_to_remove.add(b)
                                        spawn_particles(b.pos, BOID_COLOR, 6, particles, speed_mult=1.5)
                elif e.state == "DONE":
                    enemies_to_remove.add(e)
                    spawn_particles(e.pos, LASER_COLOR, 15, particles)

        # 3. Boids vs Explosions
        for ex in explosions:
            for b in boids:
                if b.pos.distance_squared_to(ex.pos) < ex.radius ** 2:
                    if b not in boids_to_remove:
                        boids_to_remove.add(b)
                        spawn_particles(b.pos, BOID_COLOR, 5, particles)

        # Apply Removals
        boids = [b for b in boids if b not in boids_to_remove]
        enemies = [e for e in enemies if e not in enemies_to_remove]
        resources = [r for r in resources if r not in resources_to_remove]

        if len(boids) <= 0:
            game_over = True

        # --- Rendering ---
        screen.fill(BG_COLOR)

        for p in particles:
            p.draw(screen)

        for r in resources:
            r.draw(screen)
        
        for e in enemies:
            if type(e) != LaserDrone: 
                e.draw(screen)
        
        for e in enemies:
            if type(e) == LaserDrone:
                e.draw(screen)

        for b in boids:
            b.draw(screen)

        for ex in explosions:
            ex.draw(screen)

        # UI
        health_text = font.render(f"Swarm Count: {len(boids)}", True, TEXT_COLOR)
        time_text = font.render(f"Time: {int(survival_time)}s", True, TEXT_COLOR)
        fps_text = font.render(f"FPS: {int(clock.get_fps())}", True, TEXT_COLOR)
        
        cd_ratio = min(1.0, (current_time - last_scatter_time) / SCATTER_COOLDOWN)
        cd_color = RESOURCE_COLOR if cd_ratio >= 1.0 else LASER_COLOR
        scatter_text = font.render(f"Scatter: {'READY' if cd_ratio >= 1.0 else 'CD'}", True, cd_color)

        pygame.draw.rect(screen, UI_BG_COLOR, (5, 5, 200, 120))
        screen.blit(health_text, (15, 15))
        screen.blit(time_text, (15, 40))
        screen.blit(scatter_text, (15, 65))
        screen.blit(fps_text, (15, 90))

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()