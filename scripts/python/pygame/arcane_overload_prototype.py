import pygame
import random
import sys

# --- Configuration ---
WIDTH, HEIGHT = 400, 700
FPS = 60

# Colors
BG_COLOR = (15, 15, 25)
PLAYER_COLOR = (100, 200, 255)
CRYSTAL_COLOR = (255, 0, 255)  # Breakable
IRON_COLOR = (80, 80, 80)      # Deadly
PARTICLE_COLOR = (200, 50, 255)
TEXT_COLOR = (255, 255, 255)

# --- Initialization ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Arcane Overload - Prototype")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)

# --- Game Entities ---
class Player:
    def __init__(self):
        self.rect = pygame.Rect(WIDTH // 2 - 15, HEIGHT - 100, 30, 30)
        self.speed = 300

    def move(self, dt):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= self.speed * dt
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += self.speed * dt
        
        # Clamp to screen
        self.rect.left = max(0, self.rect.left)
        self.rect.right = min(WIDTH, self.rect.right)

    def draw(self, surface):
        pygame.draw.rect(surface, PLAYER_COLOR, self.rect)
        # Inner core to make it look "arcane"
        pygame.draw.rect(surface, (255, 255, 255), self.rect.inflate(-10, -10))

class Obstacle:
    def __init__(self, y_pos):
        self.is_crystal = random.random() < 0.4  # 40% chance to be breakable
        width = random.randint(60, 120)
        x_pos = random.randint(0, WIDTH - width)
        self.rect = pygame.Rect(x_pos, y_pos, width, 20)
        self.color = CRYSTAL_COLOR if self.is_crystal else IRON_COLOR

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)

class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-150, 150)
        self.vy = random.uniform(-150, 150)
        self.timer = random.uniform(0.2, 0.5)
        self.size = random.randint(3, 8)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.timer -= dt

    def draw(self, surface):
        pygame.draw.rect(surface, PARTICLE_COLOR, (int(self.x), int(self.y), self.size, self.size))

# --- Game State ---
def main():
    player = Player()
    obstacles = []
    particles = []
    
    score = 0
    scroll_speed = 250
    spawn_timer = 0
    shake_timer = 0
    
    # Virtual surface for screen shake
    render_surface = pygame.Surface((WIDTH, HEIGHT))

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        # 1. Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # 2. Game Logic
        player.move(dt)

        # Spawning logic
        spawn_timer -= dt
        if spawn_timer <= 0:
            obstacles.append(Obstacle(-20))
            spawn_timer = random.uniform(0.6, 1.2)

        # Move obstacles and check collisions
        for obs in obstacles[:]:
            obs.rect.y += scroll_speed * dt
            
            if obs.rect.y > HEIGHT:
                obstacles.remove(obs)
                continue

            if player.rect.colliderect(obs.rect):
                if obs.is_crystal:
                    # THE JUICE: Hit-stop, Screen Shake, and Particles
                    pygame.time.delay(40)  # Hit-stop
                    shake_timer = 0.2      # Screen shake duration
                    
                    # Spawn particles
                    for _ in range(15):
                        particles.append(Particle(obs.rect.centerx, obs.rect.centery))
                    
                    obstacles.remove(obs)
                    score += 100
                    scroll_speed += 5  # Slowly increase difficulty
                else:
                    # Hit iron = Game Over
                    print(f"Game Over! Final Score: {score}")
                    running = False

        # Update particles
        for p in particles[:]:
            p.update(dt)
            if p.timer <= 0:
                particles.remove(p)

        # 3. Rendering
        render_surface.fill(BG_COLOR)
        
        for obs in obstacles:
            obs.draw(render_surface)
        for p in particles:
            p.draw(render_surface)
            
        player.draw(render_surface)

        # Draw Score
        score_surf = font.render(f"Score: {score}", True, TEXT_COLOR)
        render_surface.blit(score_surf, (10, 10))

        # Apply Screen Shake
        if shake_timer > 0:
            shake_timer -= dt
            shake_x = random.randint(-5, 5)
            shake_y = random.randint(-5, 5)
        else:
            shake_x, shake_y = 0, 0

        screen.blit(render_surface, (shake_x, shake_y))
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()