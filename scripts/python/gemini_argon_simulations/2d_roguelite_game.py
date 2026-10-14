import math
import random
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Type, TypeVar

import pygame

# ============================================================================
# CONFIGURATION & ARCANE-TECH PALETTE
# ============================================================================
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 800
FPS = 60
ARENA_MARGIN = 64

# Colors (Discord Dark Slate + Arcane Emerald & Cyan)
COLOR_BG_SLATE = (54, 57, 63)         # #36393f - Primary Discord Slate
COLOR_BG_DARKER = (47, 49, 54)        # #2f3136 - Grid & Floor Markings
COLOR_FLOOR_TEXT = (79, 84, 92)       # #4f545c - Rigid Monospace Floor Markings
COLOR_EMERALD = (0, 255, 136)         # #00ff88 - Arcane Emerald
COLOR_EMERALD_DARK = (16, 124, 75)    # Hooded Cloak Base
COLOR_CYAN = (0, 229, 255)            # #00e5ff - Cyan Fireballs & Highlights
COLOR_PING_RED = (237, 66, 69)        # #ed4245 - Mention "@" Projectiles & Raid Alert
COLOR_GOLD = (254, 231, 92)           # #fee75c - Accents
COLOR_WHITE = (242, 243, 245)

T = TypeVar("T")


# ============================================================================
# ECS CORE ARCHITECTURE
# ============================================================================
class World:
    """Lightweight Entity Component System (ECS) registry and state container."""

    def __init__(self) -> None:
        self._next_entity_id: int = 1
        self._components: Dict[Type, Dict[int, object]] = {}
        self._systems: List["System"] = []
        self._dead_entities: set[int] = set()

        # Global Arena & Event State
        self.arena_rect = pygame.Rect(
            ARENA_MARGIN,
            ARENA_MARGIN,
            SCREEN_WIDTH - ARENA_MARGIN * 2,
            SCREEN_HEIGHT - ARENA_MARGIN * 2,
        )
        self.score: int = 0
        self.wave: int = 1
        self.game_over: bool = False
        self.time_elapsed: float = 0.0

        # "Server Raid" Room Event State
        self.raid_active: bool = False
        self.raid_timer: float = 0.0
        self.raid_duration: float = 14.0
        self.raid_cooldown: float = 10.0
        self.raid_spawn_accum: float = 0.0
        self.screen_shake: float = 0.0

    def create_entity(self) -> int:
        eid = self._next_entity_id
        self._next_entity_id += 1
        return eid

    def destroy_entity(self, entity: int) -> None:
        self._dead_entities.add(entity)

    def add_component(self, entity: int, component: object) -> None:
        comp_type = type(component)
        if comp_type not in self._components:
            self._components[comp_type] = {}
        self._components[comp_type][entity] = component

    def get_component(self, entity: int, comp_type: Type[T]) -> Optional[T]:
        return self._components.get(comp_type, {}).get(entity)  # type: ignore

    def has_component(self, entity: int, comp_type: Type) -> bool:
        return entity in self._components.get(comp_type, {})

    def query(self, *comp_types: Type) -> List[Tuple[int, Tuple[object, ...]]]:
        """Yields (entity_id, (comp1, comp2, ...)) for entities matching all types."""
        if not comp_types:
            return []
        primary_dict = self._components.get(comp_types[0], {})
        results = []
        for entity, first_comp in primary_dict.items():
            if entity in self._dead_entities:
                continue
            comps = [first_comp]
            matched = True
            for ct in comp_types[1:]:
                c = self._components.get(ct, {}).get(entity)
                if c is None:
                    matched = False
                    break
                comps.append(c)
            if matched:
                results.append((entity, tuple(comps)))
        return results

    def add_system(self, system: "System") -> None:
        self._systems.append(system)

    def flush_dead_entities(self) -> None:
        for entity in self._dead_entities:
            for comp_dict in self._components.values():
                comp_dict.pop(entity, None)
        self._dead_entities.clear()

    def update(self, dt: float) -> None:
        for system in self._systems:
            system.update(self, dt)
        self.flush_dead_entities()


class System:
    """Base interface for all decoupled ECS systems."""

    def update(self, world: World, dt: float) -> None:
        raise NotImplementedError


# ============================================================================
# COMPONENTS (Pure Data Containers)
# ============================================================================
@dataclass
class Transform:
    x: float
    y: float
    angle: float = 0.0


@dataclass
class Velocity:
    vx: float = 0.0
    vy: float = 0.0
    drag: float = 0.0


@dataclass
class Collider:
    radius: float
    layer: str  # 'player', 'enemy', 'player_proj', 'enemy_proj'


@dataclass
class Health:
    hp: int
    max_hp: int
    iframes: float = 0.0
    flash_timer: float = 0.0


@dataclass
class PlayerTag:
    move_speed: float = 310.0
    fire_cooldown: float = 0.0
    fire_rate: float = 0.14
    mana_pulse: float = 0.0


@dataclass
class DeafenDash:
    """Handles the 'Deafen Dash' invulnerability & alpha-phasing mechanic."""
    duration: float = 0.32
    cooldown: float = 1.15
    speed_multiplier: float = 2.85
    active_timer: float = 0.0
    cooldown_timer: float = 0.0
    afterimage_timer: float = 0.0
    dash_dir: Tuple[float, float] = (0.0, 0.0)


@dataclass
class Projectile:
    damage: int
    ttl: float
    proj_type: str  # 'cyan_fireball' or 'at_ping'
    spin_speed: float = 0.0


@dataclass
class EnemyAI:
    kind: str  # 'troll' (ranged bullet-hell mask) or 'raider' (fast melee swarm)
    speed: float
    shoot_timer: float = 0.0
    shoot_interval: float = 1.8
    pattern_angle: float = 0.0
    pattern_variant: int = 0
    contact_damage: int = 15
    score_value: int = 100


@dataclass
class Visual:
    kind: str  # 'mage', 'troll', 'raider', 'cyan_fireball', 'at_ping'
    color: Tuple[int, int, int]
    accent_color: Tuple[int, int, int]
    alpha: int = 255
    scale: float = 1.0


@dataclass
class Particle:
    ttl: float
    max_ttl: float
    radius: float
    color: Tuple[int, int, int]
    glow: bool = True
    is_afterimage: bool = False


@dataclass
class FloatingText:
    text: str
    ttl: float
    max_ttl: float
    color: Tuple[int, int, int]


