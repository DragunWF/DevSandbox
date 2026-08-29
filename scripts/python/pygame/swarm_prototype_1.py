import pygame
import random
import math

# --- Configuration & Constants ---
WIDTH, HEIGHT = 800, 600
FPS = 60

# Colors
BG_COLOR = (25, 25, 30)         # Dark grey background
BOID_COLOR = (100, 150, 255)    # Blue minions
TARGET_COLOR = (255, 50, 50)    # Red targets
TEXT_COLOR = (255, 255, 255)

# Boid / Swarm Settings
NUM_BOIDS = 100
MAX_SPEED = 5.0
MAX_FORCE = 0.15
PERCEPTION_RADIUS = 60          # How far a boid can "see" its flockmates
PERCEPTION_SQ = PERCEPTION_RADIUS ** 2 # Squared for performance

# Behavior Weights (Normal state)
W_ALIGNMENT = 1.0
W_COHESION = 1.0
W_SEPARATION = 1.5
W_MOUSE = 1.2

# Behavior Weights ("Twist" / Dense state)
W_DENSE_COHESION = 6.0          # Drastically increase pull towards flock center
W_DENSE_MOUSE = 4.0             # Drastically increase pull towards cursor
W_DENSE_SEPARATION = 0.5        # Reduce separation to allow tighter packing

class Boid:
    def __init__(self, x, y):
        self.position = pygame.math.Vector2(x, y)
        # Random initial velocity
        self.velocity = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
        if self.velocity.length_squared() > 0:
            self.velocity.scale_to_length(MAX_SPEED)
        self.acceleration = pygame.math.Vector2(0, 0)
        self.size = 8

    def apply_force(self, force):
        self.acceleration += force

    def steer(self, desired):
        """Calculates the steering force required to reach a desired velocity."""
        if desired.length_squared() > 0:
            desired.scale_to_length(MAX_SPEED)
            steer_force = desired - self.velocity
            if steer_force.length_squared() > MAX_FORCE ** 2:
                steer_force.scale_to_length(MAX_FORCE)
            return steer_force
        return pygame.math.Vector2(0, 0)

    def apply_behaviors(self, boids, mouse_pos, is_dense):
        """Calculates and applies Boids AI rules: Cohesion, Alignment, Separation."""
        alignment_vec = pygame.math.Vector2(0, 0)
        cohesion_vec = pygame.math.Vector2(0, 0)
        separation_vec = pygame.math.Vector2(0, 0)
        total = 0

        # Iterate through flock to calculate local behaviors
        for other in boids:
            if other is not self:
                dist_sq = self.position.distance_squared_to(other.position)
                if dist_sq < PERCEPTION_SQ:
                    # Alignment: Add velocities of local flockmates
                    alignment_vec += other.velocity
                    
                    # Cohesion: Add positions to find the local center of mass
                    cohesion_vec += other.position
                    
                    # Separation: Steer away from crowding neighbors
                    diff = self.position - other.position
                    if dist_sq > 0:
                        diff /= dist_sq # Weight closer boids more heavily
                    separation_vec += diff
                    
                    total += 1

        if total > 0:
            # Finalize Alignment
            alignment_vec /= total
            alignment_steer = self.steer(alignment_vec)
            
            # Finalize Cohesion (steer towards center of mass)
            cohesion_vec /= total
            cohesion_steer = self.steer(cohesion_vec - self.position)
            
            # Finalize Separation
            separation_vec /= total
            separation_steer = self.steer(separation_vec)
        else:
            alignment_steer = pygame.math.Vector2(0, 0)
            cohesion_steer = pygame.math.Vector2(0, 0)
            separation_steer = pygame.math.Vector2(0, 0)

        # Mouse attraction behavior
        mouse_steer = self.steer(mouse_pos - self.position)

        # Apply weights based on the "Twist" mechanic (Density Control)
        if is_dense:
            self.apply_force(alignment_steer * W_ALIGNMENT)
            self.apply_force(cohesion_steer * W_DENSE_COHESION)
            self.apply_force(separation_steer * W_DENSE_SEPARATION)
            self.apply_force(mouse_steer * W_DENSE_MOUSE)
        else:
            self.apply_force(alignment_steer * W_ALIGNMENT)
            self.apply_force(cohesion_steer * W_COHESION)
            self.apply_force(separation_steer * W_SEPARATION)
            self.apply_force(mouse_steer * W_MOUSE)

    def update(self):
        """Updates physics and resets acceleration."""
        self.velocity += self.acceleration
        if self.velocity.length_squared() > MAX_SPEED ** 2:
            self.velocity.scale_to_length(MAX_SPEED)
        
        self.position += self.velocity
        self.acceleration *= 0 # Clear acceleration for next frame

    def draw(self, surface):
        """Draws the boid as a triangle pointing in the direction of velocity."""
        angle = math.atan2(self.velocity.y, self.velocity.x)
        # Calculate triangle vertices based on current angle
        p1 = self.position + pygame.math.Vector2(math.cos(angle), math.sin(angle)) * self.size * 1.5
        p2 = self.position + pygame.math.Vector2(math.cos(angle + 2.5), math.sin(angle + 2.5)) * self.size
        p3 = self.position + pygame.math.Vector2(math.cos(angle - 2.5), math.sin(angle - 2.5)) * self.size
        pygame.draw.polygon(surface, BOID_COLOR, [p1, p2, p3])

