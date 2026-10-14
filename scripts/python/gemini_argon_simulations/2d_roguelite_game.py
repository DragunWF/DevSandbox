import math
import random
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Type, TypeVar

import pygame

# ============================================================================
# CONFIGURATION & ARCANE-TECH PALETTE
# ============================================================================
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 800
FPS = 60
ARENA_MARGIN = 72

# Colors (Discord Dark Slate + High-Fantasy Arcane Emerald & Cyan)
COLOR_BG_VOID = (32, 34, 37)          # #202225 - Outer Void
COLOR_BG_SLATE = (54, 57, 63)         # #36393f - Primary Discord Slate
COLOR_BG_DARKER = (47, 49, 54)        # #2f3136 - Grid & Floor Markings
COLOR_FLOOR_TEXT = (79, 84, 92)       # #4f545c - Rigid Monospace Floor Markings
COLOR_EMERALD = (0, 255, 136)         # #00ff88 - Arcane Emerald
COLOR_EMERALD_DARK = (14, 98, 60)     # Wizard Cloak Base
COLOR_EMERALD_DEEP = (9, 58, 36)      # Wizard Cloak Shadow
COLOR_CYAN = (0, 229, 255)            # #00e5ff - Cyan Fireballs & Teleporters
COLOR_PING_RED = (237, 66, 69)        # #ed4245 - Mention "@" Projectiles & Raid Alert
COLOR_CRIMSON_DARK = (92, 22, 28)     # Warlock Robe Base
COLOR_GOLD = (254, 231, 92)           # #fee75c - Arcane Trim & Sanctum Accents
COLOR_STAFF_WOOD = (138, 92, 54)      # Arcane Staff Shaft
COLOR_WHITE = (242, 243, 245)

CARDINALS: Dict[str, Tuple[int, int]] = {
    "N": (0, -1),
    "S": (0, 1),
    "E": (1, 0),
    "W": (-1, 0),
}
OPPOSITE_DIR: Dict[str, str] = {"N": "S", "S": "N", "E": "W", "W": "E"}

T = TypeVar("T")


# ============================================================================
# PROCEDURAL DUNGEON DATA STRUCTURES
# ============================================================================
@dataclass
class RoomData:
    coords: Tuple[int, int]
    room_type: str  # 'START', 'COMBAT', 'RAID', 'SANCTUM'
    name: str
    cleared: bool = False
    visited: bool = False
    doors: Dict[str, Tuple[int, int]] = field(default_factory=dict)
    pillars: List[pygame.Rect] = field(default_factory=list)
    teleporter_pos: Tuple[float, float] = (SCREEN_WIDTH / 2.0, SCREEN_HEIGHT / 2.0)


class DungeonGenerator:
    """Generates a procedural multi-room floor graph with glassmorphic pillar layouts."""

    COMBAT_NAMES = [
        "#arcane-hall",
        "#hex-chamber",
        "#mana-conduit",
        "#rune-foundry",
        "#crypt-of-pings",
    ]

    @classmethod
    def generate_floor(cls, floor_num: int) -> Dict[Tuple[int, int], RoomData]:
        target_rooms = min(10, 6 + floor_num)
        rooms: Dict[Tuple[int, int], RoomData] = {}

        start_coords = (0, 0)
        rooms[start_coords] = RoomData(
            coords=start_coords,
            room_type="START",
            name="#welcome-sanctum",
            cleared=True,
            visited=True,
            pillars=[],
        )

        # Random walk + branching growth
        frontier: List[Tuple[int, int]] = [start_coords]
        while len(rooms) < target_rooms:
            base = random.choice(frontier)
            dirs = list(CARDINALS.items())
            random.shuffle(dirs)
            for _, (dx, dy) in dirs:
                nx, ny = base[0] + dx, base[1] + dy
                if (nx, ny) not in rooms:
                    rooms[(nx, ny)] = RoomData(
                        coords=(nx, ny),
                        room_type="COMBAT",
                        name=random.choice(cls.COMBAT_NAMES),
                        pillars=cls._generate_pillars(),
                    )
                    frontier.append((nx, ny))
                    break

        # Link adjacent rooms with doors
        for (x, y), room in rooms.items():
            for d_name, (dx, dy) in CARDINALS.items():
                neighbor = (x + dx, y + dy)
                if neighbor in rooms:
                    room.doors[d_name] = neighbor

        # Assign deepest room as SANCTUM (Boss + Floor Portal) and another as RAID
        non_start = [c for c in rooms if c != start_coords]
        non_start.sort(key=lambda c: abs(c[0]) + abs(c[1]), reverse=True)

        if non_start:
            sanctum_coord = non_start[0]
            rooms[sanctum_coord].room_type = "SANCTUM"
            rooms[sanctum_coord].name = "#admin-throne"
            rooms[sanctum_coord].pillars = cls._generate_pillars(preset="sanctum")

        if len(non_start) > 1:
            raid_coord = non_start[1]
            rooms[raid_coord].room_type = "RAID"
            rooms[raid_coord].name = "#raid-quarantine"
            rooms[raid_coord].pillars = cls._generate_pillars(preset="raid")

        return rooms

    @staticmethod
    def _generate_pillars(preset: Optional[str] = None) -> List[pygame.Rect]:
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        if preset == "sanctum":
            return [
                pygame.Rect(280, 210, 76, 76),
                pygame.Rect(SCREEN_WIDTH - 356, 210, 76, 76),
                pygame.Rect(280, SCREEN_HEIGHT - 286, 76, 76),
                pygame.Rect(SCREEN_WIDTH - 356, SCREEN_HEIGHT - 286, 76, 76),
            ]
        if preset == "raid":
            return [
                pygame.Rect(cx - 220, cy - 45, 70, 90),
                pygame.Rect(cx + 150, cy - 45, 70, 90),
            ]

        choice = random.randint(0, 2)
        if choice == 0:
            return [
                pygame.Rect(310, 230, 84, 84),
                pygame.Rect(SCREEN_WIDTH - 394, 230, 84, 84),
                pygame.Rect(310, SCREEN_HEIGHT - 314, 84, 84),
                pygame.Rect(SCREEN_WIDTH - 394, SCREEN_HEIGHT - 314, 84, 84),
            ]
        if choice == 1:
            return [
                pygame.Rect(cx - 260, cy - 110, 70, 220),
                pygame.Rect(cx + 190, cy - 110, 70, 220),
            ]
        return [
            pygame.Rect(cx - 180, cy - 150, 80, 70),
            pygame.Rect(cx + 100, cy - 150, 80, 70),
            pygame.Rect(cx - 180, cy + 80, 80, 70),
            pygame.Rect(cx + 100, cy + 80, 80, 70),
        ]


# ============================================================================
# ECS CORE ARCHITECTURE
# ============================================================================
class World:
    """Lightweight Entity Component System (ECS) registry and dungeon state container."""

    def __init__(self) -> None:
        self._next_entity_id: int = 1
        self._components: Dict[Type, Dict[int, object]] = {}
        self._systems: List["System"] = []
        self._dead_entities: Set[int] = set()

        self.arena_rect = pygame.Rect(
            ARENA_MARGIN,
            ARENA_MARGIN,
            SCREEN_WIDTH - ARENA_MARGIN * 2,
            SCREEN_HEIGHT - ARENA_MARGIN * 2,
        )
        self.score: int = 0
        self.floor_num: int = 1
        self.game_over: bool = False
        self.time_elapsed: float = 0.0
        self.screen_shake: float = 0.0
        self.transition_cooldown: float = 0.0

        # Procedural Dungeon State
        self.rooms: Dict[Tuple[int, int], RoomData] = DungeonGenerator.generate_floor(1)
        self.current_room_coords: Tuple[int, int] = (0, 0)
        self.room_locked: bool = False

        # "Server Raid" Room Event State
        self.raid_active: bool = False
        self.raid_timer: float = 0.0
        self.raid_duration: float = 13.0
        self.raid_spawn_accum: float = 0.0

        # Interactive Minimap Click Rects: maps room_coords -> screen rect
        self.minimap_rects: Dict[Tuple[int, int], pygame.Rect] = {}

    @property
    def current_room(self) -> RoomData:
        return self.rooms[self.current_room_coords]

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

    def query(self, *comp_types: Type) -> List[Tuple[int, Tuple[object, ...]]]:
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
class HumanoidAnim:
    """Tracks walk stride cycles, weapon swing/cast recoil, and cape billow."""
    walk_phase: float = 0.0
    cast_recoil: float = 0.0
    facing_left: bool = False