@dataclass
class GlassBarrier:
    rect: pygame.Rect
    is_raid_lock: bool = False
    label: str = "FIREWALL_NODE"


# ============================================================================
# ENTITY PREFAB FACTORIES
# ============================================================================
def spawn_player(world: World, x: float, y: float) -> int:
    eid = world.create_entity()
    world.add_component(eid, Transform(x=x, y=y))
    world.add_component(eid, Velocity())
    world.add_component(eid, Collider(radius=16.0, layer="player"))
    world.add_component(eid, Health(hp=100, max_hp=100))
    world.add_component(eid, PlayerTag())
    world.add_component(eid, DeafenDash())
    world.add_component(
        eid,
        Visual(
            kind="mage",
            color=COLOR_EMERALD,
            accent_color=COLOR_CYAN,
            alpha=255,
        ),
    )
    return eid


def spawn_troll(world: World, x: float, y: float) -> int:
    eid = world.create_entity()
    world.add_component(eid, Transform(x=x, y=y))
    world.add_component(eid, Velocity(drag=4.0))
    world.add_component(eid, Collider(radius=22.0, layer="enemy"))
    world.add_component(eid, Health(hp=90 + world.wave * 15, max_hp=90 + world.wave * 15))
    world.add_component(
        eid,
        EnemyAI(
            kind="troll",
            speed=105.0,
            shoot_timer=random.uniform(0.4, 1.4),
            shoot_interval=max(1.0, 2.0 - world.wave * 0.08),
            pattern_angle=random.uniform(0, math.tau),
            pattern_variant=random.randint(0, 2),
            contact_damage=15,
            score_value=250,
        ),
    )
    world.add_component(
        eid,
        Visual(
            kind="troll",
            color=COLOR_PING_RED,
            accent_color=COLOR_GOLD,
        ),
    )
    return eid


def spawn_raider(world: World, x: float, y: float) -> int:
    """Spawns a fast, low-health melee unit during the 'Server Raid' lockdown."""
    eid = world.create_entity()
    world.add_component(eid, Transform(x=x, y=y))
    world.add_component(eid, Velocity(drag=2.0))
    world.add_component(eid, Collider(radius=13.0, layer="enemy"))
    world.add_component(eid, Health(hp=28, max_hp=28))
    world.add_component(
        eid,
        EnemyAI(
            kind="raider",
            speed=random.uniform(235.0, 285.0),
            contact_damage=12,
            score_value=75,
        ),
    )
    world.add_component(
        eid,
        Visual(
            kind="raider",
            color=COLOR_PING_RED,
            accent_color=COLOR_WHITE,
        ),
    )
    return eid


def spawn_projectile(
    world: World,
    x: float,
    y: float,
    vx: float,
    vy: float,
    proj_type: str,
    damage: int,
    ttl: float = 3.5,
) -> int:
    eid = world.create_entity()
    angle = math.atan2(vy, vx)
    world.add_component(eid, Transform(x=x, y=y, angle=angle))
    world.add_component(eid, Velocity(vx=vx, vy=vy))
    is_player = proj_type == "cyan_fireball"
    world.add_component(
        eid,
        Collider(
            radius=8.0 if is_player else 10.0,
            layer="player_proj" if is_player else "enemy_proj",
        ),
    )
    world.add_component(
        eid,
        Projectile(
            damage=damage,
            ttl=ttl,
            proj_type=proj_type,
            spin_speed=0.0 if is_player else 3.5,
        ),
    )
    world.add_component(
        eid,
        Visual(
            kind=proj_type,
            color=COLOR_CYAN if is_player else COLOR_PING_RED,
            accent_color=COLOR_EMERALD if is_player else COLOR_WHITE,
        ),
    )
    return eid


def spawn_burst_particles(
    world: World,
    x: float,
    y: float,
    color: Tuple[int, int, int],
    count: int = 10,
    speed_range: Tuple[float, float] = (50.0, 220.0),
) -> None:
    for _ in range(count):
        eid = world.create_entity()
        ang = random.uniform(0, math.tau)
        spd = random.uniform(*speed_range)
        ttl = random.uniform(0.18, 0.45)
        world.add_component(eid, Transform(x=x, y=y))
        world.add_component(
            eid,
            Velocity(vx=math.cos(ang) * spd, vy=math.sin(ang) * spd, drag=4.5),
        )
        world.add_component(
            eid,
            Particle(
                ttl=ttl,
                max_ttl=ttl,
                radius=random.uniform(2.5, 5.5),
                color=color,
            ),
        )


def spawn_floating_text(
    world: World, x: float, y: float, text: str, color: Tuple[int, int, int]
) -> None:
    eid = world.create_entity()
    world.add_component(eid, Transform(x=x, y=y))
    world.add_component(eid, Velocity(vx=random.uniform(-20, 20), vy=-55.0, drag=1.5))
    world.add_component(eid, FloatingText(text=text, ttl=0.65, max_ttl=0.65, color=color))