class Target:
    def __init__(self):
        # Spawn randomly within screen bounds, slightly padded
        self.position = pygame.math.Vector2(random.randint(50, WIDTH-50), random.randint(50, HEIGHT-50))
        self.radius = 12

    def draw(self, surface):
        pygame.draw.circle(surface, TARGET_COLOR, (int(self.position.x), int(self.position.y)), self.radius)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Fluid Swarm Commander Prototype")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 28)

    # Initialize Entities
    boids = [Boid(random.randint(0, WIDTH), random.randint(0, HEIGHT)) for _ in range(NUM_BOIDS)]
    targets = []
    score = 0
    target_spawn_timer = 0

    running = True
    while running:
        # 1. Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # 2. Logic Updates
        mouse_x, mouse_y = pygame.mouse.get_pos()
        mouse_vec = pygame.math.Vector2(mouse_x, mouse_y)
        
        # The "Twist": Check if Left Mouse Button is held
        mouse_buttons = pygame.mouse.get_pressed()
        is_dense = mouse_buttons[0] 

        # Spawn Targets periodically (max 5 on screen)
        target_spawn_timer += 1
        if target_spawn_timer > 60 and len(targets) < 5:
            targets.append(Target())
            target_spawn_timer = 0

        # Update Swarm
        for boid in boids:
            boid.apply_behaviors(boids, mouse_vec, is_dense)
            boid.update()

        # Check Collisions (Swarm vs Targets)
        targets_to_remove = []
        for target in targets:
            for boid in boids:
                # Fast distance check using squared distance
                if boid.position.distance_squared_to(target.position) < target.radius ** 2:
                    score += 1
                    targets_to_remove.append(target)
                    break # Target is destroyed, move to next target
        
        for t in targets_to_remove:
            if t in targets:
                targets.remove(t)

        # 3. Rendering
        screen.fill(BG_COLOR)

        for target in targets:
            target.draw(screen)

        for boid in boids:
            boid.draw(screen)

        # Draw UI (Score & FPS)
        fps = int(clock.get_fps())
        score_surface = font.render(f"Score: {score}", True, TEXT_COLOR)
        fps_surface = font.render(f"FPS: {fps}", True, TEXT_COLOR)
        mode_surface = font.render(f"Mode: {'DENSE' if is_dense else 'FLUID'}", True, TEXT_COLOR)
        
        screen.blit(score_surface, (10, 10))
        screen.blit(fps_surface, (10, 40))
        screen.blit(mode_surface, (10, 70))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()