@dataclass
class PlayerTag:
    move_speed: float = 315.0
    fire_cooldown: float = 0.0
    fire_rate: float = 0.14


@dataclass
class DeafenDash:
    duration: float = 0.32
    cooldown: float = 1.10
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
    kind: str  # 'troll_warlock', 'raid_thrall', 'arch_overseer'
    speed: float
    shoot_timer: float = 0.0
    shoot_interval: float = 1.7
    pattern_angle: float = 0.0
    pattern_variant: int = 0
    contact_damage: int = 15
    score_value: int = 120


@dataclass
class Visual:
    kind: str  # 'mage', 'troll_warlock', 'raid_thrall', 'arch_overseer', 'cyan_fireball', 'at_ping'
    color: Tuple[int, int, int]
    accent_color: Tuple[int, int, int]
    alpha: int = 255


@dataclass
class TeleporterPad:
    radius: float = 38.0
    is_floor_exit: bool = False
    pulse: float = 0.0


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


# ============================================================================
# ENTITY PREFAB FACTORIES
# ============================================================================
def spawn_player(world: World, x: float, y: float) -> int:
    eid = world.create_entity()
    world.add_component(eid, Transform(x=x, y=y))
    world.add_component(eid, Velocity())
    world.add_component(eid, Collider(radius=16.0, layer="player"))
    world.add_component(eid, Health(hp=100, max_hp=100))
    world.add_component(eid, HumanoidAnim())
    world.add_component(eid, PlayerTag())
    world.add_component(eid, DeafenDash())
    world.add_component(
        eid,
        Visual(kind="mage", color=COLOR_EMERALD, accent_color=COLOR_CYAN, alpha=255),
    )
    return eid


def spawn_troll_warlock(world: World, x: float, y: float) -> int:
    eid = world.create_entity()
    hp_val = 95 + world.floor_num * 25
    world.add_component(eid, Transform(x=x, y=y))
    world.add_component(eid, Velocity(drag=4.0))
    world.add_component(eid, Collider(radius=20.0, layer="enemy"))
    world.add_component(eid, Health(hp=hp_val, max_hp=hp_val))
    world.add_component(eid, HumanoidAnim(walk_phase=random.uniform(0, math.tau)))
    world.add_component(
        eid,
        EnemyAI(
            kind="troll_warlock",
            speed=108.0,
            shoot_timer=random.uniform(0.4, 1.3),
            shoot_interval=max(1.0, 1.85 - world.floor_num * 0.12),
            pattern_angle=random.uniform(0, math.tau),
            pattern_variant=random.randint(0, 2),
            contact_damage=15,
            score_value=250,
        ),
    )
    world.add_component(
        eid,
        Visual(kind="troll_warlock", color=COLOR_PING_RED, accent_color=COLOR_GOLD),
    )
    return eid


def spawn_raid_thrall(world: World, x: float, y: float) -> int:
    """Spawns an agile, hunched humanoid melee berserker with twin crimson daggers."""
    eid = world.create_entity()
    hp_val = 30 + world.floor_num * 8
    world.add_component(eid, Transform(x=x, y=y))
    world.add_component(eid, Velocity(drag=2.0))
    world.add_component(eid, Collider(radius=14.0, layer="enemy"))
    world.add_component(eid, Health(hp=hp_val, max_hp=hp_val))
    world.add_component(eid, HumanoidAnim(walk_phase=random.uniform(0, math.tau)))
    world.add_component(
        eid,
        EnemyAI(
            kind="raid_thrall",
            speed=random.uniform(230.0, 275.0),
            contact_damage=12,
            score_value=80,
        ),
    )
    world.add_component(
        eid,
        Visual(kind="raid_thrall", color=COLOR_PING_RED, accent_color=COLOR_WHITE),
    )
    return eid


def spawn_arch_overseer(world: World, x: float, y: float) -> int:
    """Spawns the Sanctum Floor Guardian: a crowned humanoid Arch-Troll Lich."""
    eid = world.create_entity()
    hp_val = 380 + world.floor_num * 110
    world.add_component(eid, Transform(x=x, y=y))
    world.add_component(eid, Velocity(drag=3.0))
    world.add_component(eid, Collider(radius=28.0, layer="enemy"))
    world.add_component(eid, Health(hp=hp_val, max_hp=hp_val))
    world.add_component(eid, HumanoidAnim())
    world.add_component(
        eid,
        EnemyAI(
            kind="arch_overseer",
            speed=88.0,
            shoot_timer=0.8,
            shoot_interval=1.15,
            pattern_angle=0.0,
            pattern_variant=0,
            contact_damage=22,
            score_value=1000,
        ),
    )
    world.add_component(
        eid,
        Visual(kind="arch_overseer", color=COLOR_GOLD, accent_color=COLOR_PING_RED),
    )
    return eid


def spawn_teleporter_pad(
    world: World, x: float, y: float, is_floor_exit: bool = False
) -> int:
    eid = world.create_entity()
    world.add_component(eid, Transform(x=x, y=y))
    world.add_component(eid, TeleporterPad(radius=38.0, is_floor_exit=is_floor_exit))
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
    world.add_component(
        eid, FloatingText(text=text, ttl=0.75, max_ttl=0.75, color=color)
    )