def setup_arena_barriers(world: World) -> None:
    """Creates internal glassmorphic tactical pillars and perimeter raid gates."""
    pillars = [
        pygame.Rect(310, 230, 90, 90),
        pygame.Rect(SCREEN_WIDTH - 400, 230, 90, 90),
        pygame.Rect(310, SCREEN_HEIGHT - 320, 90, 90),
        pygame.Rect(SCREEN_WIDTH - 400, SCREEN_HEIGHT - 320, 90, 90),
    ]
    for idx, rect in enumerate(pillars):
        eid = world.create_entity()
        world.add_component(
            eid, GlassBarrier(rect=rect, is_raid_lock=False, label=f"NODE_0{idx+1}")
        )

    # 4 Perimeter Gates that seal with translucent red glass during a Server Raid
    gate_w, gate_h = 180, 22
    gates = [
        pygame.Rect(SCREEN_WIDTH // 2 - gate_w // 2, ARENA_MARGIN - 4, gate_w, gate_h),
        pygame.Rect(
            SCREEN_WIDTH // 2 - gate_w // 2,
            SCREEN_HEIGHT - ARENA_MARGIN - gate_h + 4,
            gate_w,
            gate_h,
        ),
        pygame.Rect(ARENA_MARGIN - 4, SCREEN_HEIGHT // 2 - gate_w // 2, gate_h, gate_w),
        pygame.Rect(
            SCREEN_WIDTH - ARENA_MARGIN - gate_h + 4,
            SCREEN_HEIGHT // 2 - gate_w // 2,
            gate_h,
            gate_w,
        ),
    ]
    for rect in gates:
        eid = world.create_entity()
        world.add_component(
            eid, GlassBarrier(rect=rect, is_raid_lock=True, label="RAID_GATE_LOCKED")
        )


# ============================================================================
# GAMEPLAY & COMBAT SYSTEMS
# ============================================================================
class InputAndPlayerSystem(System):
    """Handles WASD movement, mouse aiming, cyan fireball casting, and Deafen Dash."""

    def update(self, world: World, dt: float) -> None:
        if world.game_over:
            return

        keys = pygame.key.get_pressed()
        mouse_buttons = pygame.mouse.get_pressed()
        mx, my = pygame.mouse.get_pos()

        for eid, (transform, vel, player, dash, health, visual) in world.query(
            Transform, Velocity, PlayerTag, DeafenDash, Health, Visual
        ):
            player.mana_pulse += dt * 5.0
            player.fire_cooldown = max(0.0, player.fire_cooldown - dt)
            dash.cooldown_timer = max(0.0, dash.cooldown_timer - dt)

            # Aim toward cursor
            dx_aim = mx - transform.x
            dy_aim = my - transform.y
            transform.angle = math.atan2(dy_aim, dx_aim)

            # Read WASD directional input
            move_x = float(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - float(
                keys[pygame.K_a] or keys[pygame.K_LEFT]
            )
            move_y = float(keys[pygame.K_s] or keys[pygame.K_DOWN]) - float(
                keys[pygame.K_w] or keys[pygame.K_UP]
            )
            length = math.hypot(move_x, move_y)
            if length > 0:
                move_x /= length
                move_y /= length

            # Trigger "Deafen Dash" on Space or Right Click
            want_dash = keys[pygame.K_SPACE] or mouse_buttons[2]
            if want_dash and dash.cooldown_timer <= 0.0 and dash.active_timer <= 0.0:
                dash.active_timer = dash.duration
                dash.cooldown_timer = dash.cooldown
                # Dash toward movement direction, or toward mouse if standing still
                if length > 0:
                    dash.dash_dir = (move_x, move_y)
                else:
                    dash.dash_dir = (math.cos(transform.angle), math.sin(transform.angle))
                health.iframes = max(health.iframes, dash.duration + 0.06)
                spawn_floating_text(
                    world, transform.x, transform.y - 26, "DEAFENED [PHASING]", COLOR_CYAN
                )
                spawn_burst_particles(world, transform.x, transform.y, COLOR_EMERALD, 14)

            # Active Deafen Dash state vs Normal Movement
            if dash.active_timer > 0.0:
                dash.active_timer -= dt
                dash_speed = player.move_speed * dash.speed_multiplier
                vel.vx = dash.dash_dir[0] * dash_speed
                vel.vy = dash.dash_dir[1] * dash_speed
                visual.alpha = 95  # Translucent alpha-blending while phasing

                # Spawn emerald/cyan translucent afterimage trail
                dash.afterimage_timer -= dt
                if dash.afterimage_timer <= 0.0:
                    dash.afterimage_timer = 0.035
                    ghost = world.create_entity()
                    world.add_component(ghost, Transform(x=transform.x, y=transform.y))
                    world.add_component(
                        ghost,
                        Particle(
                            ttl=0.22,
                            max_ttl=0.22,
                            radius=15.0,
                            color=COLOR_CYAN,
                            is_afterimage=True,
                        ),
                    )
            else:
                vel.vx = move_x * player.move_speed
                vel.vy = move_y * player.move_speed
                visual.alpha = 155 if health.iframes > 0.0 else 255

            # Cast Cyan Fireballs (Left Mouse Button)
            if mouse_buttons[0] and player.fire_cooldown <= 0.0:
                player.fire_cooldown = player.fire_rate
                proj_speed = 680.0
                muzzle_dist = 22.0
                sx = transform.x + math.cos(transform.angle) * muzzle_dist
                sy = transform.y + math.sin(transform.angle) * muzzle_dist
                spawn_projectile(
                    world,
                    sx,
                    sy,
                    math.cos(transform.angle) * proj_speed,
                    math.sin(transform.angle) * proj_speed,
                    proj_type="cyan_fireball",
                    damage=24,
                )
                spawn_burst_particles(
                    world, sx, sy, COLOR_CYAN, count=4, speed_range=(40.0, 110.0)
                )


class EnemyAISystem(System):
    """Controls floating Troll masks ('@' bullet patterns) and Server Raid swarmers."""

    def update(self, world: World, dt: float) -> None:
        if world.game_over:
            return

        players = world.query(Transform, PlayerTag)
        if not players:
            return
        _, (player_tf, _) = players[0]

        for eid, (tf, vel, ai) in world.query(Transform, Velocity, EnemyAI):
            dx = player_tf.x - tf.x
            dy = player_tf.y - tf.y
            dist = math.hypot(dx, dy) or 1.0
            nx, ny = dx / dist, dy / dist
            tf.angle = math.atan2(dy, dx)

            if ai.kind == "troll":
                # Strafe/orbit behavior: maintain mid-range distance
                desired_dist = 260.0
                radial_factor = (dist - desired_dist) / 140.0
                radial_factor = max(-1.0, min(1.0, radial_factor))
                # Tangential orbit vector
                tx, ty = -ny, nx
                vel.vx = (nx * radial_factor + tx * 0.75) * ai.speed
                vel.vy = (ny * radial_factor + ty * 0.75) * ai.speed

                # Bullet-hell '@' pattern emission
                ai.shoot_timer -= dt
                if ai.shoot_timer <= 0.0:
                    ai.shoot_timer = ai.shoot_interval
                    self._fire_troll_pattern(world, tf, ai, tf.angle)

            elif ai.kind == "raider":
                # Fast relentless melee rush
                vel.vx = nx * ai.speed
                vel.vy = ny * ai.speed

    def _fire_troll_pattern(
        self, world: World, tf: Transform, ai: EnemyAI, aim_angle: float
    ) -> None:
        bullet_speed = 245.0
        if ai.pattern_variant == 0:
            # Dense 10-way radial ring of glowing '@' mentions
            count = 10
            ai.pattern_angle += 0.35
            for i in range(count):
                ang = ai.pattern_angle + (math.tau * i / count)
                spawn_projectile(
                    world,
                    tf.x,
                    tf.y,
                    math.cos(ang) * bullet_speed,
                    math.sin(ang) * bullet_speed,
                    proj_type="at_ping",
                    damage=16,
                    ttl=4.5,
                )
        elif ai.pattern_variant == 1:
            # Aimed 5-way fan + double speed layer
            spread = 0.20
            for layer_spd in (bullet_speed * 0.85, bullet_speed * 1.18):
                for offset in (-2, -1, 0, 1, 2):
                    ang = aim_angle + offset * spread
                    spawn_projectile(
                        world,
                        tf.x,
                        tf.y,
                        math.cos(ang) * layer_spd,
                        math.sin(ang) * layer_spd,
                        proj_type="at_ping",
                        damage=15,
                        ttl=4.2,
                    )
        else:
            # Twin counter-rotating arcane spiral burst
            count = 8
            ai.pattern_angle += 0.55
            for i in range(count):
                ang = ai.pattern_angle + (math.tau * i / count)
                spd = bullet_speed * (0.9 if i % 2 == 0 else 1.25)
                spawn_projectile(
                    world,
                    tf.x,
                    tf.y,
                    math.cos(ang) * spd,
                    math.sin(ang) * spd,
                    proj_type="at_ping",
                    damage=15,
                    ttl=4.5,
                )


class RaidDirectorSystem(System):
    """Manages wave spawns and triggers the 'Server Raid' lockdown room event."""

    def trigger_server_raid(self, world: World) -> None:
        if world.raid_active:
            return
        world.raid_active = True
        world.raid_timer = world.raid_duration
        world.raid_spawn_accum = 0.0
        world.screen_shake = 0.45

        players = world.query(Transform, PlayerTag)
        if players:
            _, (ptf, _) = players[0]
            spawn_floating_text(
                world,
                ptf.x,
                ptf.y - 45,
                "!! SERVER RAID LOCKDOWN INITIATED !!",
                COLOR_PING_RED,
            )

    def update(self, world: World, dt: float) -> None:
        if world.game_over:
            return

        world.time_elapsed += dt
        world.screen_shake = max(0.0, world.screen_shake - dt)

        enemies = world.query(EnemyAI)
        troll_count = sum(1 for _, (ai,) in enemies if ai.kind == "troll")

        # Keep Trolls active in the room
        if troll_count == 0 and not world.raid_active:
            spawn_count = min(6, 2 + world.wave)
            for _ in range(spawn_count):
                sx, sy = self._random_edge_point(world, inset=70)
                spawn_troll(world, sx, sy)
            world.wave += 1

        # Manage Server Raid Countdown & Swarm Spawning
        if world.raid_active:
            world.raid_timer -= dt
            world.raid_spawn_accum += dt
            spawn_interval = max(0.32, 0.68 - world.wave * 0.04)

            while world.raid_spawn_accum >= spawn_interval:
                world.raid_spawn_accum -= spawn_interval
                sx, sy = self._random_edge_point(world, inset=18)
                spawn_raider(world, sx, sy)
                spawn_burst_particles(world, sx, sy, COLOR_PING_RED, count=6)

            if world.raid_timer <= 0.0:
                world.raid_active = False
                world.raid_cooldown = 16.0
                players = world.query(Transform, PlayerTag)
                if players:
                    _, (ptf, _) = players[0]
                    spawn_floating_text(
                        world,
                        ptf.x,
                        ptf.y - 40,
                        "RAID CONTAINED // LOCKDOWN LIFTED",
                        COLOR_EMERALD,
                    )
        else:
            world.raid_cooldown -= dt
            if world.raid_cooldown <= 0.0:
                self.trigger_server_raid(world)
                # Also spawn an elite Troll alongside the raid
                sx, sy = self._random_edge_point(world, inset=80)
                spawn_troll(world, sx, sy)

    def _random_edge_point(self, world: World, inset: int = 40) -> Tuple[float, float]:
        r = world.arena_rect
        side = random.randint(0, 3)
        if side == 0:  # Top
            return random.uniform(r.left + inset, r.right - inset), float(r.top + inset)
        if side == 1:  # Bottom
            return random.uniform(r.left + inset, r.right - inset), float(r.bottom - inset)
        if side == 2:  # Left
            return float(r.left + inset), random.uniform(r.top + inset, r.bottom - inset)
        return float(r.right - inset), random.uniform(r.top + inset, r.bottom - inset)


class PhysicsAndCollisionSystem(System):
    """Resolves velocity, glassmorphic barrier collisions, and bullet-hell combat hits."""

    def update(self, world: World, dt: float) -> None:
        # 1. Integrate Positions & Drag
        for eid, (tf, vel) in world.query(Transform, Velocity):
            tf.x += vel.vx * dt
            tf.y += vel.vy * dt
            if vel.drag > 0.0:
                factor = max(0.0, 1.0 - vel.drag * dt)
                vel.vx *= factor
                vel.vy *= factor

        # Gather solid internal glass pillars
        solid_pillars = [
            b.rect
            for _, (b,) in world.query(GlassBarrier)
            if not b.is_raid_lock
        ]

        # 2. Arena Boundary & Glass Pillar Resolution for Actors
        for eid, (tf, col) in world.query(Transform, Collider):
            if col.layer in ("player", "enemy"):
                # Clamp inside the main slate arena
                tf.x = max(
                    world.arena_rect.left + col.radius,
                    min(world.arena_rect.right - col.radius, tf.x),
                )
                tf.y = max(
                    world.arena_rect.top + col.radius,
                    min(world.arena_rect.bottom - col.radius, tf.y),
                )
                # Push actors out of glassmorphic pillars
                for rect in solid_pillars:
                    self._resolve_circle_rect(tf, col.radius, rect)

            elif col.layer in ("player_proj", "enemy_proj"):
                # Destroy projectiles hitting arena outer walls
                if not world.arena_rect.inflate(-8, -8).collidepoint(tf.x, tf.y):
                    spawn_burst_particles(
                        world,
                        tf.x,
                        tf.y,
                        COLOR_CYAN if col.layer == "player_proj" else COLOR_PING_RED,
                        count=5,
                    )
                    world.destroy_entity(eid)
                    continue
                # Destroy projectiles hitting internal glass pillars
                for rect in solid_pillars:
                    if rect.collidepoint(tf.x, tf.y):
                        spawn_burst_particles(
                            world,
                            tf.x,
                            tf.y,
                            COLOR_CYAN if col.layer == "player_proj" else COLOR_PING_RED,
                            count=6,
                        )
                        world.destroy_entity(eid)
                        break

        # 3. Update Health Invulnerability & Hit Flash Timers
        for _, (hp,) in world.query(Health):
            hp.iframes = max(0.0, hp.iframes - dt)
            hp.flash_timer = max(0.0, hp.flash_timer - dt)

        # 4. Combat Hit Detection (Projectiles & Melee Swarms)
        self._resolve_combat_hits(world, dt)

        # 5. Lifecycle Cleanup (Projectiles, Particles, Floating Text)
        for eid, (proj, tf) in world.query(Projectile, Transform):
            proj.ttl -= dt
            tf.angle += proj.spin_speed * dt
            if proj.ttl <= 0.0:
                world.destroy_entity(eid)

        for eid, (part,) in world.query(Particle):
            part.ttl -= dt
            if part.ttl <= 0.0:
                world.destroy_entity(eid)

        for eid, (ft,) in world.query(FloatingText):
            ft.ttl -= dt
            if ft.ttl <= 0.0:
                world.destroy_entity(eid)

    def _resolve_circle_rect(
        self, tf: Transform, radius: float, rect: pygame.Rect
    ) -> None:
        closest_x = max(rect.left, min(tf.x, rect.right))
        closest_y = max(rect.top, min(tf.y, rect.bottom))
        dx = tf.x - closest_x
        dy = tf.y - closest_y
        dist_sq = dx * dx + dy * dy
        if dist_sq < radius * radius:
            dist = math.sqrt(dist_sq)
            if dist == 0.0:
                tf.y = rect.top - radius
            else:
                overlap = radius - dist
                tf.x += (dx / dist) * overlap
                tf.y += (dy / dist) * overlap

    def _resolve_combat_hits(self, world: World, dt: float) -> None:
        players = world.query(Transform, Collider, Health, PlayerTag)
        if not players:
            return
        player_eid, (p_tf, p_col, p_hp, _) = players[0]

        enemies = world.query(Transform, Collider, Health, EnemyAI)
        projectiles = world.query(Transform, Collider, Projectile)

        # Player Projectiles -> Enemies
        for proj_eid, (pr_tf, pr_col, proj) in projectiles:
            if pr_col.layer == "player_proj":
                for en_eid, (en_tf, en_col, en_hp, en_ai) in enemies:
                    if math.hypot(pr_tf.x - en_tf.x, pr_tf.y - en_tf.y) <= (
                        pr_col.radius + en_col.radius
                    ):
                        en_hp.hp -= proj.damage
                        en_hp.flash_timer = 0.09
                        spawn_burst_particles(world, pr_tf.x, pr_tf.y, COLOR_CYAN, count=7)
                        spawn_floating_text(
                            world, en_tf.x, en_tf.y - 18, f"-{proj.damage}", COLOR_CYAN
                        )
                        world.destroy_entity(proj_eid)

                        if en_hp.hp <= 0:
                            world.score += en_ai.score_value
                            spawn_burst_particles(
                                world,
                                en_tf.x,
                                en_tf.y,
                                COLOR_EMERALD if en_ai.kind == "troll" else COLOR_PING_RED,
                                count=18,
                            )
                            world.destroy_entity(en_eid)
                        break

            # Enemy '@' Projectiles -> Player (Ignored during Deafen Dash iframes!)
            elif pr_col.layer == "enemy_proj":
                if p_hp.iframes <= 0.0:
                    if math.hypot(pr_tf.x - p_tf.x, pr_tf.y - p_tf.y) <= (
                        pr_col.radius + p_col.radius
                    ):
                        self._damage_player(world, p_tf, p_hp, proj.damage)
                        world.destroy_entity(proj_eid)

        # Enemy Melee Contact -> Player (Raiders & Trolls)
        if p_hp.iframes <= 0.0:
            for en_eid, (en_tf, en_col, en_hp, en_ai) in enemies:
                if math.hypot(en_tf.x - p_tf.x, en_tf.y - p_tf.y) <= (
                    en_col.radius + p_col.radius
                ):
                    self._damage_player(world, p_tf, p_hp, en_ai.contact_damage)
                    if en_ai.kind == "raider":
                        # Raider self-destructs in a packet-burst on contact
                        world.destroy_entity(en_eid)
                    break

    def _damage_player(
        self, world: World, p_tf: Transform, p_hp: Health, damage: int
    ) -> None:
        p_hp.hp = max(0, p_hp.hp - damage)
        p_hp.iframes = 0.55
        p_hp.flash_timer = 0.15
        world.screen_shake = 0.25
        spawn_burst_particles(world, p_tf.x, p_tf.y, COLOR_PING_RED, count=16)
        spawn_floating_text(world, p_tf.x, p_tf.y - 24, f"-{damage} HP", COLOR_PING_RED)
        if p_hp.hp <= 0:
            world.game_over = True


# ============================================================================
# DECOUPLED RENDER SYSTEM (Arcane Tech + Glassmorphism + Glow Cache)
# ============================================================================
class RenderSystem:
    """Purely visual renderer decoupled from simulation state mutation."""

    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.font_sm = pygame.font.SysFont("consolas,courier,monospace", 14, bold=True)
        self.font_md = pygame.font.SysFont("consolas,courier,monospace", 18, bold=True)
        self.font_lg = pygame.font.SysFont("consolas,courier,monospace", 28, bold=True)
        self.font_at = pygame.font.SysFont("consolas,courier,monospace", 20, bold=True)

        self._glow_cache: Dict[Tuple[int, Tuple[int, int, int]], pygame.Surface] = {}
        self._at_proj_surface = self._build_at_projectile_surface()

    def _get_glow_surface(
        self, radius: int, color: Tuple[int, int, int]
    ) -> pygame.Surface:
        key = (radius, color)
        if key not in self._glow_cache:
            size = radius * 2
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            for layer in range(4, 0, -1):
                r = int(radius * (layer / 4.0))
                alpha = int(38 * (1.0 - (layer - 1) / 4.0))
                pygame.draw.circle(surf, (*color, alpha), (radius, radius), r)
            self._glow_cache[key] = surf
        return self._glow_cache[key]

    def _build_at_projectile_surface(self) -> pygame.Surface:
        """Pre-renders a glowing crimson '@' projectile sprite."""
        surf = pygame.Surface((40, 40), pygame.SRCALPHA)
        glow = self._get_glow_surface(18, COLOR_PING_RED)
        surf.blit(glow, (2, 2))
        pygame.draw.circle(surf, (*COLOR_PING_RED, 210), (20, 20), 10, width=2)
        glyph = self.font_at.render("@", True, COLOR_WHITE)
        surf.blit(
            glyph,
            (20 - glyph.get_width() // 2, 20 - glyph.get_height() // 2 - 1),
        )
        return surf

    def render(self, world: World) -> None:
        # Screen shake camera offset
        ox, oy = 0, 0
        if world.screen_shake > 0.0:
            mag = int(world.screen_shake * 14)
            ox = random.randint(-mag, mag)
            oy = random.randint(-mag, mag)

        # 1. Base Slate Background & Digital Grid Floor
        self.screen.fill(COLOR_BG_SLATE)
        self._draw_arcane_floor(world, ox, oy)

        # 2. Subtle Red Lighting Pulse during "Server Raid" Lockdown
        if world.raid_active:
            pulse = (math.sin(world.time_elapsed * 7.5) + 1.0) * 0.5
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((237, 66, 69, int(18 + pulse * 34)))
            self.screen.blit(overlay, (0, 0))

        # 3. Particles & Deafen Dash Afterimages
        for _, (tf, part) in world.query(Transform, Particle):
            ratio = max(0.0, part.ttl / part.max_ttl)
            px, py = int(tf.x + ox), int(tf.y + oy)
            if part.is_afterimage:
                ghost_surf = pygame.Surface((44, 44), pygame.SRCALPHA)
                alpha = int(115 * ratio)
                pygame.draw.circle(ghost_surf, (*COLOR_CYAN, alpha), (22, 22), 15)
                pygame.draw.circle(
                    ghost_surf, (*COLOR_EMERALD, alpha), (22, 22), 15, width=2
                )
                self.screen.blit(ghost_surf, (px - 22, py - 22))
            else:
                r = max(1, int(part.radius * ratio))
                if part.glow:
                    glow = self._get_glow_surface(max(6, r * 3), part.color)
                    self.screen.blit(
                        glow,
                        (px - glow.get_width() // 2, py - glow.get_height() // 2),
                        special_flags=pygame.BLEND_RGB_ADD,
                    )
                pygame.draw.circle(self.screen, part.color, (px, py), r)

        # 4. Glassmorphic Walls, Pillars, and Lockdown Gates
        self._draw_glassmorphic_arena(world, ox, oy)

        # 5. Entities (Mage, Trolls, Raiders, Projectiles)
        for eid, (tf, vis) in world.query(Transform, Visual):
            hp = world.get_component(eid, Health)
            dash = world.get_component(eid, DeafenDash)
            if vis.kind == "mage":
                self._draw_mage(world, tf, vis, hp, dash, ox, oy)
            elif vis.kind == "troll":
                self._draw_troll(tf, vis, hp, ox, oy)
            elif vis.kind == "raider":
                self._draw_raider(tf, vis, hp, ox, oy)
            elif vis.kind == "cyan_fireball":
                self._draw_cyan_fireball(tf, ox, oy)
            elif vis.kind == "at_ping":
                self._draw_at_projectile(tf, ox, oy)

        # 6. Floating Monospace Combat Text
        for _, (tf, ft) in world.query(Transform, FloatingText):
            txt_surf = self.font_sm.render(ft.text, True, ft.color)
            self.screen.blit(
                txt_surf,
                (int(tf.x - txt_surf.get_width() // 2 + ox), int(tf.y + oy)),
            )

        # 7. Monospace Arcane-Tech HUD
        self._draw_hud(world)

    def _draw_arcane_floor(self, world: World, ox: int, oy: int) -> None:
        r = world.arena_rect.move(ox, oy)
        pygame.draw.rect(self.screen, COLOR_BG_DARKER, r)

        # Rigid grid lines
        step = 64
        for x in range(r.left, r.right, step):
            pygame.draw.line(self.screen, COLOR_BG_SLATE, (x, r.top), (x, r.bottom), 2)
        for y in range(r.top, r.bottom, step):
            pygame.draw.line(self.screen, COLOR_BG_SLATE, (r.left, y), (r.right, y), 2)

        # Central Arcane Rune Circle on the floor
        cx, cy = r.centerx, r.centery
        pygame.draw.circle(self.screen, COLOR_BG_SLATE, (cx, cy), 135, width=2)
        pygame.draw.circle(self.screen, COLOR_BG_SLATE, (cx, cy), 95, width=1)

        # Monospace Floor Sector Stamps
        stamps = [
            ("#DRAGUNWF-CASTLE // SECTOR_01", r.left + 18, r.top + 14),
            ("SYS.ARCANE_CORE: ONLINE", r.right - 225, r.top + 14),
            ("CHAN_ID: 0x36393F_BULLET_HELL", r.left + 18, r.bottom - 26),
            ("[SPACE/RMB]: DEAFEN_DASH", r.right - 225, r.bottom - 26),
        ]
        for text, sx, sy in stamps:
            surf = self.font_sm.render(text, True, COLOR_FLOOR_TEXT)
            self.screen.blit(surf, (sx, sy))

    def _draw_glassmorphic_arena(self, world: World, ox: int, oy: int) -> None:
        r = world.arena_rect.move(ox, oy)
        border_col = COLOR_PING_RED if world.raid_active else COLOR_CYAN
        pygame.draw.rect(self.screen, border_col, r, width=2, border_radius=4)

        for _, (barrier,) in world.query(GlassBarrier):
            if barrier.is_raid_lock and not world.raid_active:
                continue

            brect = barrier.rect.move(ox, oy)
            glass = pygame.Surface((brect.width, brect.height), pygame.SRCALPHA)

            if barrier.is_raid_lock:
                # Translucent crimson lockdown barrier
                glass.fill((237, 66, 69, 58))
                pygame.draw.rect(
                    glass,
                    (*COLOR_PING_RED, 220),
                    glass.get_rect(),
                    width=2,
                    border_radius=4,
                )
            else:
                # Frosted cyan/emerald glassmorphic pillar
                glass.fill((255, 255, 255, 24))
                # Diagonal frosted specular reflection lines
                pygame.draw.line(
                    glass, (255, 255, 255, 55), (8, 0), (0, 8), width=2
                )
                pygame.draw.line(
                    glass,
                    (0, 229, 255, 45),
                    (brect.width - 10, 0),
                    (0, brect.height - 10),
                    width=3,
                )
                pygame.draw.rect(
                    glass,
                    (*COLOR_CYAN, 150),
                    glass.get_rect(),
                    width=2,
                    border_radius=6,
                )

            self.screen.blit(glass, brect.topleft)
            if not barrier.is_raid_lock:
                lbl = self.font_sm.render(barrier.label, True, COLOR_CYAN)
                self.screen.blit(
                    lbl,
                    (
                        brect.centerx - lbl.get_width() // 2,
                        brect.centery - lbl.get_height() // 2,
                    ),
                )

    def _draw_mage(
        self,
        world: World,
        tf: Transform,
        vis: Visual,
        hp: Optional[Health],
        dash: Optional[DeafenDash],
        ox: int,
        oy: int,
    ) -> None:
        px, py = int(tf.x + ox), int(tf.y + oy)

        # Ambient emerald/cyan aura
        glow = self._get_glow_surface(30, COLOR_EMERALD)
        self.screen.blit(
            glow,
            (px - 30, py - 30),
            special_flags=pygame.BLEND_RGB_ADD,
        )

        # Render Mage onto an alpha surface to support Deafen Dash translucency
        mage_surf = pygame.Surface((64, 64), pygame.SRCALPHA)
        c = 32
        alpha = vis.alpha

        # Outer Emerald Cloak & Hood
        cloak_color = (
            (*COLOR_WHITE, alpha)
            if (hp and hp.flash_timer > 0)
            else (*COLOR_EMERALD_DARK, alpha)
        )
        trim_color = (*COLOR_EMERALD, alpha)

        pygame.draw.circle(mage_surf, cloak_color, (c, c), 16)
        pygame.draw.circle(mage_surf, trim_color, (c, c), 16, width=2)

        # Pointed Green Hood Peak (oriented opposite to aim vector)
        back_x = c - math.cos(tf.angle) * 14
        back_y = c - math.sin(tf.angle) * 14
        perp_x = -math.sin(tf.angle) * 9
        perp_y = math.cos(tf.angle) * 9
        hood_pts = [
            (back_x, back_y),
            (c + perp_x, c + perp_y),
            (c - perp_x, c - perp_y),
        ]
        pygame.draw.polygon(mage_surf, (*COLOR_EMERALD, alpha), hood_pts)

        # Shadowed Visor & Glowing Cyan Eyes
        eye_base_x = c + math.cos(tf.angle) * 5
        eye_base_y = c + math.sin(tf.angle) * 5
        pygame.draw.circle(mage_surf, (20, 22, 26, alpha), (int(eye_base_x), int(eye_base_y)), 8)
        for side in (-1, 1):
            ex = eye_base_x + math.cos(tf.angle) * 3 - math.sin(tf.angle) * side * 3.5
            ey = eye_base_y + math.sin(tf.angle) * 3 + math.cos(tf.angle) * side * 3.5
            pygame.draw.circle(mage_surf, (*COLOR_CYAN, alpha), (int(ex), int(ey)), 2)

        # Floating Cyan Arcane Orb at Staff Tip
        orb_x = int(c + math.cos(tf.angle) * 21)
        orb_y = int(c + math.sin(tf.angle) * 21)
        pygame.draw.circle(mage_surf, (*COLOR_CYAN, alpha), (orb_x, orb_y), 5)
        pygame.draw.circle(mage_surf, (*COLOR_WHITE, alpha), (orb_x, orb_y), 2)

        self.screen.blit(mage_surf, (px - c, py - c))

        # Draw Discord "Deafened" Slashed-Headset Icon above Mage while Dashing
        if dash and dash.active_timer > 0.0:
            hx, hy = px, py - 28
            pygame.draw.arc(
                self.screen,
                COLOR_CYAN,
                pygame.Rect(hx - 8, hy - 8, 16, 14),
                0,
                math.pi,
                2,
            )
            pygame.draw.line(self.screen, COLOR_PING_RED, (hx - 9, hy - 8), (hx + 9, hy + 6), 2)

    def _draw_troll(
        self,
        tf: Transform,
        vis: Visual,
        hp: Optional[Health],
        ox: int,
        oy: int,
    ) -> None:
        px, py = int(tf.x + ox), int(tf.y + oy)
        glow = self._get_glow_surface(28, COLOR_PING_RED)
        self.screen.blit(
            glow, (px - 28, py - 28), special_flags=pygame.BLEND_RGB_ADD
        )

        # Floating Digital/Arcane Mask Polygon
        fill = COLOR_WHITE if (hp and hp.flash_timer > 0) else (40, 43, 48)
        mask_pts = [
            (px, py - 22),
            (px + 19, py - 10),
            (px + 15, py + 14),
            (px, py + 23),
            (px - 15, py + 14),
            (px - 19, py - 10),
        ]
        pygame.draw.polygon(self.screen, fill, mask_pts)
        pygame.draw.polygon(self.screen, COLOR_PING_RED, mask_pts, width=2)

        # Menacing Glowing Eyes & Grin
        pygame.draw.polygon(
            self.screen, COLOR_PING_RED, [(px - 11, py - 6), (px - 3, py - 2), (px - 10, py + 1)]
        )
        pygame.draw.polygon(
            self.screen, COLOR_PING_RED, [(px + 11, py - 6), (px + 3, py - 2), (px + 10, py + 1)]
        )
        pygame.draw.arc(
            self.screen,
            COLOR_GOLD,
            pygame.Rect(px - 10, py + 1, 20, 12),
            math.pi,
            math.tau,
            2,
        )

        # Mini Health Bar above Troll
        if hp and hp.hp < hp.max_hp:
            bw = 34
            ratio = max(0.0, hp.hp / hp.max_hp)
            pygame.draw.rect(self.screen, COLOR_BG_DARKER, (px - bw // 2, py - 30, bw, 4))
            pygame.draw.rect(
                self.screen, COLOR_PING_RED, (px - bw // 2, py - 30, int(bw * ratio), 4)
            )

    def _draw_raider(
        self,
        tf: Transform,
        vis: Visual,
        hp: Optional[Health],
        ox: int,
        oy: int,
    ) -> None:
        px, py = int(tf.x + ox), int(tf.y + oy)
        glow = self._get_glow_surface(18, COLOR_PING_RED)
        self.screen.blit(
            glow, (px - 18, py - 18), special_flags=pygame.BLEND_RGB_ADD
        )

        # Sharp darting chevron geometry oriented along velocity/aim
        ca, sa = math.cos(tf.angle), math.sin(tf.angle)
        pts = [
            (px + ca * 15, py + sa * 15),
            (px - ca * 10 - sa * 10, py - sa * 10 + ca * 10),
            (px - ca * 5, py - sa * 5),
            (px - ca * 10 + sa * 10, py - sa * 10 - ca * 10),
        ]
        fill = COLOR_WHITE if (hp and hp.flash_timer > 0) else COLOR_PING_RED
        pygame.draw.polygon(self.screen, fill, pts)
        pygame.draw.polygon(self.screen, COLOR_WHITE, pts, width=1)

    def _draw_cyan_fireball(self, tf: Transform, ox: int, oy: int) -> None:
        px, py = int(tf.x + ox), int(tf.y + oy)
        glow = self._get_glow_surface(18, COLOR_CYAN)
        self.screen.blit(
            glow, (px - 18, py - 18), special_flags=pygame.BLEND_RGB_ADD
        )
        pygame.draw.circle(self.screen, COLOR_CYAN, (px, py), 7)
        pygame.draw.circle(self.screen, COLOR_WHITE, (px, py), 3)

    def _draw_at_projectile(self, tf: Transform, ox: int, oy: int) -> None:
        px, py = int(tf.x + ox), int(tf.y + oy)
        self.screen.blit(self._at_proj_surface, (px - 20, py - 20))

    def _draw_hud(self, world: World) -> None:
        # Top Glassmorphic Status Bar
        hud_bar = pygame.Surface((SCREEN_WIDTH - ARENA_MARGIN * 2, 46), pygame.SRCALPHA)
        hud_bar.fill((32, 34, 37, 210))
        pygame.draw.rect(
            hud_bar, (*COLOR_EMERALD, 160), hud_bar.get_rect(), width=1, border_radius=6
        )
        self.screen.blit(hud_bar, (ARENA_MARGIN, 10))

        players = world.query(Health, DeafenDash, PlayerTag)
        if players:
            _, (hp, dash, _) = players[0]
            # HP Bar
            hp_ratio = max(0.0, hp.hp / hp.max_hp)
            pygame.draw.rect(self.screen, COLOR_BG_SLATE, (ARENA_MARGIN + 16, 21, 180, 22), border_radius=4)
            pygame.draw.rect(
                self.screen,
                COLOR_EMERALD if hp_ratio > 0.3 else COLOR_PING_RED,
                (ARENA_MARGIN + 16, 21, int(180 * hp_ratio), 22),
                border_radius=4,
            )
            hp_txt = self.font_sm.render(f"MAGE_HP: {hp.hp}/{hp.max_hp}", True, COLOR_WHITE)
            self.screen.blit(hp_txt, (ARENA_MARGIN + 26, 24))

            # Deafen Dash Status Indicator
            dash_ready = dash.cooldown_timer <= 0.0
            dash_col = COLOR_CYAN if dash_ready else COLOR_FLOOR_TEXT
            dash_str = (
                "DEAFEN_DASH [SPACE/RMB]: READY"
                if dash_ready
                else f"DEAFEN_DASH: {dash.cooldown_timer:.1f}s"
            )
            dash_surf = self.font_sm.render(dash_str, True, dash_col)
            self.screen.blit(dash_surf, (ARENA_MARGIN + 220, 24))

        # Wave, Score & Manual Raid Trigger Hint
        status_str = (
            f"WAVE: {world.wave:02d}  |  SCORE: {world.score:05d}  |  [F]: FORCE SERVER RAID"
        )
        status_surf = self.font_sm.render(status_str, True, COLOR_EMERALD)
        self.screen.blit(
            status_surf,
            (SCREEN_WIDTH - ARENA_MARGIN - status_surf.get_width() - 16, 24),
        )

        # Active Server Raid Warning Banner
        if world.raid_active:
            banner = self.font_md.render(
                f"⚠ ALERT: INCOMING SERVER RAID // LOCKDOWN ACTIVE ({world.raid_timer:.1f}s) ⚠",
                True,
                COLOR_PING_RED,
            )
            self.screen.blit(
                banner, (SCREEN_WIDTH // 2 - banner.get_width() // 2, ARENA_MARGIN + 12)
            )

        # Game Over Overlay
        if world.game_over:
            over_glass = pygame.Surface((520, 170), pygame.SRCALPHA)
            over_glass.fill((24, 25, 28, 235))
            pygame.draw.rect(
                over_glass, COLOR_PING_RED, over_glass.get_rect(), width=2, border_radius=8
            )
            bx = SCREEN_WIDTH // 2 - 260
            by = SCREEN_HEIGHT // 2 - 85
            self.screen.blit(over_glass, (bx, by))

            t1 = self.font_lg.render("CONNECTION TERMINATED", True, COLOR_PING_RED)
            t2 = self.font_md.render(
                f"FINAL SCORE: {world.score} // WAVES SURVIVED: {world.wave}",
                True,
                COLOR_WHITE,
            )
            t3 = self.font_sm.render(
                "PRESS [R] TO REBOOT DRAGUNWF'S CASTLE  |  [ESC] TO EXIT",
                True,
                COLOR_CYAN,
            )
            self.screen.blit(t1, (SCREEN_WIDTH // 2 - t1.get_width() // 2, by + 28))
            self.screen.blit(t2, (SCREEN_WIDTH // 2 - t2.get_width() // 2, by + 78))
            self.screen.blit(t3, (SCREEN_WIDTH // 2 - t3.get_width() // 2, by + 122))


# ============================================================================
# ENGINE BOOTSTRAP & MAIN LOOP
# ============================================================================
def create_game_world() -> Tuple[World, RaidDirectorSystem]:
    world = World()
    raid_director = RaidDirectorSystem()

    world.add_system(InputAndPlayerSystem())
    world.add_system(EnemyAISystem())
    world.add_system(raid_director)
    world.add_system(PhysicsAndCollisionSystem())

    setup_arena_barriers(world)
    spawn_player(world, SCREEN_WIDTH / 2.0, SCREEN_HEIGHT / 2.0)
    spawn_troll(world, 220.0, 180.0)
    spawn_troll(world, SCREEN_WIDTH - 220.0, SCREEN_HEIGHT - 180.0)

    return world, raid_director


def main() -> None:
    pygame.init()
    pygame.display.set_caption("DragunWF's Castle // Arcane-Tech Bullet Hell")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    world, raid_director = create_game_world()
    renderer = RenderSystem(screen)

    running = True
    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r and world.game_over:
                    world, raid_director = create_game_world()
                elif event.key == pygame.K_f and not world.game_over:
                    # Allow instant on-demand testing of the Server Raid Lockdown
                    raid_director.trigger_server_raid(world)

        world.update(dt)
        renderer.render(world)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()