# ============================================================================
# DUNGEON ROOM TRANSITION, TELEPORTER & RAID DIRECTOR SYSTEM
# ============================================================================
class DungeonAndRaidSystem(System):
    """Manages room transitions, teleporter network, wave clears, and Server Raids."""

    def enter_room(
        self,
        world: World,
        target_coords: Tuple[int, int],
        entry_dir: Optional[str] = None,
    ) -> None:
        # Clear transient room entities (enemies, projectiles, teleporters, particles)
        for eid, _ in world.query(EnemyAI):
            world.destroy_entity(eid)
        for eid, _ in world.query(Projectile):
            world.destroy_entity(eid)
        for eid, _ in world.query(TeleporterPad):
            world.destroy_entity(eid)
        for eid, _ in world.query(Particle):
            world.destroy_entity(eid)
        world.flush_dead_entities()

        world.current_room_coords = target_coords
        room = world.current_room
        room.visited = True
        world.transition_cooldown = 0.35
        world.raid_active = False

        # Spawn room's central Arcane Teleporter Pad
        cx, cy = SCREEN_WIDTH / 2.0, SCREEN_HEIGHT / 2.0
        spawn_teleporter_pad(world, cx, cy, is_floor_exit=False)
        if room.room_type == "SANCTUM" and room.cleared:
            spawn_teleporter_pad(world, cx, cy - 150.0, is_floor_exit=True)

        # Position Player at doorway or teleporter pad
        players = world.query(Transform, PlayerTag)
        if players:
            _, (ptf, _) = players[0]
            r = world.arena_rect
            if entry_dir == "N":
                ptf.x, ptf.y = cx, float(r.top + 52)
            elif entry_dir == "S":
                ptf.x, ptf.y = cx, float(r.bottom - 52)
            elif entry_dir == "W":
                ptf.x, ptf.y = float(r.left + 52), cy
            elif entry_dir == "E":
                ptf.x, ptf.y = float(r.right - 52), cy
            else:
                ptf.x, ptf.y = cx, cy
            spawn_burst_particles(world, ptf.x, ptf.y, COLOR_CYAN, count=20)

        # Populate Uncleared Combat / Raid / Sanctum Rooms
        if not room.cleared:
            world.room_locked = True
            if room.room_type == "COMBAT":
                troll_count = 2 + (world.floor_num // 2)
                for _ in range(troll_count):
                    sx, sy = self._safe_spawn_point(world)
                    spawn_troll_warlock(world, sx, sy)
                for _ in range(2 + world.floor_num):
                    sx, sy = self._safe_spawn_point(world)
                    spawn_raid_thrall(world, sx, sy)
                if players:
                    spawn_floating_text(
                        world,
                        players[0][1][0].x,
                        players[0][1][0].y - 38,
                        f"ENTERED {room.name.upper()} // DOORS SEALED",
                        COLOR_CYAN,
                    )

            elif room.room_type == "RAID":
                self.trigger_server_raid(world)
                for _ in range(2):
                    sx, sy = self._safe_spawn_point(world)
                    spawn_troll_warlock(world, sx, sy)

            elif room.room_type == "SANCTUM":
                spawn_arch_overseer(world, cx, cy - 130.0)
                spawn_troll_warlock(world, cx - 260.0, cy - 110.0)
                spawn_troll_warlock(world, cx + 260.0, cy - 110.0)
                if players:
                    spawn_floating_text(
                        world,
                        players[0][1][0].x,
                        players[0][1][0].y - 44,
                        "!! SANCTUM GUARDIAN: ARCH-TROLL OVERSEER !!",
                        COLOR_GOLD,
                    )
        else:
            world.room_locked = False

    def trigger_server_raid(self, world: World) -> None:
        world.raid_active = True
        world.room_locked = True
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

    def teleport_to_room(
        self, world: World, target_coords: Tuple[int, int]
    ) -> None:
        if world.room_locked or world.raid_active:
            players = world.query(Transform, PlayerTag)
            if players:
                spawn_floating_text(
                    world,
                    players[0][1][0].x,
                    players[0][1][0].y - 32,
                    "TELEPORTER JAMMED DURING COMBAT!",
                    COLOR_PING_RED,
                )
            return
        if target_coords in world.rooms and world.rooms[target_coords].visited:
            self.enter_room(world, target_coords, entry_dir=None)
            players = world.query(Transform, PlayerTag)
            if players:
                spawn_floating_text(
                    world,
                    players[0][1][0].x,
                    players[0][1][0].y - 35,
                    f"WARPED -> {world.rooms[target_coords].name.upper()}",
                    COLOR_CYAN,
                )

    def cycle_teleporter(self, world: World) -> None:
        """Cycles to the next cleared room in the procedural dungeon."""
        cleared_coords = [
            coords for coords, r in world.rooms.items() if r.cleared and r.visited
        ]
        if len(cleared_coords) <= 1:
            players = world.query(Transform, PlayerTag)
            if players:
                spawn_floating_text(
                    world,
                    players[0][1][0].x,
                    players[0][1][0].y - 32,
                    "NO OTHER TELEPORTERS LINKED YET",
                    COLOR_GOLD,
                )
            return
        idx = (
            cleared_coords.index(world.current_room_coords)
            if world.current_room_coords in cleared_coords
            else 0
        )
        next_coords = cleared_coords[(idx + 1) % len(cleared_coords)]
        self.teleport_to_room(world, next_coords)

    def advance_next_floor(self, world: World) -> None:
        world.floor_num += 1
        world.rooms = DungeonGenerator.generate_floor(world.floor_num)
        players = world.query(Health, PlayerTag)
        if players:
            _, (hp, _) = players[0]
            hp.hp = min(hp.max_hp, hp.hp + 35)
        self.enter_room(world, (0, 0), entry_dir=None)
        players_tf = world.query(Transform, PlayerTag)
        if players_tf:
            spawn_floating_text(
                world,
                players_tf[0][1][0].x,
                players_tf[0][1][0].y - 44,
                f"DESCENDED TO FLOOR 0{world.floor_num} // +35 HP RESTORED",
                COLOR_EMERALD,
            )

    def update(self, world: World, dt: float) -> None:
        if world.game_over:
            return

        world.time_elapsed += dt
        world.screen_shake = max(0.0, world.screen_shake - dt)
        world.transition_cooldown = max(0.0, world.transition_cooldown - dt)

        for _, (_, pad) in world.query(Transform, TeleporterPad):
            pad.pulse += dt * 4.0

        # Handle active Server Raid swarm spawning
        if world.raid_active:
            world.raid_timer -= dt
            world.raid_spawn_accum += dt
            spawn_interval = max(0.35, 0.72 - world.floor_num * 0.05)

            while world.raid_spawn_accum >= spawn_interval:
                world.raid_spawn_accum -= spawn_interval
                sx, sy = self._random_edge_point(world, inset=24)
                spawn_raid_thrall(world, sx, sy)
                spawn_burst_particles(world, sx, sy, COLOR_PING_RED, count=6)

            if world.raid_timer <= 0.0:
                world.raid_active = False

        # Check if room combat & raid are completely cleared
        enemies = world.query(EnemyAI)
        if world.room_locked and not world.raid_active and len(enemies) == 0:
            world.room_locked = False
            room = world.current_room
            room.cleared = True
            world.score += 200

            players = world.query(Transform, PlayerTag)
            if players:
                ptf = players[0][1][0]
                spawn_floating_text(
                    world,
                    ptf.x,
                    ptf.y - 42,
                    "ROOM CLEARED // TELEPORTER & DOORS UNLOCKED!",
                    COLOR_EMERALD,
                )
                spawn_burst_particles(
                    world,
                    SCREEN_WIDTH / 2.0,
                    SCREEN_HEIGHT / 2.0,
                    COLOR_EMERALD,
                    count=26,
                )

            if room.room_type == "SANCTUM":
                spawn_teleporter_pad(
                    world,
                    SCREEN_WIDTH / 2.0,
                    SCREEN_HEIGHT / 2.0 - 150.0,
                    is_floor_exit=True,
                )

        # Check cardinal doorway transitions when unlocked
        if not world.room_locked and world.transition_cooldown <= 0.0:
            players = world.query(Transform, PlayerTag)
            if players:
                ptf = players[0][1][0]
                door_rects = get_room_door_rects(world.arena_rect)
                for d_name, target_coords in world.current_room.doors.items():
                    if door_rects[d_name].inflate(12, 12).collidepoint(ptf.x, ptf.y):
                        self.enter_room(
                            world, target_coords, entry_dir=OPPOSITE_DIR[d_name]
                        )
                        break

    def _safe_spawn_point(self, world: World) -> Tuple[float, float]:
        r = world.arena_rect
        cx, cy = SCREEN_WIDTH / 2.0, SCREEN_HEIGHT / 2.0
        for _ in range(25):
            x = random.uniform(r.left + 65, r.right - 65)
            y = random.uniform(r.top + 65, r.bottom - 65)
            if math.hypot(x - cx, y - cy) < 170.0:
                continue
            if any(p.inflate(40, 40).collidepoint(x, y) for p in world.current_room.pillars):
                continue
            return x, y
        return float(r.left + 80), float(r.top + 80)

    def _random_edge_point(self, world: World, inset: int = 35) -> Tuple[float, float]:
        r = world.arena_rect
        side = random.randint(0, 3)
        if side == 0:
            return random.uniform(r.left + inset, r.right - inset), float(r.top + inset)
        if side == 1:
            return random.uniform(r.left + inset, r.right - inset), float(r.bottom - inset)
        if side == 2:
            return float(r.left + inset), random.uniform(r.top + inset, r.bottom - inset)
        return float(r.right - inset), random.uniform(r.top + inset, r.bottom - inset)


def get_room_door_rects(arena_rect: pygame.Rect) -> Dict[str, pygame.Rect]:
    gate_len, gate_thick = 130, 22
    cx, cy = arena_rect.centerx, arena_rect.centery
    return {
        "N": pygame.Rect(cx - gate_len // 2, arena_rect.top - 6, gate_len, gate_thick),
        "S": pygame.Rect(
            cx - gate_len // 2, arena_rect.bottom - gate_thick + 6, gate_len, gate_thick
        ),
        "W": pygame.Rect(arena_rect.left - 6, cy - gate_len // 2, gate_thick, gate_len),
        "E": pygame.Rect(
            arena_rect.right - gate_thick + 6, cy - gate_len // 2, gate_thick, gate_len
        ),
    }


# ============================================================================
# GAMEPLAY & COMBAT SYSTEMS
# ============================================================================
class InputAndPlayerSystem(System):
    """Handles WASD movement, staff aiming, cyan fireball casting, and Deafen Dash."""

    def update(self, world: World, dt: float) -> None:
        if world.game_over:
            return

        keys = pygame.key.get_pressed()
        mouse_buttons = pygame.mouse.get_pressed()
        mx, my = pygame.mouse.get_pos()

        for eid, (transform, vel, player, dash, health, visual, anim) in world.query(
            Transform, Velocity, PlayerTag, DeafenDash, Health, Visual, HumanoidAnim
        ):
            player.fire_cooldown = max(0.0, player.fire_cooldown - dt)
            dash.cooldown_timer = max(0.0, dash.cooldown_timer - dt)
            anim.cast_recoil = max(0.0, anim.cast_recoil - dt * 5.0)

            # Aim staff toward cursor
            dx_aim = mx - transform.x
            dy_aim = my - transform.y
            transform.angle = math.atan2(dy_aim, dx_aim)
            anim.facing_left = dx_aim < 0

            # WASD directional input
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
                anim.walk_phase += dt * 14.0
            else:
                anim.walk_phase = 0.0

            # Trigger "Deafen Dash" on Space or Right Click
            want_dash = keys[pygame.K_SPACE] or mouse_buttons[2]
            if want_dash and dash.cooldown_timer <= 0.0 and dash.active_timer <= 0.0:
                dash.active_timer = dash.duration
                dash.cooldown_timer = dash.cooldown
                if length > 0:
                    dash.dash_dir = (move_x, move_y)
                else:
                    dash.dash_dir = (math.cos(transform.angle), math.sin(transform.angle))
                health.iframes = max(health.iframes, dash.duration + 0.06)
                spawn_floating_text(
                    world, transform.x, transform.y - 30, "DEAFENED [PHASING]", COLOR_CYAN
                )
                spawn_burst_particles(world, transform.x, transform.y, COLOR_EMERALD, 14)

            if dash.active_timer > 0.0:
                dash.active_timer -= dt
                dash_speed = player.move_speed * dash.speed_multiplier
                vel.vx = dash.dash_dir[0] * dash_speed
                vel.vy = dash.dash_dir[1] * dash_speed
                visual.alpha = 95

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

            # Cast Cyan Fireballs from the Staff Crystal Tip (Left Mouse Button)
            if mouse_buttons[0] and player.fire_cooldown <= 0.0:
                player.fire_cooldown = player.fire_rate
                anim.cast_recoil = 1.0
                proj_speed = 690.0
                staff_tip_dist = 26.0
                sx = transform.x + math.cos(transform.angle) * staff_tip_dist
                sy = transform.y + math.sin(transform.angle) * staff_tip_dist
                spawn_projectile(
                    world,
                    sx,
                    sy,
                    math.cos(transform.angle) * proj_speed,
                    math.sin(transform.angle) * proj_speed,
                    proj_type="cyan_fireball",
                    damage=25,
                )
                spawn_burst_particles(
                    world, sx, sy, COLOR_CYAN, count=4, speed_range=(40.0, 110.0)
                )


class EnemyAISystem(System):
    """Controls humanoid Troll Warlocks, Raid Thralls, and the Arch-Troll Overseer."""

    def update(self, world: World, dt: float) -> None:
        if world.game_over:
            return

        players = world.query(Transform, PlayerTag)
        if not players:
            return
        _, (player_tf, _) = players[0]

        for eid, (tf, vel, ai, anim) in world.query(
            Transform, Velocity, EnemyAI, HumanoidAnim
        ):
            dx = player_tf.x - tf.x
            dy = player_tf.y - tf.y
            dist = math.hypot(dx, dy) or 1.0
            nx, ny = dx / dist, dy / dist
            tf.angle = math.atan2(dy, dx)
            anim.facing_left = dx < 0
            anim.walk_phase += dt * (16.0 if ai.kind == "raid_thrall" else 9.0)
            anim.cast_recoil = max(0.0, anim.cast_recoil - dt * 3.5)

            if ai.kind == "troll_warlock":
                desired_dist = 250.0
                radial_factor = max(-1.0, min(1.0, (dist - desired_dist) / 140.0))
                tx, ty = -ny, nx
                vel.vx = (nx * radial_factor + tx * 0.75) * ai.speed
                vel.vy = (ny * radial_factor + ty * 0.75) * ai.speed

                ai.shoot_timer -= dt
                if ai.shoot_timer <= 0.0:
                    ai.shoot_timer = ai.shoot_interval
                    anim.cast_recoil = 1.0
                    self._fire_warlock_pattern(world, tf, ai, tf.angle)

            elif ai.kind == "arch_overseer":
                desired_dist = 220.0
                radial_factor = max(-1.0, min(1.0, (dist - desired_dist) / 120.0))
                tx, ty = -ny, nx
                vel.vx = (nx * radial_factor + tx * 0.85) * ai.speed
                vel.vy = (ny * radial_factor + ty * 0.85) * ai.speed

                ai.shoot_timer -= dt
                if ai.shoot_timer <= 0.0:
                    ai.shoot_timer = ai.shoot_interval
                    anim.cast_recoil = 1.0
                    ai.pattern_variant = (ai.pattern_variant + 1) % 3
                    self._fire_overseer_pattern(world, tf, ai, tf.angle)

            elif ai.kind == "raid_thrall":
                vel.vx = nx * ai.speed
                vel.vy = ny * ai.speed

    def _fire_warlock_pattern(
        self, world: World, tf: Transform, ai: EnemyAI, aim_angle: float
    ) -> None:
        bullet_speed = 240.0
        if ai.pattern_variant == 0:
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
            spread = 0.20
            for layer_spd in (bullet_speed * 0.85, bullet_speed * 1.15):
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

    def _fire_overseer_pattern(
        self, world: World, tf: Transform, ai: EnemyAI, aim_angle: float
    ) -> None:
        bullet_speed = 265.0
        # Dense 14-way radial ring + aimed 3-way lance
        ai.pattern_angle += 0.28
        for i in range(14):
            ang = ai.pattern_angle + (math.tau * i / 14)
            spawn_projectile(
                world,
                tf.x,
                tf.y,
                math.cos(ang) * (bullet_speed * 0.88),
                math.sin(ang) * (bullet_speed * 0.88),
                proj_type="at_ping",
                damage=18,
                ttl=4.8,
            )
        for offset in (-0.14, 0.0, 0.14):
            ang = aim_angle + offset
            spawn_projectile(
                world,
                tf.x,
                tf.y,
                math.cos(ang) * (bullet_speed * 1.3),
                math.sin(ang) * (bullet_speed * 1.3),
                proj_type="at_ping",
                damage=18,
                ttl=4.2,
            )


class PhysicsAndCollisionSystem(System):
    """Resolves velocity, glassmorphic pillar collisions, and bullet-hell hits."""

    def update(self, world: World, dt: float) -> None:
        for eid, (tf, vel) in world.query(Transform, Velocity):
            tf.x += vel.vx * dt
            tf.y += vel.vy * dt
            if vel.drag > 0.0:
                factor = max(0.0, 1.0 - vel.drag * dt)
                vel.vx *= factor
                vel.vy *= factor

        solid_pillars = world.current_room.pillars

        for eid, (tf, col) in world.query(Transform, Collider):
            if col.layer in ("player", "enemy"):
                tf.x = max(
                    world.arena_rect.left + col.radius,
                    min(world.arena_rect.right - col.radius, tf.x),
                )
                tf.y = max(
                    world.arena_rect.top + col.radius,
                    min(world.arena_rect.bottom - col.radius, tf.y),
                )
                for rect in solid_pillars:
                    self._resolve_circle_rect(tf, col.radius, rect)

            elif col.layer in ("player_proj", "enemy_proj"):
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

        for _, (hp,) in world.query(Health):
            hp.iframes = max(0.0, hp.iframes - dt)
            hp.flash_timer = max(0.0, hp.flash_timer - dt)

        self._resolve_combat_hits(world)

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

    def _resolve_combat_hits(self, world: World) -> None:
        players = world.query(Transform, Collider, Health, PlayerTag)
        if not players:
            return
        _, (p_tf, p_col, p_hp, _) = players[0]

        enemies = world.query(Transform, Collider, Health, EnemyAI)
        projectiles = world.query(Transform, Collider, Projectile)

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
                            world, en_tf.x, en_tf.y - 22, f"-{proj.damage}", COLOR_CYAN
                        )
                        world.destroy_entity(proj_eid)

                        if en_hp.hp <= 0:
                            world.score += en_ai.score_value
                            spawn_burst_particles(
                                world,
                                en_tf.x,
                                en_tf.y,
                                COLOR_EMERALD
                                if en_ai.kind != "raid_thrall"
                                else COLOR_PING_RED,
                                count=20,
                            )
                            world.destroy_entity(en_eid)
                        break

            elif pr_col.layer == "enemy_proj" and p_hp.iframes <= 0.0:
                if math.hypot(pr_tf.x - p_tf.x, pr_tf.y - p_tf.y) <= (
                    pr_col.radius + p_col.radius
                ):
                    self._damage_player(world, p_tf, p_hp, proj.damage)
                    world.destroy_entity(proj_eid)

        if p_hp.iframes <= 0.0:
            for en_eid, (en_tf, en_col, en_hp, en_ai) in enemies:
                if math.hypot(en_tf.x - p_tf.x, en_tf.y - p_tf.y) <= (
                    en_col.radius + p_col.radius
                ):
                    self._damage_player(world, p_tf, p_hp, en_ai.contact_damage)
                    if en_ai.kind == "raid_thrall":
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
        spawn_floating_text(world, p_tf.x, p_tf.y - 26, f"-{damage} HP", COLOR_PING_RED)
        if p_hp.hp <= 0:
            world.game_over = True


# ============================================================================
# DECOUPLED RENDER SYSTEM (Humanoid Fantasy Sprites, Teleporters & Minimap)
# ============================================================================
class RenderSystem:
    """Renders articulated 3/4-perspective humanoid fantasy sprites and Arcane-Tech UI."""

    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.font_xs = pygame.font.SysFont("consolas,courier,monospace", 12, bold=True)
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
        ox, oy = 0, 0
        if world.screen_shake > 0.0:
            mag = int(world.screen_shake * 14)
            ox = random.randint(-mag, mag)
            oy = random.randint(-mag, mag)

        self.screen.fill(COLOR_BG_VOID)
        self._draw_arcane_floor(world, ox, oy)
        self._draw_teleporter_pads(world, ox, oy)

        if world.raid_active:
            pulse = (math.sin(world.time_elapsed * 7.5) + 1.0) * 0.5
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((237, 66, 69, int(18 + pulse * 36)))
            self.screen.blit(overlay, (0, 0))

        # Particles & Humanoid Phantom Afterimages
        for _, (tf, part) in world.query(Transform, Particle):
            ratio = max(0.0, part.ttl / part.max_ttl)
            px, py = int(tf.x + ox), int(tf.y + oy)
            if part.is_afterimage:
                ghost = pygame.Surface((52, 52), pygame.SRCALPHA)
                alpha = int(125 * ratio)
                # Hooded humanoid silhouette afterimage
                pygame.draw.polygon(
                    ghost,
                    (*COLOR_CYAN, alpha),
                    [(26, 6), (16, 22), (12, 44), (40, 44), (36, 22)],
                )
                pygame.draw.polygon(
                    ghost,
                    (*COLOR_EMERALD, alpha),
                    [(26, 6), (16, 22), (12, 44), (40, 44), (36, 22)],
                    width=2,
                )
                self.screen.blit(ghost, (px - 26, py - 26))
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

        # Glassmorphic Arena Walls, Pillars, and Cardinal Doors
        self._draw_glassmorphic_arena_and_doors(world, ox, oy)

        # Sort entities by Y coordinate for proper 3/4 humanoid depth overlap
        renderables = world.query(Transform, Visual)
        renderables.sort(key=lambda item: item[1][0].y)

        for eid, (tf, vis) in renderables:
            hp = world.get_component(eid, Health)
            dash = world.get_component(eid, DeafenDash)
            anim = world.get_component(eid, HumanoidAnim)
            if vis.kind == "mage":
                self._draw_humanoid_mage(world, tf, vis, hp, dash, anim, ox, oy)
            elif vis.kind == "troll_warlock":
                self._draw_humanoid_troll_warlock(world, tf, hp, anim, ox, oy)
            elif vis.kind == "raid_thrall":
                self._draw_humanoid_raid_thrall(tf, hp, anim, ox, oy)
            elif vis.kind == "arch_overseer":
                self._draw_humanoid_arch_overseer(world, tf, hp, anim, ox, oy)
            elif vis.kind == "cyan_fireball":
                self._draw_cyan_fireball(tf, ox, oy)
            elif vis.kind == "at_ping":
                self._draw_at_projectile(tf, ox, oy)

        for _, (tf, ft) in world.query(Transform, FloatingText):
            txt_surf = self.font_sm.render(ft.text, True, ft.color)
            self.screen.blit(
                txt_surf,
                (int(tf.x - txt_surf.get_width() // 2 + ox), int(tf.y + oy)),
            )

        self._draw_hud_and_minimap(world)

    def _draw_arcane_floor(self, world: World, ox: int, oy: int) -> None:
        r = world.arena_rect.move(ox, oy)
        pygame.draw.rect(self.screen, COLOR_BG_SLATE, r)

        step = 64
        for x in range(r.left, r.right, step):
            pygame.draw.line(self.screen, COLOR_BG_DARKER, (x, r.top), (x, r.bottom), 2)
        for y in range(r.top, r.bottom, step):
            pygame.draw.line(self.screen, COLOR_BG_DARKER, (r.left, y), (r.right, y), 2)

        room = world.current_room
        stamps = [
            (
                f"FLOOR_0{world.floor_num} // {room.name.upper()} [{room.room_type}]",
                r.left + 18,
                r.top + 14,
            ),
            (
                f"COORDS: ({room.coords[0]:+d}, {room.coords[1]:+d})",
                r.right - 185,
                r.top + 14,
            ),
            (
                "[E/TAB]: WARP TELEPORTER  |  CLICK MINIMAP NODE TO WARP",
                r.left + 18,
                r.bottom - 26,
            ),
            ("[SPACE/RMB]: DEAFEN_DASH", r.right - 225, r.bottom - 26),
        ]
        for text, sx, sy in stamps:
            surf = self.font_sm.render(text, True, COLOR_FLOOR_TEXT)
            self.screen.blit(surf, (sx, sy))

    def _draw_teleporter_pads(self, world: World, ox: int, oy: int) -> None:
        players = world.query(Transform, PlayerTag)
        p_tf = players[0][1][0] if players else None

        for _, (tf, pad) in world.query(Transform, TeleporterPad):
            px, py = int(tf.x + ox), int(tf.y + oy)
            active = not world.room_locked and not world.raid_active
            base_col = (
                COLOR_GOLD
                if pad.is_floor_exit
                else (COLOR_CYAN if active else COLOR_FLOOR_TEXT)
            )

            if active:
                glow = self._get_glow_surface(50, base_col)
                self.screen.blit(
                    glow, (px - 50, py - 50), special_flags=pygame.BLEND_RGB_ADD
                )

            # Rotating hexagonal arcane sigil
            hex_pts = []
            inner_pts = []
            for i in range(6):
                ang = pad.pulse * 0.4 + i * (math.tau / 6)
                hex_pts.append(
                    (px + math.cos(ang) * pad.radius, py + math.sin(ang) * pad.radius)
                )
                ang_in = -pad.pulse * 0.6 + i * (math.tau / 6)
                inner_pts.append(
                    (
                        px + math.cos(ang_in) * (pad.radius * 0.58),
                        py + math.sin(ang_in) * (pad.radius * 0.58),
                    )
                )

            pygame.draw.polygon(self.screen, COLOR_BG_DARKER, hex_pts)
            pygame.draw.polygon(self.screen, base_col, hex_pts, width=2)
            pygame.draw.polygon(self.screen, base_col, inner_pts, width=1)
            pygame.draw.circle(
                self.screen,
                COLOR_EMERALD if active else COLOR_FLOOR_TEXT,
                (px, py),
                6,
            )

            label_str = (
                "DESCEND FLOOR [E]"
                if pad.is_floor_exit
                else ("ARCANE TELEPORTER [E]" if active else "TELEPORTER OFFLINE")
            )
            if p_tf and math.hypot(p_tf.x - tf.x, p_tf.y - tf.y) <= pad.radius + 24:
                lbl = self.font_sm.render(label_str, True, base_col)
                self.screen.blit(lbl, (px - lbl.get_width() // 2, py + 44))

    def _draw_glassmorphic_arena_and_doors(
        self, world: World, ox: int, oy: int
    ) -> None:
        r = world.arena_rect.move(ox, oy)
        border_col = (
            COLOR_PING_RED
            if world.raid_active
            else (COLOR_GOLD if world.room_locked else COLOR_CYAN)
        )
        pygame.draw.rect(self.screen, border_col, r, width=2, border_radius=4)

        # Draw Internal Glassmorphic Pillars
        for pillar in world.current_room.pillars:
            brect = pillar.move(ox, oy)
            glass = pygame.Surface((brect.width, brect.height), pygame.SRCALPHA)
            glass.fill((255, 255, 255, 26))
            pygame.draw.line(
                glass,
                (0, 229, 255, 50),
                (brect.width - 10, 0),
                (0, brect.height - 10),
                width=3,
            )
            pygame.draw.rect(
                glass, (*COLOR_CYAN, 165), glass.get_rect(), width=2, border_radius=6
            )
            self.screen.blit(glass, brect.topleft)

        # Draw Cardinal Glassmorphic Doors
        door_rects = get_room_door_rects(r)
        for d_name, target_coords in world.current_room.doors.items():
            drect = door_rects[d_name]
            door_surf = pygame.Surface((drect.width, drect.height), pygame.SRCALPHA)
            if world.room_locked or world.raid_active:
                # Locked crimson glass barrier
                door_surf.fill((237, 66, 69, 95))
                pygame.draw.rect(
                    door_surf,
                    (*COLOR_PING_RED, 240),
                    door_surf.get_rect(),
                    width=2,
                    border_radius=4,
                )
            else:
                # Unlocked shimmering emerald/cyan archway
                target_room = world.rooms[target_coords]
                tint = (
                    COLOR_GOLD
                    if target_room.room_type == "SANCTUM"
                    else (COLOR_EMERALD if target_room.cleared else COLOR_CYAN)
                )
                door_surf.fill((*tint, 55))
                pygame.draw.rect(
                    door_surf, (*tint, 230), door_surf.get_rect(), width=2, border_radius=4
                )
            self.screen.blit(door_surf, drect.topleft)

    # ------------------------------------------------------------------------
    # HUMANOID FANTASY SPRITE RENDERING (3/4 Top-Down Perspective)
    # ------------------------------------------------------------------------
    def _draw_humanoid_mage(
        self,
        world: World,
        tf: Transform,
        vis: Visual,
        hp: Optional[Health],
        dash: Optional[DeafenDash],
        anim: Optional[HumanoidAnim],
        ox: int,
        oy: int,
    ) -> None:
        px, py = int(tf.x + ox), int(tf.y + oy)
        glow = self._get_glow_surface(32, COLOR_EMERALD)
        self.screen.blit(
            glow, (px - 32, py - 32), special_flags=pygame.BLEND_RGB_ADD
        )

        surf = pygame.Surface((84, 84), pygame.SRCALPHA)
        cx, cy = 42, 44
        alpha = vis.alpha
        walk = anim.walk_phase if anim else 0.0
        recoil = anim.cast_recoil if anim else 0.0

        # 1. Ground Shadow
        pygame.draw.ellipse(surf, (15, 17, 20, alpha // 2), (cx - 14, cy + 12, 28, 10))

        # 2. Animated Walking Boots
        foot_l_y = cy + 13 + int(math.sin(walk) * 4)
        foot_r_y = cy + 13 - int(math.sin(walk) * 4)
        pygame.draw.circle(surf, (30, 35, 42, alpha), (cx - 6, foot_l_y), 4)
        pygame.draw.circle(surf, (30, 35, 42, alpha), (cx + 6, foot_r_y), 4)

        # 3. Flowing Emerald Wizard Robe & Mantle (Trapezoidal Cloak)
        is_flashing = hp and hp.flash_timer > 0
        robe_fill = (*COLOR_WHITE, alpha) if is_flashing else (*COLOR_EMERALD_DARK, alpha)
        robe_shadow = (*COLOR_EMERALD_DEEP, alpha)
        trim_col = (*COLOR_EMERALD, alpha)

        robe_poly = [
            (cx - 9, cy - 6),
            (cx + 9, cy - 6),
            (cx + 14, cy + 13),
            (cx - 14, cy + 13),
        ]
        pygame.draw.polygon(surf, robe_fill, robe_poly)
        pygame.draw.polygon(surf, trim_col, robe_poly, width=2)
        # Golden Arcane Sash / Belt
        pygame.draw.line(
            surf, (*COLOR_GOLD, alpha), (cx - 10, cy + 3), (cx + 10, cy + 3), 2
        )
        # Shoulder Pauldrons
        pygame.draw.circle(surf, robe_shadow, (cx - 10, cy - 4), 5)
        pygame.draw.circle(surf, robe_shadow, (cx + 10, cy - 4), 5)
        pygame.draw.circle(surf, trim_col, (cx - 10, cy - 4), 5, width=1)
        pygame.draw.circle(surf, trim_col, (cx + 10, cy - 4), 5, width=1)

        # 4. Pointed Fantasy Wizard Hood & Shadowed Face with Glowing Cyan Eyes
        hood_sway = int(math.sin(walk * 0.5) * 2)
        hood_poly = [
            (cx + hood_sway, cy - 26),  # Tall pointed wizard hat/hood apex
            (cx - 12, cy - 11),
            (cx - 10, cy - 2),
            (cx + 10, cy - 2),
            (cx + 12, cy - 11),
        ]
        pygame.draw.polygon(surf, robe_fill, hood_poly)
        pygame.draw.polygon(surf, trim_col, hood_poly, width=2)

        # Dark Face Cavity under Hood
        pygame.draw.ellipse(surf, (16, 18, 22, alpha), (cx - 7, cy - 13, 14, 10))
        # Glowing Cyan Eyes looking slightly toward aim angle
        look_x = int(math.cos(tf.angle) * 2.2)
        look_y = int(math.sin(tf.angle) * 1.5)
        pygame.draw.circle(
            surf, (*COLOR_CYAN, alpha), (cx - 3 + look_x, cy - 8 + look_y), 2
        )
        pygame.draw.circle(
            surf, (*COLOR_CYAN, alpha), (cx + 3 + look_x, cy - 8 + look_y), 2
        )

        # 5. Off-Hand Floating Arcane Grimoire (Spellbook)
        book_ang = tf.angle + math.pi * 0.65
        bx = int(cx + math.cos(book_ang) * 16)
        by = int(cy + math.sin(book_ang) * 12 + math.sin(world.time_elapsed * 6.0) * 2)
        pygame.draw.rect(surf, (*COLOR_EMERALD_DEEP, alpha), (bx - 5, by - 6, 10, 12), border_radius=2)
        pygame.draw.rect(surf, (*COLOR_GOLD, alpha), (bx - 5, by - 6, 10, 12), width=1, border_radius=2)
        pygame.draw.line(surf, (*COLOR_CYAN, alpha), (bx, by - 4), (bx, by + 4), 1)

        # 6. Main-Hand Articulated Arm & Crystal-Tipped Arcane Staff
        ca, sa = math.cos(tf.angle), math.sin(tf.angle)
        hand_dist = 12.0 - recoil * 4.0
        hx = cx + ca * hand_dist
        hy = cy - 2 + sa * hand_dist
        # Staff shaft
        staff_back = (int(hx - ca * 10), int(hy - sa * 10))
        staff_tip = (int(hx + ca * 18), int(hy + sa * 18))
        pygame.draw.line(surf, (*COLOR_STAFF_WOOD, alpha), staff_back, staff_tip, 3)
        # Mage Hand gripping staff
        pygame.draw.circle(surf, (*COLOR_EMERALD, alpha), (int(hx), int(hy)), 3)
        # Glowing Cyan Head Crystal on Staff Tip
        pygame.draw.circle(surf, (*COLOR_CYAN, alpha), staff_tip, 6)
        pygame.draw.circle(surf, (*COLOR_WHITE, alpha), staff_tip, 3)

        self.screen.blit(surf, (px - cx, py - cy))

        # Deafened Headset Icon during Dash
        if dash and dash.active_timer > 0.0:
            hx_i, hy_i = px, py - 36
            pygame.draw.arc(
                self.screen,
                COLOR_CYAN,
                pygame.Rect(hx_i - 8, hy_i - 8, 16, 14),
                0,
                math.pi,
                2,
            )
            pygame.draw.line(
                self.screen, COLOR_PING_RED, (hx_i - 9, hy_i - 8), (hx_i + 9, hy_i + 6), 2
            )

    def _draw_humanoid_troll_warlock(
        self,
        world: World,
        tf: Transform,
        hp: Optional[Health],
        anim: Optional[HumanoidAnim],
        ox: int,
        oy: int,
    ) -> None:
        px, py = int(tf.x + ox), int(tf.y + oy)
        glow = self._get_glow_surface(30, COLOR_PING_RED)
        self.screen.blit(
            glow, (px - 30, py - 30), special_flags=pygame.BLEND_RGB_ADD
        )

        walk = anim.walk_phase if anim else 0.0
        recoil = anim.cast_recoil if anim else 0.0
        bob = int(math.sin(walk) * 2.5)
        is_flash = hp and hp.flash_timer > 0

        # Shadow
        pygame.draw.ellipse(self.screen, (18, 20, 24), (px - 15, py + 15, 30, 10))

        # Tattered Dark-Crimson Cultist Robe & Spiked Pauldrons
        robe_col = COLOR_WHITE if is_flash else COLOR_CRIMSON_DARK
        robe_pts = [
            (px - 11, py - 6 + bob),
            (px + 11, py - 6 + bob),
            (px + 16, py + 17 + bob),
            (px + 6, py + 14 + bob),
            (px, py + 18 + bob),
            (px - 6, py + 14 + bob),
            (px - 16, py + 17 + bob),
        ]
        pygame.draw.polygon(self.screen, robe_col, robe_pts)
        pygame.draw.polygon(self.screen, COLOR_PING_RED, robe_pts, width=2)

        # Spiked Warlock Pauldrons
        pygame.draw.polygon(
            self.screen,
             (40, 43, 48),
            [(px - 10, py - 7 + bob), (px - 20, py - 12 + bob), (px - 15, py + 1 + bob)],
        )
        pygame.draw.polygon(
            self.screen,
            (40, 43, 48),
            [(px + 10, py - 7 + bob), (px + 20, py - 12 + bob), (px + 15, py + 1 + bob)],
        )

        # Horned Troll Mask Head
        hy = py - 13 + bob
        pygame.draw.polygon(
            self.screen,
            COLOR_GOLD,
            [(px - 9, hy - 5), (px - 17, hy - 18), (px - 4, hy - 9)],
        )
        pygame.draw.polygon(
            self.screen,
            COLOR_GOLD,
            [(px + 9, hy - 5), (px + 17, hy - 18), (px + 4, hy - 9)],
        )
        mask_pts = [
            (px, hy - 11),
            (px + 11, hy - 4),
            (px + 9, hy + 9),
            (px, hy + 13),
            (px - 9, hy + 9),
            (px - 11, hy - 4),
        ]
        pygame.draw.polygon(
            self.screen, COLOR_WHITE if is_flash else (36, 38, 44), mask_pts
        )
        pygame.draw.polygon(self.screen, COLOR_PING_RED, mask_pts, width=2)
        # Glowing Crimson Eyes & Jagged Grin
        pygame.draw.circle(self.screen, COLOR_PING_RED, (px - 4, hy - 1), 2)
        pygame.draw.circle(self.screen, COLOR_PING_RED, (px + 4, hy - 1), 2)
        pygame.draw.arc(
            self.screen,
            COLOR_GOLD,
            pygame.Rect(px - 6, hy + 1, 12, 7),
            math.pi,
            math.tau,
            2,
        )

        # Levitating Ritual Casting Hands
        hand_spread = 16.0 + recoil * 5.0
        for side in (-1, 1):
            hx = int(px + side * hand_spread + math.cos(tf.angle) * 5)
            h_y = int(py + 2 + math.sin(walk + side) * 3)
            pygame.draw.circle(self.screen, COLOR_PING_RED, (hx, h_y), 5)
            pygame.draw.circle(self.screen, COLOR_WHITE, (hx, h_y), 2)

        if hp and hp.hp < hp.max_hp:
            bw = 36
            ratio = max(0.0, hp.hp / hp.max_hp)
            pygame.draw.rect(
                self.screen, COLOR_BG_DARKER, (px - bw // 2, py - 36, bw, 4)
            )
            pygame.draw.rect(
                self.screen,
                COLOR_PING_RED,
                (px - bw // 2, py - 36, int(bw * ratio), 4),
            )

    def _draw_humanoid_raid_thrall(
        self,
        tf: Transform,
        hp: Optional[Health],
        anim: Optional[HumanoidAnim],
        ox: int,
        oy: int,
    ) -> None:
        """Draws a hunched, fast-sprinting humanoid rogue-imp with twin crimson daggers."""
        px, py = int(tf.x + ox), int(tf.y + oy)
        walk = anim.walk_phase if anim else 0.0
        is_flash = hp and hp.flash_timer > 0

        # Sprinting Feet
        fl = int(math.sin(walk) * 5)
        pygame.draw.circle(self.screen, (25, 27, 30), (px - 5, py + 10 + fl), 3)
        pygame.draw.circle(self.screen, (25, 27, 30), (px + 5, py + 10 - fl), 3)

        # Hunched Rogue Tunic & Jagged Hood
        body_col = COLOR_WHITE if is_flash else (68, 24, 30)
        pygame.draw.polygon(
            self.screen,
            body_col,
            [(px - 8, py - 3), (px + 8, py - 3), (px + 10, py + 9), (px - 10, py + 9)],
        )
        pygame.draw.polygon(
            self.screen,
            COLOR_PING_RED,
            [(px, py - 16), (px - 9, py - 3), (px + 9, py - 3)],
        )
        # Glowing Eyes
        pygame.draw.circle(self.screen, COLOR_WHITE, (px - 3, py - 6), 2)
        pygame.draw.circle(self.screen, COLOR_WHITE, (px + 3, py - 6), 2)

        # Twin Crimson Energy Daggers thrusting toward player
        ca, sa = math.cos(tf.angle), math.sin(tf.angle)
        px_perp, py_perp = -sa * 8, ca * 8
        for side in (-1, 1):
            bx = px + side * px_perp + ca * 4
            by = py + side * py_perp + sa * 4
            tip_x = bx + ca * 13
            tip_y = by + sa * 13
            pygame.draw.line(
                self.screen, COLOR_PING_RED, (int(bx), int(by)), (int(tip_x), int(tip_y)), 3
            )
            pygame.draw.line(
                self.screen, COLOR_WHITE, (int(bx), int(by)), (int(tip_x), int(tip_y)), 1
            )

    def _draw_humanoid_arch_overseer(
        self,
        world: World,
        tf: Transform,
        hp: Optional[Health],
        anim: Optional[HumanoidAnim],
        ox: int,
        oy: int,
    ) -> None:
        """Draws the Sanctum Boss: a towering crowned humanoid Arch-Troll Lich."""
        px, py = int(tf.x + ox), int(tf.y + oy)
        glow = self._get_glow_surface(46, COLOR_GOLD)
        self.screen.blit(
            glow, (px - 46, py - 46), special_flags=pygame.BLEND_RGB_ADD
        )

        walk = anim.walk_phase if anim else 0.0
        bob = int(math.sin(walk) * 3)
        is_flash = hp and hp.flash_timer > 0

        # Royal Obsidian & Crimson Robes
        robe_col = COLOR_WHITE if is_flash else (38, 18, 26)
        robe_pts = [
            (px - 16, py - 10 + bob),
            (px + 16, py - 10 + bob),
            (px + 24, py + 24 + bob),
            (px - 24, py + 24 + bob),
        ]
        pygame.draw.polygon(self.screen, robe_col, robe_pts)
        pygame.draw.polygon(self.screen, COLOR_GOLD, robe_pts, width=2)

        # Golden Pauldrons
        pygame.draw.circle(self.screen, COLOR_GOLD, (px - 18, py - 7 + bob), 7)
        pygame.draw.circle(self.screen, COLOR_GOLD, (px + 18, py - 7 + bob), 7)

        # Horned Mask & Levitating Golden Crown
        hy = py - 18 + bob
        pygame.draw.polygon(
            self.screen,
            (30, 32, 38),
            [
                (px, hy - 14),
                (px + 14, hy - 4),
                (px + 11, hy + 11),
                (px, hy + 15),
                (px - 11, hy + 11),
                (px - 14, hy - 4),
            ],
        )
        pygame.draw.polygon(
            self.screen,
            COLOR_GOLD,
            [
                (px - 10, hy - 15),
                (px - 12, hy - 25),
                (px - 5, hy - 19),
                (px, hy - 28),
                (px + 5, hy - 19),
                (px + 12, hy - 25),
                (px + 10, hy - 15),
            ],
        )
        pygame.draw.circle(self.screen, COLOR_PING_RED, (px - 5, hy - 1), 3)
        pygame.draw.circle(self.screen, COLOR_PING_RED, (px + 5, hy - 1), 3)

        # Twin Levitating Arcane Scepters
        for side in (-1, 1):
            sx = px + side * 26
            sy = py + bob
            pygame.draw.line(self.screen, COLOR_GOLD, (sx, sy - 16), (sx, sy + 14), 3)
            pygame.draw.circle(self.screen, COLOR_PING_RED, (sx, sy - 18), 6)
            pygame.draw.circle(self.screen, COLOR_WHITE, (sx, sy - 18), 2)

        if hp:
            bw = 64
            ratio = max(0.0, hp.hp / hp.max_hp)
            pygame.draw.rect(
                self.screen, COLOR_BG_DARKER, (px - bw // 2, py - 52, bw, 6)
            )
            pygame.draw.rect(
                self.screen, COLOR_GOLD, (px - bw // 2, py - 52, int(bw * ratio), 6)
            )

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

    # ------------------------------------------------------------------------
    # HUD & INTERACTIVE TELEPORTER MINIMAP
    # ------------------------------------------------------------------------
    def _draw_hud_and_minimap(self, world: World) -> None:
        hud_bar = pygame.Surface((SCREEN_WIDTH - ARENA_MARGIN * 2, 48), pygame.SRCALPHA)
        hud_bar.fill((32, 34, 37, 220))
        pygame.draw.rect(
            hud_bar, (*COLOR_EMERALD, 160), hud_bar.get_rect(), width=1, border_radius=6
        )
        self.screen.blit(hud_bar, (ARENA_MARGIN, 12))

        players = world.query(Health, DeafenDash, PlayerTag)
        if players:
            _, (hp, dash, _) = players[0]
            hp_ratio = max(0.0, hp.hp / hp.max_hp)
            pygame.draw.rect(
                self.screen, COLOR_BG_SLATE, (ARENA_MARGIN + 14, 24, 175, 22), border_radius=4
            )
            pygame.draw.rect(
                self.screen,
                COLOR_EMERALD if hp_ratio > 0.3 else COLOR_PING_RED,
                (ARENA_MARGIN + 14, 24, int(175 * hp_ratio), 22),
                border_radius=4,
            )
            hp_txt = self.font_sm.render(f"MAGE_HP: {hp.hp}/{hp.max_hp}", True, COLOR_WHITE)
            self.screen.blit(hp_txt, (ARENA_MARGIN + 22, 27))

            dash_ready = dash.cooldown_timer <= 0.0
            dash_col = COLOR_CYAN if dash_ready else COLOR_FLOOR_TEXT
            dash_str = (
                "DEAFEN_DASH: READY"
                if dash_ready
                else f"DEAFEN_DASH: {dash.cooldown_timer:.1f}s"
            )
            self.screen.blit(
                self.font_sm.render(dash_str, True, dash_col), (ARENA_MARGIN + 205, 27)
            )

        status_str = (
            f"FLOOR: 0{world.floor_num}  |  ROOM: {world.current_room.name}  "
            f"|  SCORE: {world.score:05d}  |  [F]: RAID"
        )
        status_surf = self.font_sm.render(status_str, True, COLOR_EMERALD)
        self.screen.blit(
            status_surf,
            (SCREEN_WIDTH - ARENA_MARGIN - status_surf.get_width() - 16, 27),
        )

        # Interactive Procedural Dungeon Minimap Panel (Top-Right inside Arena)
        self._draw_minimap(world)

        if world.raid_active:
            banner = self.font_md.render(
                f"⚠ SERVER RAID LOCKDOWN ACTIVE ({world.raid_timer:.1f}s) ⚠",
                True,
                COLOR_PING_RED,
            )
            self.screen.blit(
                banner, (SCREEN_WIDTH // 2 - banner.get_width() // 2, ARENA_MARGIN + 14)
            )

        if world.game_over:
            over_glass = pygame.Surface((540, 175), pygame.SRCALPHA)
            over_glass.fill((24, 25, 28, 238))
            pygame.draw.rect(
                over_glass, COLOR_PING_RED, over_glass.get_rect(), width=2, border_radius=8
            )
            bx, by = SCREEN_WIDTH // 2 - 270, SCREEN_HEIGHT // 2 - 88
            self.screen.blit(over_glass, (bx, by))

            t1 = self.font_lg.render("CONNECTION TERMINATED", True, COLOR_PING_RED)
            t2 = self.font_md.render(
                f"SCORE: {world.score} // REACHED FLOOR 0{world.floor_num}",
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
            self.screen.blit(t3, (SCREEN_WIDTH // 2 - t3.get_width() // 2, by + 124))

    def _draw_minimap(self, world: World) -> None:
        map_w, map_h = 195, 145
        mx = SCREEN_WIDTH - ARENA_MARGIN - map_w - 14
        my = ARENA_MARGIN + 38

        panel = pygame.Surface((map_w, map_h), pygame.SRCALPHA)
        panel.fill((24, 26, 30, 195))
        pygame.draw.rect(
            panel, (*COLOR_CYAN, 150), panel.get_rect(), width=1, border_radius=6
        )
        self.screen.blit(panel, (mx, my))

        hdr = self.font_xs.render("DUNGEON MAP (CLICK TO WARP)", True, COLOR_CYAN)
        self.screen.blit(hdr, (mx + 8, my + 5))

        center_x = mx + map_w // 2
        center_y = my + map_h // 2 + 8
        cur_x, cur_y = world.current_room_coords
        cell_step = 26
        node_size = 18

        world.minimap_rects.clear()

        for (rx, ry), room in world.rooms.items():
            # Show visited rooms or rooms directly connected to visited rooms
            is_known = room.visited or any(
                world.rooms[nb].visited for nb in room.doors.values()
            )
            if not is_known:
                continue

            nx = center_x + (rx - cur_x) * cell_step
            ny = center_y + (ry - cur_y) * cell_step
            node_rect = pygame.Rect(
                nx - node_size // 2, ny - node_size // 2, node_size, node_size
            )
            if not pygame.Rect(mx + 6, my + 20, map_w - 12, map_h - 26).contains(
                node_rect
            ):
                continue

            # Draw corridor links
            for _, nb_coords in room.doors.items():
                nbx = center_x + (nb_coords[0] - cur_x) * cell_step
                nby = center_y + (nb_coords[1] - cur_y) * cell_step
                pygame.draw.line(self.screen, COLOR_FLOOR_TEXT, (nx, ny), (nbx, nby), 2)

            if (rx, ry) == world.current_room_coords:
                fill_col = COLOR_CYAN
            elif room.room_type == "SANCTUM":
                fill_col = COLOR_GOLD
            elif room.room_type == "RAID" and not room.cleared:
                fill_col = COLOR_PING_RED
            elif room.cleared:
                fill_col = COLOR_EMERALD
            else:
                fill_col = COLOR_FLOOR_TEXT

            pygame.draw.rect(self.screen, fill_col, node_rect, border_radius=3)
            pygame.draw.rect(self.screen, COLOR_WHITE, node_rect, width=1, border_radius=3)
            world.minimap_rects[(rx, ry)] = node_rect


# ============================================================================
# ENGINE BOOTSTRAP & MAIN LOOP
# ============================================================================
def create_game_world() -> Tuple[World, DungeonAndRaidSystem]:
    world = World()
    dungeon_sys = DungeonAndRaidSystem()

    world.add_system(InputAndPlayerSystem())
    world.add_system(EnemyAISystem())
    world.add_system(dungeon_sys)
    world.add_system(PhysicsAndCollisionSystem())

    spawn_player(world, SCREEN_WIDTH / 2.0, SCREEN_HEIGHT / 2.0)
    dungeon_sys.enter_room(world, (0, 0), entry_dir=None)

    return world, dungeon_sys


def handle_interaction_key(world: World, dungeon_sys: DungeonAndRaidSystem) -> None:
    """Handles [E] / [TAB] teleporter activation and floor descent portals."""
    players = world.query(Transform, PlayerTag)
    if not players:
        return
    p_tf = players[0][1][0]

    for _, (pad_tf, pad) in world.query(Transform, TeleporterPad):
        if math.hypot(p_tf.x - pad_tf.x, p_tf.y - pad_tf.y) <= pad.radius + 28:
            if pad.is_floor_exit and not world.room_locked:
                dungeon_sys.advance_next_floor(world)
                return
            dungeon_sys.cycle_teleporter(world)
            return

    # Even if not standing directly on the center pad, allow cycling teleporters when room is clear
    dungeon_sys.cycle_teleporter(world)


def main() -> None:
    pygame.init()
    pygame.display.set_caption(
        "DragunWF's Castle // Procedural Arcane-Tech Roguelite"
    )
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    world, dungeon_sys = create_game_world()
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
                    world, dungeon_sys = create_game_world()
                elif event.key == pygame.K_f and not world.game_over:
                    dungeon_sys.trigger_server_raid(world)
                elif event.key in (pygame.K_e, pygame.K_TAB) and not world.game_over:
                    handle_interaction_key(world, dungeon_sys)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not world.game_over:
                    mx, my = event.pos
                    for coords, rect in world.minimap_rects.items():
                        if rect.collidepoint(mx, my):
                            dungeon_sys.teleport_to_room(world, coords)
                            break

        world.update(dt)
        renderer.render(world)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()