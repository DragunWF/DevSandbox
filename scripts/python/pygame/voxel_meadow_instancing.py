#!/usr/bin/env python3
"""
Voxel Meadow Instancing: Arcane Tech Edition
  + Arcane Staff & Plasma Bolts
  + Procedural Sky & Emerald Sun
  + Destructible Slate Monoliths (fragment-shader holes)
  + Hostile Violet-Core Constructs that SHATTER into tumbling debris
  + Seamless F11 Fullscreen toggle (viewport + projection rebuilt)
  + TRUE infinite 360-degree FPS mouse-look (relative mouse, unbounded yaw, clamped pitch)
  + NEW: Procedural "Cozy House" (slate walls, sheened roof, glowing amber windows)
  + NEW: Solar-Amber Artillery Constructs whose shots BOUNCE harmlessly off the player
=============================================================================
Dependencies:  pip install pygame moderngl numpy      (pygame 2.x or pygame-ce)

Controls:
    W/A/S/D      move (on the ground plane, relative to where you look)
    Mouse        look around (cursor hidden + locked, unlimited turning)
    Left click   cast an Arcane Plasma Bolt from the staff
    Space / Ctrl move up / down
    Shift        sprint
    F11          toggle fullscreen / windowed
    Esc          quit

Render passes per frame:
    0. Sky + sun                        (full-screen triangle, depth test OFF, drawn first)
    1. Ground plane                     (opaque; also receives the amber window-light pool)
    2. Slate monoliths (trees)          (ONE instanced draw call, fragment-shader `discard` holes)
    3. Cozy house                       (ONE draw call, composite static mesh, 4 part types)
    4. Constructs + debris              (TWO instanced draw calls: cube parts, shard parts)
    5. Grass meadow                     (ONE instanced draw call, 60k blades)
    6. Plasma bolts + enemy shots       (two instanced draw calls, additive blend, spherical billboards)
    7. Staff view-model                 (separate pass: static "view space" matrix, locked to the camera)
    8. Crosshair                        (additive 2D overlay)

Everything (geometry, colours, noise, sky, physics) is generated procedurally.
"""

import math
import numpy as np
import pygame
import moderngl

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------
WIDTH, HEIGHT = 800, 600      # initial WINDOWED size (fullscreen uses the desktop size)
FOV_Y_DEG = 70.0
BLADE_COUNT = 60_000          # number of instanced grass blades
MEADOW_HALF_SIZE = 32.0       # meadow spans [-32, 32] on X and Z
GROUND_HALF_SIZE = 120.0      # ground plane is bigger than the meadow (fog hides the edge)
MOVE_SPEED = 6.0

# --- Mouse look ---
# Angles are stored in DEGREES, so the sensitivity is "degrees of rotation per
# pixel of mouse movement". 0.12 deg/px  ->  about 3000 px of mouse travel per full turn.
MOUSE_SENSITIVITY = 0.12
PITCH_LIMIT_DEG = 89.0        # look straight up/down, but never quite 90 (that would flip the camera)

# --- Projectile settings (player) ---
BOLT_SPEED = 30.0             # world units per second
BOLT_LIFESPAN = 4.5           # seconds before a bolt dissipates
MAX_FIREBALLS = 64            # capacity of the dynamic instance buffer
MAX_BOLT_LIGHTS = 16          # how many bolts can disturb/light the grass at once
STAFF_CRYSTAL_TIP = (0.0, 0.92, 0.0)   # staff-local point where bolts are born

# --- Tree / destruction settings ---
TREE_COUNT = 40               # number of instanced monoliths
MAX_HIT_POINTS = 48           # size of the `uniform vec3 hit_points[]` array (oldest overwritten)
HOLE_RADIUS = 0.50            # world-space radius of every blasted hole
CARVE_EXIT_HOLE = True        # also punch a hole where the bolt WOULD have left the pillar

# --- Melee creature settings ---
CREATURE_COUNT = 8            # how many violet constructs roam the meadow at once
CREATURE_HOVER = 1.55         # hover height of a creature's centre
CREATURE_SPEED = 1.3          # wander speed (units / second)
CREATURE_HALF = np.array([0.90, 0.90, 0.90])    # AABB half extents below / sideways of the centre
CREATURE_TOP = 1.05                              # AABB reaches a bit higher (the top spike)
RESPAWN_DELAY = 5.0           # seconds until a destroyed creature is replaced
MAX_DEBRIS = 200              # cap on tumbling pieces (oldest are recycled)
MAX_PART_INSTANCES = 512      # capacity of each per-mesh dynamic instance buffer

# --- Artillery constructs + enemy projectiles ---
ARTILLERY_COUNT = 3           # how many amber ranged constructs are alive at once
ARTILLERY_HOVER = 2.0         # they hover a little higher than the melee constructs
ARTILLERY_RANGE = 26.0        # they only fire when the player is closer than this
ARTILLERY_COOLDOWN = (2.2, 3.6)   # random seconds between shots
ARTILLERY_TURN_RATE = 1.8     # rad/s: how fast they swivel to face the player
ENEMY_SHOT_SPEED = 13.0       # slow enough that a moving player can dodge
ENEMY_SHOT_RADIUS = 0.22      # collision radius of an enemy projectile
ENEMY_SHOT_LIFE = 6.0         # seconds a shot lives if it hits nothing
MAX_ENEMY_SHOTS = 48          # capacity of the enemy-shot instance buffer
PLAYER_RADIUS = 0.75          # the player is a sphere of this radius around the camera

# --- Cozy house (all dimensions in world units) ---
HOUSE_CENTER = (-9.0, -3.0)   # (x, z) of the house centre; its base sits on y = 0
HOUSE_HALF = (2.6, 2.0)       # half-width along X, half-depth along Z
HOUSE_WALL_H = 2.8            # wall height
HOUSE_ROOF_H = 1.7            # height of the roof ridge above the eaves
HOUSE_OVERHANG = 0.45         # how far the roof sticks out past the walls

# --- Ragdoll / kinematic debris physics ---
GRAVITY = -18.0               # m/s^2 (a bit stronger than real, feels snappier / heavier)
RESTITUTION = 0.42            # fraction of vertical speed kept after a bounce
FLOOR_FRICTION = 0.70         # fraction of horizontal speed kept per bounce
BOUNCE_MIN_SPEED = 1.5        # slower impacts do not bounce, they just stick to the floor
UP = np.array([0.0, 1.0, 0.0])

# --- Sky ---
SUN_DIR = np.array([0.35, 0.22, -0.90], dtype=np.float32)
SUN_DIR /= np.linalg.norm(SUN_DIR)

# Colour of the distant haze. The sky shader uses EXACTLY this colour at the
# horizon and every object fades into it, so the ground melts seamlessly into the sky.
FOG_COLOR_GLSL = "vec3(0.015, 0.20, 0.25)"


def prep(src):
    """Inject shared constants into a GLSL source string."""
    return (src.replace("__FOG_COLOR__", FOG_COLOR_GLSL)
               .replace("__MAX_BOLTS__", str(MAX_BOLT_LIGHTS))
               .replace("__MAX_HITS__", str(MAX_HIT_POINTS)))


# ----------------------------------------------------------------------------
# GLSL: Sky shaders (full-screen triangle, view-direction gradient + sun)
# ----------------------------------------------------------------------------
SKY_VERTEX_SHADER = """
#version 330 core
in vec2 in_pos;          // one big triangle covering the whole screen in NDC
out vec2 v_ndc;
void main() {
    v_ndc = in_pos;
    // z = w  ->  depth = 1.0 (the far plane). The sky is also drawn with the
    // depth test disabled, so it never occludes anything.
    gl_Position = vec4(in_pos, 1.0, 1.0);
}
"""

SKY_FRAGMENT_SHADER = """
#version 330 core
in vec2 v_ndc;

uniform vec3  u_cam_right;      // camera basis in WORLD space
uniform vec3  u_cam_up;
uniform vec3  u_cam_fwd;
uniform float u_tan_half_fov;   // tan(fov_y / 2)
uniform float u_aspect;         // width / height  (updated whenever the window resizes)
uniform vec3  u_sun_dir;        // static, normalised
uniform float u_time;

out vec4 fragColor;

void main() {
    // ---------------- Per-pixel VIEW DIRECTION ----------------
    // A pixel at normalised device coords (x, y) in [-1,1] looks along:
    //     forward + right * (x * aspect * tan(fov/2)) + up * (y * tan(fov/2))
    // This is the inverse of the perspective projection, expressed with the
    // camera's world-space basis, so `dir` is a world-space direction and the
    // sky stays glued to the world as you look around.
    vec3 dir = normalize(u_cam_fwd
                       + u_cam_right * (v_ndc.x * u_aspect * u_tan_half_fov)
                       + u_cam_up    * (v_ndc.y * u_tan_half_fov));

    // ---------------- Gradient on the Y axis ----------------
    float h = max(dir.y, 0.0);
    vec3 zenith  = vec3(0.004, 0.008, 0.016);
    vec3 horizon = __FOG_COLOR__;
    float blend  = 1.0 - exp(-h * 4.2);              // fast rise near the horizon, long soft tail
    vec3 sky = mix(horizon, zenith, blend);

    // ---------------- Sun ----------------
    float d   = dot(dir, u_sun_dir);
    float ang = acos(clamp(d, -1.0, 1.0));

    vec3  sr = normalize(cross(u_sun_dir, vec3(0.0, 1.0, 0.0)));
    vec3  su = cross(sr, u_sun_dir);
    float around = atan(dot(dir, su), dot(dir, sr));

    float disc = 1.0 - smoothstep(0.030, 0.034, ang);

    float swirl = 0.5 + 0.5 * sin(around * 5.0 + ang * 170.0 - u_time * 2.0);
    vec3  disc_col = mix(vec3(0.05, 1.00, 0.50), vec3(0.00, 0.90, 1.00), swirl * 0.7);
    disc_col = mix(disc_col, vec3(0.85, 1.0, 0.95), (1.0 - smoothstep(0.0, 0.030, ang)) * 0.85);
    disc_col *= 1.6;                                  // overexposed: "blinding"

    float halo_tight = exp(-ang * 16.0);
    float halo_wide  = exp(-ang * 4.0);
    float rays = pow(0.5 + 0.5 * sin(around * 14.0 + u_time * 0.35), 3.0) * exp(-ang * 6.0);

    sky += vec3(0.05, 0.95, 0.60) * halo_tight * 0.85;
    sky += vec3(0.00, 0.55, 0.65) * halo_wide  * 0.45;
    sky += vec3(0.20, 1.00, 0.85) * rays * 0.22;
    sky  = mix(sky, disc_col, disc);

    fragColor = vec4(sky, 1.0);
}
"""

# ----------------------------------------------------------------------------
# GLSL: Grass shaders (meadow + reaction to plasma bolts)
# ----------------------------------------------------------------------------
GRASS_VERTEX_SHADER = """
#version 330 core

// ---- Per-VERTEX attributes (the shared blade mesh; divisor = 0) ----
// x : horizontal offset across the blade, in [-0.5, 0.5]
// y : height fraction, 0 at the root and 1 at the tip
// z : unused (kept as vec3 so the mesh could be extended to 3D blades)
in vec3 in_vert;

// ---- Per-INSTANCE attributes (one value per blade; divisor = 1) ----
// xyz : world-space root position of this blade
// w   : random seed in [0,1], used for height/width/colour variation
in vec4 in_offset;

uniform mat4  u_mvp;        // projection * view (model is identity: offsets are already world space)
uniform float u_time;       // seconds since start
uniform vec3  u_cam_pos;    // camera position (for fog)
uniform vec3  u_cam_right;  // camera's right vector flattened onto XZ and normalised (for billboarding)

// Active plasma bolts: xyz = world position, w = strength (0 = slot unused).
uniform vec4  u_bolts[__MAX_BOLTS__];

out float v_height;   // height fraction -> colour gradient in the fragment shader
out float v_energy;   // wind "energy" 0..1 -> glow at wave crests
out float v_rand;     // per-blade random
out float v_fog;      // fog factor (1 = clear, 0 = fully fogged)

void main() {
    vec3  root = in_offset.xyz;
    float rnd  = in_offset.w;

    // ---------------- Blade size (per-instance variation) ----------------
    float blade_height = mix(0.55, 1.45, rnd);
    float blade_width  = mix(0.07, 0.12, fract(rnd * 7.31));

    // ---------------- Billboarding (cylindrical, around the Y axis) ----------------
    vec3 world = root;
    world += u_cam_right * (in_vert.x * blade_width);
    world.y += in_vert.y * blade_height;

    // ---------------- WIND DISPLACEMENT ----------------
    // Only the upper part of the blade should move; the root stays pinned.
    float bend = in_vert.y * in_vert.y;

    // (1) Main travelling wave: phase depends on the instance's WORLD position
    //     projected on a wind direction => a coherent sweeping wavefront.
    vec2  wind_dir = normalize(vec2(1.0, 0.45));
    float phase1   = dot(root.xz, wind_dir) * 0.55 - u_time * 2.2;
    float wave1    = sin(phase1);

    // (2) A faster, shorter cross-wave -> interference patterns.
    float phase2   = dot(root.xz, vec2(-0.4, 1.0)) * 1.3 - u_time * 3.6 + rnd * 6.2831;
    float wave2    = sin(phase2) * 0.35;

    // (3) A pulsing radial shockwave from the origin: "arcane energy" rings.
    float radial   = length(root.xz);
    float ring     = sin(radial * 0.45 - u_time * 2.8);
    float pulse    = smoothstep(0.55, 1.0, ring);

    float wave     = wave1 + wave2 + pulse * 1.2;

    float amplitude = 0.55;
    vec2  sway = wind_dir * wave * amplitude * bend;
    sway += vec2(-wind_dir.y, wind_dir.x) * wave2 * 0.25 * bend;  // perpendicular flutter
    world.xz += sway;

    world.y -= length(sway) * 0.35 * bend;

    // ---------------- PLASMA BOLT INTERACTION ----------------
    float bolt_glow = 0.0;
    for (int i = 0; i < __MAX_BOLTS__; i++) {
        vec4 b = u_bolts[i];
        if (b.w <= 0.0) continue;                         // unused slot
        vec3  d    = root - b.xyz;
        float dist = length(d);
        float inf  = (1.0 - smoothstep(0.0, 4.5, dist)) * b.w;
        world.xz  += normalize(d.xz + vec2(1e-4)) * inf * 1.1 * bend;
        bolt_glow  = max(bolt_glow, inf);
    }

    // ---------------- Outputs ----------------
    gl_Position = u_mvp * vec4(world, 1.0);

    v_height = in_vert.y;
    v_rand   = rnd;
    v_energy = clamp(0.5 + 0.35 * wave1 + 0.25 * wave2 + pulse * 0.9, 0.0, 1.0);
    v_energy = max(v_energy, bolt_glow);

    float dist = length(world - u_cam_pos);
    v_fog = exp(-dist * dist * 0.00045);   // exponential-squared fog (blended toward the sky haze)
}
"""

GRASS_FRAGMENT_SHADER = """
#version 330 core

in float v_height;
in float v_energy;
in float v_rand;
in float v_fog;

out vec4 fragColor;

void main() {
    // Arcane palette: deep cyan at the root -> glowing emerald at the tip
    vec3 root_cyan   = vec3(0.00, 0.22, 0.34);
    vec3 mid_cyan    = vec3(0.00, 0.75, 0.85);
    vec3 tip_emerald = vec3(0.10, 1.00, 0.45);

    vec3 col = mix(root_cyan, mid_cyan, smoothstep(0.0, 0.55, v_height));
    col      = mix(col, tip_emerald, smoothstep(0.45, 1.0, v_height));

    col = mix(col, col.gbr * vec3(0.6, 1.0, 1.0), (v_rand - 0.5) * 0.35);

    float glow = v_energy * v_energy * (0.35 + 0.9 * v_height);
    col += vec3(0.05, 0.55, 0.35) * glow;
    col += vec3(0.6, 1.0, 0.9) * pow(v_energy, 6.0) * v_height * 0.6;

    col *= mix(0.35, 1.0, smoothstep(0.0, 0.35, v_height));

    col = mix(__FOG_COLOR__, col, v_fog);

    fragColor = vec4(col, 1.0);
}
"""

# ----------------------------------------------------------------------------
# GLSL: Ground shaders (dark polished slate, faint arcane grid, amber house glow)
# ----------------------------------------------------------------------------
GROUND_VERTEX_SHADER = """
#version 330 core
in vec3 in_position;
uniform mat4 u_mvp;
out vec3 v_world;
void main() {
    v_world = in_position;
    gl_Position = u_mvp * vec4(in_position, 1.0);
}
"""

GROUND_FRAGMENT_SHADER = """
#version 330 core
in vec3 v_world;
uniform float u_time;
uniform vec3  u_cam_pos;
uniform vec4  u_house_rect;   // house footprint: (centre x, centre z, half width, half depth)
out vec4 fragColor;

void main() {
    vec3 slate = vec3(0.018, 0.026, 0.034);

    vec3  to_cam = u_cam_pos - v_world;
    float dist   = length(to_cam);
    float sheen  = pow(clamp(normalize(to_cam).y, 0.0, 1.0), 3.0);
    slate += vec3(0.01, 0.025, 0.03) * sheen;

    vec2 cell = v_world.xz;
    vec2 g    = abs(fract(cell - 0.5) - 0.5) / fwidth(cell);
    float line = 1.0 - clamp(min(g.x, g.y), 0.0, 1.0);

    float radial = length(v_world.xz);
    float ring   = smoothstep(0.55, 1.0, sin(radial * 0.45 - u_time * 2.8));

    vec3 col = slate;
    col += vec3(0.0, 0.22, 0.28) * line * (0.10 + 0.9 * ring);
    col += vec3(0.0, 0.10, 0.12) * ring * 0.35;

    // ---- Warm pool of window light around the house ----
    // Signed-box distance: how far this ground pixel is OUTSIDE the house footprint
    // (0 inside). An exponential falloff of that distance paints a soft amber halo
    // on the slate all the way around the building, so the house looks like it is
    // emitting light into the dark. The grid lines pick the light up too.
    vec2  q  = abs(v_world.xz - u_house_rect.xy) - u_house_rect.zw;
    float hd = length(max(q, 0.0));
    float warm = exp(-hd * 0.55);
    col += vec3(1.0, 0.45, 0.04) * warm * (0.16 + 0.30 * line) * (0.94 + 0.06 * sin(u_time * 1.9));

    col = mix(__FOG_COLOR__, col, exp(-dist * dist * 0.00045));
    fragColor = vec4(col, 1.0);
}
"""

# ----------------------------------------------------------------------------
# GLSL: Tree (slate monolith) shaders: instanced boxes + `discard` holes
# ----------------------------------------------------------------------------
TREE_VERTEX_SHADER = """
#version 330 core

// ---- Per-VERTEX: a unit pillar mesh (divisor = 0) ----
// x,z in [-1, 1], y in [0, 1]  (the base sits on the ground, the top at y = 1)
in vec3 in_vert;
in vec3 in_normal;      // flat face normal (axis aligned)

// ---- Per-INSTANCE (divisor = 1) ----
in vec4 in_base;        // xyz = world position of the base centre, w = random seed
in vec3 in_size;        // x = half-width along X, y = height, z = half-width along Z

uniform mat4 u_mvp;

out vec3  v_world;
out vec3  v_normal;
out float v_hfrac;
out float v_seed;

void main() {
    // Non-uniform scaling of an AXIS-ALIGNED box does not change its face
    // normals, so we can pass in_normal through untouched.
    vec3 world = in_base.xyz + in_vert * in_size;

    v_world  = world;
    v_normal = in_normal;
    v_hfrac  = in_vert.y;
    v_seed   = in_base.w;
    gl_Position = u_mvp * vec4(world, 1.0);
}
"""

TREE_FRAGMENT_SHADER = """
#version 330 core
in vec3  v_world;
in vec3  v_normal;
in float v_hfrac;
in float v_seed;

uniform float u_time;
uniform vec3  u_cam_pos;
uniform vec3  u_sun_dir;

// ---- Destruction data, written from Python every frame ----
uniform vec3  hit_points[__MAX_HITS__];   // world-space impact coordinates
uniform int   u_hit_count;                // how many entries are valid
uniform float u_hole_radius;              // radius of every blasted hole

out vec4 fragColor;

void main() {
    // =====================================================================
    // THE HOLE TEST  (this is the whole destruction effect)
    // =====================================================================
    // For this pixel's WORLD position we measure the distance to every
    // recorded impact point. A pixel closer than the hole radius is
    // `discard`ed: the GPU throws the fragment away completely, so it writes
    // neither colour NOR depth. The pillar's surface simply does not exist
    // there, so the background / interior behind it shows through. Because
    // the test is done in 3D world space, the same sphere carves every face
    // it touches (front, back, edges) as one consistent hole.
    //
    // The radius is perturbed by a product of sines of the position relative
    // to the impact, so the rim becomes ragged, like melted stone.
    //
    // `gap` records how far OUTSIDE the nearest hole this pixel is
    // (distance - effective radius). It drives the glowing rim afterwards.
    float gap = 1e5;
    for (int i = 0; i < __MAX_HITS__; i++) {
        if (i >= u_hit_count) break;                       // only the valid entries
        vec3  off = v_world - hit_points[i];
        float d   = length(off);
        float ragged = sin(off.x * 21.0 + off.y * 13.0 + float(i) * 1.7)
                     * sin(off.z * 25.0 - off.y *  9.0 + float(i) * 0.9);
        float r = u_hole_radius * (1.0 + 0.16 * ragged);   // effective, irregular radius
        if (d < r) discard;                                // INSIDE the hole -> pixel vanishes
        gap = min(gap, d - r);                             // just outside -> remember how close
    }

    vec3 N = normalize(v_normal);
    bool front = gl_FrontFacing;
    if (!front) N = -N;     // looking at the inside of the shell through a hole

    vec3 V = normalize(u_cam_pos - v_world);
    vec3 cyan    = vec3(0.00, 0.85, 1.00);
    vec3 emerald = vec3(0.05, 1.00, 0.40);

    vec3 col;
    if (front) {
        float diff   = max(dot(N, u_sun_dir), 0.0);
        float strata = 0.5 + 0.5 * sin(v_world.y * 9.0 + v_seed * 20.0);
        col  = vec3(0.030, 0.042, 0.055) * (0.8 + 0.4 * strata);
        col += vec3(0.02, 0.16, 0.14) * diff * 0.55;

        float u = (abs(N.x) > 0.5) ? v_world.z : v_world.x;
        col += cyan * smoothstep(0.94, 1.0, sin(u * 6.0 + v_seed * 10.0)) * 0.10;

        float band = smoothstep(0.95, 1.0, sin(v_world.y * 2.2 - u_time * 1.4 + v_seed * 6.2831));
        col += cyan * band * 0.45;

        col += cyan * smoothstep(0.955, 0.985, v_hfrac) * (0.5 + 0.2 * sin(u_time * 2.0 + v_seed * 6.0));
        if (N.y > 0.9) col = mix(col, cyan * (0.55 + 0.25 * sin(u_time * 2.0 + v_seed * 6.0)), 0.85);

        col += cyan * pow(1.0 - max(dot(N, V), 0.0), 3.0) * 0.18;
    } else {
        col  = vec3(0.004, 0.018, 0.020);
        col += emerald * exp(-gap * 2.5) * (0.55 + 0.15 * sin(u_time * 5.0));
    }

    // ---- Superheated arcane slag on the rim of every hole ----
    float rim_w = 0.18;
    if (gap < rim_w) {
        float k = 1.0 - gap / rim_w;                        // 1 at the hole edge, 0 at the outer rim
        vec3 slag = mix(vec3(0.00, 1.00, 0.35), vec3(0.80, 1.00, 0.90), k * k);
        slag *= 1.8 + 0.5 * sin(u_time * 9.0 + v_world.y * 20.0);
        col = mix(col, slag, pow(k, 0.6));
    }
    col += emerald * exp(-gap * 7.0) * 0.45;

    float dist = length(v_world - u_cam_pos);
    col = mix(__FOG_COLOR__, col, exp(-dist * dist * 0.00045));
    fragColor = vec4(col, 1.0);
}
"""

# ----------------------------------------------------------------------------
# GLSL: Cozy house shaders (one static mesh, four surface types selected by a part id)
# ----------------------------------------------------------------------------
HOUSE_VERTEX_SHADER = """
#version 330 core
// The house is ONE static mesh whose vertices are already in WORLD space
// (the house position was baked in when the mesh was generated), so no model matrix is needed.
in vec3  in_pos;
in vec3  in_normal;   // flat face normal
in float in_part;     // 0 = slate wall, 1 = roof, 2 = glowing window, 3 = door
in vec2  in_uv;       // 0..1 across windows / door (used for frames, mullions, trim)

uniform mat4 u_mvp;

out vec3  v_world;
out vec3  v_normal;
out float v_part;
out vec2  v_uv;

void main() {
    v_world  = in_pos;
    v_normal = in_normal;
    v_part   = in_part;
    v_uv     = in_uv;
    gl_Position = u_mvp * vec4(in_pos, 1.0);
}
"""

HOUSE_FRAGMENT_SHADER = """
#version 330 core
in vec3  v_world;
in vec3  v_normal;
in float v_part;
in vec2  v_uv;

uniform float u_time;
uniform vec3  u_cam_pos;
uniform vec3  u_sun_dir;
uniform vec3  u_light_pos;   // the "hearth light": an invisible warm point light in front of the door

out vec4 fragColor;

const vec3 AMBER = vec3(1.0, 0.52, 0.04);

void main() {
    int part = int(v_part + 0.5);

    vec3 N = normalize(v_normal);
    if (!gl_FrontFacing) N = -N;                  // seeing the inside of a wall: flip toward the eye

    vec3  V  = normalize(u_cam_pos - v_world);
    vec3  H  = normalize(u_sun_dir + V);
    vec3  Lw = u_light_pos - v_world;             // surface -> warm light
    float dl = length(Lw);
    Lw /= dl;
    float att  = 1.0 / (1.0 + 0.09 * dl * dl);    // inverse-square-ish falloff
    float diff = max(dot(N, u_sun_dir), 0.0);
    float fres = pow(1.0 - max(dot(N, V), 0.0), 4.0);

    vec3 col;

    if (part == 2) {
        // ---------------- WINDOW: warm, highly saturated amber glow ----------------
        vec2  uv   = v_uv;
        float edge = min(min(uv.x, 1.0 - uv.x), min(uv.y, 1.0 - uv.y));  // distance to the pane border
        float bar  = min(abs(uv.x - 0.5), abs(uv.y - 0.5));              // distance to the nearest mullion
        float frame_mask = 1.0 - smoothstep(0.07, 0.09, edge);
        float mull_mask  = 1.0 - smoothstep(0.022, 0.034, bar);
        float dark = max(frame_mask, mull_mask);

        // Candle-like flicker, de-synchronised per window through the world position
        float flicker = 0.92 + 0.08 * sin(u_time * 1.9 + v_world.x * 3.1 + v_world.z * 2.3);

        // Hotter gold in the middle of the pane, deep orange-amber near the edges
        float centre = clamp(1.0 - length(uv - 0.5) * 1.25, 0.0, 1.0);
        vec3 glass = mix(vec3(1.0, 0.30, 0.0), vec3(1.0, 0.82, 0.28), centre);
        glass *= (1.5 + 0.5 * uv.y) * flicker;

        vec3 frame_col = vec3(0.020, 0.026, 0.034) + AMBER * 0.10;       // slate frame lit from the pane
        col = mix(glass, frame_col, dark);
    }
    else if (part == 3) {
        // ---------------- DOOR: dark slate slab with glowing amber trim ----------------
        vec2  uv   = v_uv;
        float edge = min(min(uv.x, 1.0 - uv.x), min(uv.y, 1.0 - uv.y));
        float trim  = 1.0 - smoothstep(0.05, 0.075, edge);
        float panel = 1.0 - smoothstep(0.0, 0.012, abs(edge - 0.16));    // inset panel line
        col  = vec3(0.020, 0.026, 0.036) * (0.8 + 0.6 * diff);
        col += AMBER * (trim * 1.3 + panel * 0.35);
        float hd = length(uv - vec2(0.82, 0.48));                         // handle
        col += AMBER * 1.6 * (1.0 - smoothstep(0.03, 0.05, hd));
        col += AMBER * att * 0.25;
    }
    else if (part == 1) {
        // ---------------- ROOF: darker slate with a subtle polished specular sheen ----------------
        vec3 base = vec3(0.022, 0.030, 0.044);
        // Shingle courses: horizontal rows every 0.3 units, vertical joints staggered per row
        float row = floor(v_world.y / 0.30);
        float fu  = fract(v_world.x / 0.55 + 0.5 * mod(row, 2.0));
        float fy  = fract(v_world.y / 0.30);
        float seam = max(1.0 - smoothstep(0.0, 0.05, min(fy, 1.0 - fy)),
                         1.0 - smoothstep(0.0, 0.04, min(fu, 1.0 - fu)));
        col = base * (1.0 - 0.45 * seam);

        // Polished-stone sheen = three small terms:
        //  (a) Blinn-Phong highlight of the emerald sun,
        //  (b) a mirror glint (reflect the view ray about N, compare with the sun),
        //  (c) a faint reflection of the hazy cyan horizon, strongest when the reflected ray
        //      points toward the horizon (R.y small) and weakest when it points at the dark zenith.
        vec3  R     = reflect(-V, N);
        float spec  = pow(max(dot(N, H), 0.0), 24.0);
        float glint = pow(max(dot(R, u_sun_dir), 0.0), 48.0);
        float haze  = exp(-max(R.y, 0.0) * 3.0);
        col += vec3(0.30, 0.95, 0.85) * (spec * 0.35 + glint * 1.0);
        col += vec3(0.00, 0.10, 0.12) * haze * 0.35;
        col += vec3(0.00, 0.25, 0.30) * fres * 0.5;
        // Warm window light grazes the eaves
        vec3  Hl = normalize(Lw + V);
        col += AMBER * pow(max(dot(N, Hl), 0.0), 40.0) * att * 2.0 * 0.5;
        col += AMBER * att * max(dot(N, Lw), 0.0) * 0.10;
    }
    else {
        // ---------------- WALL: the same dark polished slate as the rest of the world ----------------
        vec3 slate = vec3(0.032, 0.042, 0.056);
        float u   = (abs(N.x) > 0.5) ? v_world.z : v_world.x;      // coordinate running ALONG this wall
        float row = floor(v_world.y / 0.35);
        float fy  = fract(v_world.y / 0.35);
        float fu  = fract(u / 0.80 + 0.5 * mod(row, 2.0));          // staggered like masonry courses
        float seam = max(1.0 - smoothstep(0.0, 0.05, min(fy, 1.0 - fy)),
                         1.0 - smoothstep(0.0, 0.03, min(fu, 1.0 - fu)));
        col  = slate * (1.0 - 0.5 * seam);
        col += vec3(0.00, 0.10, 0.12) * seam * 0.25;                // faint cyan tech grooves
        col += vec3(0.02, 0.14, 0.12) * diff * 0.5;                 // emerald sun
        col += vec3(0.00, 0.20, 0.25) * fres * 0.25;
        // Warm light from the windows / door washing over the facade ("safe haven" glow)
        col += AMBER * att * (0.15 + 0.5 * max(dot(N, Lw), 0.0)) * 0.35;
    }

    float dist = length(v_world - u_cam_pos);
    col = mix(__FOG_COLOR__, col, exp(-dist * dist * 0.00045));
    fragColor = vec4(col, 1.0);
}
"""

# ----------------------------------------------------------------------------
# GLSL: Creature shaders (instanced parts: alive constructs AND dead debris)
#       team 0 = violet/magenta melee constructs, team 1 = solar amber artillery
# ----------------------------------------------------------------------------
CREATURE_VERTEX_SHADER = """
#version 330 core

// ---- Per-VERTEX: a unit primitive centred on the origin (cube or shard) ----
in vec3 in_vert;
in vec3 in_normal;

// ---- Per-INSTANCE: one record per PART (divisor = 1), 19 floats ----
// The part's rigid transform is given as a 3x3 rotation (its three COLUMNS)
// plus a translation and a per-axis scale. Passing it this way (instead of a
// mat4) lets us build the correct normal matrix cheaply, see below.
in vec3 in_r0;        // world-space image of local +X   (column 0 of R)
in vec3 in_r1;        // world-space image of local +Y   (column 1 of R)
in vec3 in_r2;        // world-space image of local +Z   (column 2 of R)
in vec3 in_ipos;      // world-space centre of the part
in vec3 in_scale;     // half-extents of the part along its local axes
in vec4 in_params;    // x = ENERGY (glow multiplier, 0 = dead), y = seed, z = role id, w = TEAM (0 violet, 1 amber)

uniform mat4 u_mvp;

out vec3 v_world;
out vec3 v_normal;
out vec3 v_local;     // position in the unit primitive's own space (for edge / tip glow)
out vec4 v_params;

void main() {
    // world = R * (S * local) + position
    vec3 local = in_vert * in_scale;
    vec3 world = in_r0 * local.x + in_r1 * local.y + in_r2 * local.z + in_ipos;

    // Normals under non-uniform scale: the normal matrix is the inverse
    // transpose of (R * S), which is R * S^-1 for a rotation R and diagonal S.
    // So: divide by the scale first, THEN rotate.
    vec3 n = in_normal / in_scale;
    v_normal = normalize(in_r0 * n.x + in_r1 * n.y + in_r2 * n.z);

    v_world  = world;
    v_local  = in_vert;
    v_params = in_params;
    gl_Position = u_mvp * vec4(world, 1.0);
}
"""

CREATURE_FRAGMENT_SHADER = """
#version 330 core
in vec3 v_world;
in vec3 v_normal;
in vec3 v_local;
in vec4 v_params;

uniform float u_time;
uniform vec3  u_cam_pos;
uniform vec3  u_sun_dir;

out vec4 fragColor;

void main() {
    float energy = v_params.x;               // glow multiplier: 1 = alive, >1 = charging a shot, 0 = dead
    float seed   = v_params.y;
    int   role   = int(v_params.z + 0.5);    // 0 body, 1 armour plate, 2 spike / shard
    float team   = v_params.w;               // 0 = violet/magenta melee, 1 = solar amber artillery

    vec3 N = normalize(v_normal);
    vec3 V = normalize(u_cam_pos - v_world);
    vec3 H = normalize(u_sun_dir + V);

    // ---------------- Dark polished slate ----------------
    // Subtle faceting using the LOCAL position, so the pattern sticks to the
    // part as it moves / tumbles instead of swimming across it.
    float facet = 0.5 + 0.5 * sin(dot(v_local, vec3(5.0, 9.0, 7.0)) + seed * 30.0);
    vec3 slate = vec3(0.034, 0.044, 0.060) * (0.75 + 0.5 * facet);

    float diff = max(dot(N, u_sun_dir), 0.0);
    float spec = pow(max(dot(N, H), 0.0), 70.0);              // tight polished highlight
    float fres = pow(1.0 - max(dot(N, V), 0.0), 4.0);

    vec3 col = slate * (0.7 + 1.8 * diff);
    col += vec3(0.25, 0.95, 0.85) * spec * 0.55;              // sun glint (emerald-cyan sun)
    col += vec3(0.00, 0.20, 0.25) * fres * 0.55;              // polished surface mirrors the cyan haze

    // ---------------- Energy glow (ALIVE only) ----------------
    // `a` is the absolute local coordinate: 1.0 on the outer surface of the primitive.
    vec3  a    = abs(v_local);
    float glow = 0.0;
    if (role == 2) {
        // Shards glow at their needle tips
        glow = smoothstep(0.70, 1.0, a.y);
    } else {
        // Cubes glow along their EDGES: at least two coordinates close to +-1
        float e = step(0.86, a.x) + step(0.86, a.y) + step(0.86, a.z);
        glow = (e > 1.5) ? 1.0 : 0.0;
        // The body also has a burning "eye slit" on its front (+Z) face
        if (role == 0 && v_local.z > 0.99 && a.y < 0.20 && a.x < 0.75) glow = 1.6;
    }
    float pulse = 0.75 + 0.25 * sin(u_time * 7.0 + seed * 6.2831);

    // Team palettes: melee = violet <-> magenta, artillery = Solar Amber <-> Crimson Gold
    vec3 violet  = vec3(0.55, 0.05, 1.00);
    vec3 magenta = vec3(1.00, 0.00, 0.65);
    vec3 amber   = vec3(1.00, 0.55, 0.02);
    vec3 crimson = vec3(1.00, 0.10, 0.06);
    float k = 0.5 + 0.5 * sin(u_time * 2.0 + seed * 9.0);
    vec3 glow_col = mix(mix(violet, magenta, k), mix(amber, crimson, k * 0.8), team);
    vec3 rim_col  = mix(violet, amber, team);
    vec3 leak_col = mix(magenta, crimson, team);

    // Everything below is multiplied by `energy`: when a construct dies the
    // Python side uploads energy = 0 and ALL of this vanishes at once,
    // leaving only the unlit slate computed above. (Artillery push energy above 1
    // for a moment before firing, so the barrel visibly "charges".)
    col += glow_col * glow * energy * pulse * 2.3;
    col += rim_col * fres * energy * 0.9;                     // coloured rim light
    col += leak_col * energy * 0.05;                          // faint inner leak

    float dist = length(v_world - u_cam_pos);
    col = mix(__FOG_COLOR__, col, exp(-dist * dist * 0.00045));
    fragColor = vec4(col, 1.0);
}
"""

# ----------------------------------------------------------------------------
# GLSL: Plasma orb shaders (instanced, spherically billboarded quads).
# The SAME shaders draw the player's cyan/emerald bolts and the enemy's amber/crimson
# shots: only the palette uniforms and the size differ.
# ----------------------------------------------------------------------------
BOLT_VERTEX_SHADER = """
#version 330 core

// ---- Per-VERTEX: one shared unit quad, corners in [-1, 1] ----
in vec2  in_quad;

// ---- Per-INSTANCE: one record per live orb (divisor = 1) ----
in vec3  in_center;   // world-space centre of the orb
in float in_seed;     // random 0..1: de-synchronises the swirl of each orb
in float in_fade;     // 0..1: grows in at birth, shrinks at the end of the lifespan

uniform mat4  u_mvp;        // projection * view
uniform float u_time;
uniform float u_size;       // base orb radius (player bolts 0.6, enemy shots smaller)
uniform vec3  u_cam_right;  // camera's TRUE right vector (row 0 of the view rotation)
uniform vec3  u_cam_up;     // camera's TRUE up vector    (row 1 of the view rotation)

out vec2  v_uv;
out float v_seed;
out float v_fade;

void main() {
    // ---------------- SPHERICAL BILLBOARDING ----------------
    // Expand the quad along the camera's own right/up axes:
    //     corner_world = centre + right * (qx * size) + up * (qy * size)
    // right/up are the basis vectors of the camera's image plane, so the quad
    // ends up exactly parallel to the screen => it always faces the viewer,
    // even when looking up or down (spherical billboarding).
    float size = u_size * (0.92 + 0.12 * sin(u_time * 14.0 + in_seed * 30.0)) * in_fade;
    vec3 world = in_center
               + u_cam_right * (in_quad.x * size)
               + u_cam_up    * (in_quad.y * size);

    gl_Position = u_mvp * vec4(world, 1.0);
    v_uv   = in_quad;
    v_seed = in_seed;
    v_fade = in_fade;
}
"""

BOLT_FRAGMENT_SHADER = """
#version 330 core

in vec2  v_uv;
in float v_seed;
in float v_fade;

uniform float u_time;
uniform vec3  u_col_a;      // palette colour A (player: cyan,    enemy: crimson)
uniform vec3  u_col_b;      // palette colour B (player: emerald, enemy: solar amber)
uniform vec3  u_core;       // white-hot heart colour
out vec4 fragColor;

float hash(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

float fbm(vec2 p) {
    float v = 0.0, a = 0.5;
    for (int i = 0; i < 4; i++) {
        v += a * noise(p);
        p  = p * 2.03 + vec2(17.1, 9.2);
        a *= 0.5;
    }
    return v;
}

mat2 rot(float a) { float c = cos(a), s = sin(a); return mat2(c, -s, s, c); }

void main() {
    vec2  uv = v_uv;
    float r  = length(uv);
    if (r > 1.0) discard;

    // Differential rotation (bigger twist near the centre) drags the noise into a vortex.
    float twist = (1.0 - r) * 5.0 - u_time * 4.0 + v_seed * 6.2831;
    vec2  p = rot(twist) * uv * 2.2;

    float n1 = fbm(p + vec2(u_time * 0.8, -u_time * 0.6));
    float n2 = fbm(p * 1.7 - n1 * 1.5 + vec2(-u_time * 1.1, u_time * 0.7));

    float ang  = atan(uv.y, uv.x);
    float arms = 0.5 + 0.5 * sin(ang * 3.0 + r * 9.0 - u_time * 7.0 + v_seed * 6.2831);

    vec3 col = mix(u_col_a, u_col_b, smoothstep(0.30, 0.70, n2));
    col *= 0.35 + 1.7 * n2;

    float falloff = 1.0 - smoothstep(0.30, 1.0, r);
    float core    = exp(-r * r * 7.0);

    col += u_col_a * arms * falloff * 0.45;
    col += u_core * core * 1.7;
    col += u_col_a * 0.5 * smoothstep(0.6, 0.95, r) * (1.0 - smoothstep(0.95, 1.0, r)) * 0.6;

    fragColor = vec4(col * falloff * v_fade, 1.0);
}
"""

# ----------------------------------------------------------------------------
# GLSL: Staff view-model shaders (dark slate shaft + pulsing tech-glass crystal)
# ----------------------------------------------------------------------------
STAFF_VERTEX_SHADER = """
#version 330 core
in vec3  in_pos;      // staff-local position
in vec3  in_normal;   // flat-shaded face normal (staff-local)
in float in_part;     // 0 = slate shaft, 1 = glass crystal

uniform mat4  u_proj;    // projection ONLY: the "view" is identity, we place the staff directly in view space
uniform mat4  u_model;   // staff-local -> view space (fixed offset in the bottom-right corner)
uniform float u_time;

out vec3  v_normal;      // view-space normal
out vec3  v_view;        // view-space position
out float v_part;
out float v_h;           // staff-local height (for rune bands / shimmer)

void main() {
    vec3 p = in_pos;
    vec3 n = in_normal;

    if (in_part > 0.5) {
        vec3  c = vec3(0.0, 0.85, 0.0);
        float a = u_time * 0.9;
        mat2  R = mat2(cos(a), -sin(a), sin(a), cos(a));
        vec3  q = p - c;
        q.xz = R * q.xz;
        n.xz = R * n.xz;
        float pulse = 1.0 + 0.07 * sin(u_time * 3.0);
        p = c + q * pulse;
    }

    vec4 vp  = u_model * vec4(p, 1.0);
    v_view   = vp.xyz;
    v_normal = mat3(u_model) * n;
    v_part   = in_part;
    v_h      = in_pos.y;
    gl_Position = u_proj * vp;
}
"""

STAFF_FRAGMENT_SHADER = """
#version 330 core
in vec3  v_normal;
in vec3  v_view;
in float v_part;
in float v_h;

uniform float u_time;
out vec4 fragColor;

void main() {
    vec3 N = normalize(v_normal);
    vec3 V = normalize(-v_view);
    vec3 L = normalize(vec3(-0.4, 0.7, 0.6));
    float diff = max(dot(N, L), 0.0);
    float fres = pow(1.0 - max(dot(N, V), 0.0), 3.0);

    vec3 cyan    = vec3(0.00, 0.85, 1.00);
    vec3 emerald = vec3(0.05, 1.00, 0.45);
    float beat   = 0.5 + 0.5 * sin(u_time * 3.0);

    vec3 col;
    if (v_part < 0.5) {
        col  = vec3(0.025, 0.04, 0.055) + diff * vec3(0.035, 0.055, 0.07);
        col += cyan * fres * 0.30;
        float band = smoothstep(0.94, 1.0, sin(v_h * 38.0 - u_time * 2.5));
        col += cyan * band * 0.55;
    } else {
        vec3 base = mix(cyan, emerald, 0.5 + 0.5 * N.x + 0.2 * sin(u_time + v_h * 6.0));
        float shimmer = 0.5 + 0.5 * sin(v_h * 30.0 - u_time * 4.0);
        col  = base * (0.30 + 0.55 * diff + 0.55 * beat);
        col += base * shimmer * 0.25;
        col += vec3(0.7, 1.0, 0.95) * fres * (0.6 + 0.6 * beat);
    }
    fragColor = vec4(col, 1.0);
}
"""

# ----------------------------------------------------------------------------
# GLSL: Crosshair (tiny 2D overlay in NDC)
# ----------------------------------------------------------------------------
CROSS_VERTEX_SHADER = """
#version 330 core
in vec2 in_pos;
void main() { gl_Position = vec4(in_pos, 0.0, 1.0); }
"""
CROSS_FRAGMENT_SHADER = """
#version 330 core
out vec4 fragColor;
void main() { fragColor = vec4(0.0, 0.55, 0.45, 1.0); }
"""


# ----------------------------------------------------------------------------
# Matrix helpers (column-vector convention: clip = M @ v)
# ----------------------------------------------------------------------------
def perspective(fov_y_deg, aspect, near, far):
    """Standard OpenGL perspective projection matrix."""
    f = 1.0 / math.tan(math.radians(fov_y_deg) / 2.0)
    m = np.zeros((4, 4), dtype=np.float32)
    m[0, 0] = f / aspect
    m[1, 1] = f
    m[2, 2] = (far + near) / (near - far)
    m[2, 3] = (2.0 * far * near) / (near - far)
    m[3, 2] = -1.0
    return m


def look_along(eye, forward, up=np.array([0.0, 1.0, 0.0], dtype=np.float32)):
    """
    View matrix for a camera at `eye` looking along the unit vector `forward`.
    Rows of the rotation part are the camera's basis vectors (right, up, -forward);
    the translation moves the world so the eye sits at the origin.
    """
    f = forward / np.linalg.norm(forward)
    r = np.cross(f, up)
    r /= np.linalg.norm(r)
    u = np.cross(r, f)

    view = np.identity(4, dtype=np.float32)
    view[0, :3] = r
    view[1, :3] = u
    view[2, :3] = -f
    view[0, 3] = -np.dot(r, eye)
    view[1, 3] = -np.dot(u, eye)
    view[2, 3] = np.dot(f, eye)
    return view


def translate(x, y, z):
    m = np.identity(4, dtype=np.float32)
    m[:3, 3] = (x, y, z)
    return m


def rotate_x(a):
    c, s = math.cos(a), math.sin(a)
    m = np.identity(4, dtype=np.float32)
    m[1, 1], m[1, 2], m[2, 1], m[2, 2] = c, -s, s, c
    return m


def rotate_z(a):
    c, s = math.cos(a), math.sin(a)
    m = np.identity(4, dtype=np.float32)
    m[0, 0], m[0, 1], m[1, 0], m[1, 1] = c, -s, s, c
    return m


def scale(s):
    m = np.identity(4, dtype=np.float32)
    m[0, 0] = m[1, 1] = m[2, 2] = s
    return m


def to_gl_bytes(mat):
    """NumPy is row-major; GLSL expects column-major. Transpose before serialising."""
    return mat.T.astype("f4").tobytes()


# ---- 3x3 rotation helpers (float64) used by creatures and the debris physics ----
def rot_y3(a):
    """Rotation about the world Y axis. Maps local +Z to (sin a, 0, cos a)."""
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]])


def rot_z3(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def axis_angle_matrix(axis, angle):
    """
    Rodrigues' rotation formula: the 3x3 matrix that rotates by `angle` radians
    about the UNIT vector `axis`.
        R = I + sin(angle) * K + (1 - cos(angle)) * K^2
    where K is the skew-symmetric "cross-product matrix" of the axis (K @ v == axis x v).
    """
    x, y, z = axis
    K = np.array([[0.0, -z, y], [z, 0.0, -x], [-y, x, 0.0]])
    return np.eye(3) + math.sin(angle) * K + (1.0 - math.cos(angle)) * (K @ K)


def orthonormalize(R):
    """
    Repeatedly multiplying rotation matrices accumulates floating-point error, so
    R slowly stops being a pure rotation. One Gram-Schmidt pass on the columns
    snaps it back to an orthonormal basis.
    """
    c0 = R[:, 0] / np.linalg.norm(R[:, 0])
    c1 = R[:, 1] - c0 * np.dot(c0, R[:, 1])
    c1 /= np.linalg.norm(c1)
    c2 = np.cross(c0, c1)                 # right-handed: third axis is fully determined
    return np.stack([c0, c1, c2], axis=1)


# ----------------------------------------------------------------------------
# First-person camera  (INFINITE 360-degree mouse look)
# ----------------------------------------------------------------------------
class FPSCamera:
    """
    Camera state is just TWO angles (in degrees) plus a position:

        yaw   : rotation about the world Y axis. Deliberately UNBOUNDED. It is only
                ever fed to sin()/cos(), which are periodic, so yaw = 10 and
                yaw = 370 and yaw = -350 are the same direction. Spinning forever
                in either direction therefore just works.
        pitch : up/down angle. CLAMPED to [-89, +89] degrees. At exactly +-90 the
                forward vector becomes parallel to the world "up" axis, so
                cross(forward, up) is the zero vector and the right/up basis
                collapses (gimbal lock: the view flips upside down). Stopping one
                degree short keeps the basis well defined.

    From these two angles we rebuild the Forward / Right / Up vectors EVERY time
    the angles change (see update_vectors).
    """

    def __init__(self, position):
        self.position = np.array(position, dtype=np.float32)
        self.yaw = 0.0        # degrees; 0 => looking toward -Z (OpenGL's default view direction)
        self.pitch = -8.0     # degrees; slightly down
        self._fwd = self._right = self._up = None
        self.update_vectors()

    def rotate(self, dx, dy):
        """
        Apply one frame of RELATIVE mouse movement.

        dx, dy come from pygame.mouse.get_rel(): the number of pixels the mouse moved
        since the previous call. They are small deltas, never screen positions, so it
        does not matter where the cursor is: there is no screen edge to run into.

        * Mouse right (dx > 0) must turn the view right. With the basis defined below,
          increasing yaw rotates forward from -Z toward +X (to the right), so yaw += dx.
        * Mouse up (dy < 0 in screen coordinates, since screen Y grows downward) must
          look up, so pitch -= dy.
        """
        self.yaw += dx * MOUSE_SENSITIVITY                       # NO clamp: unlimited spins
        self.pitch -= dy * MOUSE_SENSITIVITY
        self.pitch = max(-PITCH_LIMIT_DEG, min(PITCH_LIMIT_DEG, self.pitch))   # clamp ONLY pitch
        self.update_vectors()

    def update_vectors(self):
        """
        Recompute Forward, Right and Up from yaw and pitch with plain trigonometry.

        Let y = yaw, p = pitch (converted to radians).

        FORWARD: spherical -> Cartesian conversion.
            The horizontal part of the look direction has length cos(p) (it shrinks as
            you look up/down) and points along (sin y, -cos y) on the XZ plane:
                forward.x =  cos(p) * sin(y)
                forward.y =  sin(p)
                forward.z = -cos(p) * cos(y)
            Check: y = 0, p = 0 -> (0, 0, -1), i.e. looking down -Z.
                   |forward|^2 = cos^2(p)(sin^2 y + cos^2 y) + sin^2(p) = 1  -> unit length.

        RIGHT: right = normalize( forward x worldUp ), worldUp = (0, 1, 0).
            Working the cross product out, the pitch terms cancel and the cos(p)
            factor is exactly what normalisation divides away:
                right = (cos(y), 0, sin(y))
            So Right depends on YAW ONLY: looking up or down never tilts it (no roll).
            Check: y = 0 -> (1, 0, 0), +X is to the right when facing -Z.

        UP: up = right x forward. Perpendicular to both, so it tilts with the pitch:
                up = (-sin(y) * sin(p), cos(p), cos(y) * sin(p))
            It always has a positive Y component (cos p > 0 because |p| <= 89 deg),
            which is exactly what keeps the camera from ever flipping upside down.

        These three vectors are an orthonormal basis; they are the rows of the view
        matrix's rotation part, and are used for movement, bolt billboards and the sky.
        """
        y = math.radians(self.yaw)
        p = math.radians(self.pitch)
        cy, sy = math.cos(y), math.sin(y)
        cp, sp = math.cos(p), math.sin(p)

        self._fwd = np.array([cp * sy, sp, -cp * cy], dtype=np.float32)
        self._right = np.array([cy, 0.0, sy], dtype=np.float32)
        self._up = np.array([-sy * sp, cp, cy * sp], dtype=np.float32)   # == cross(right, forward)

    # ---- accessors (all read the vectors rebuilt in update_vectors) ----
    def forward(self):
        """Full 3D look direction (includes pitch). Used for aiming and the view matrix."""
        return self._fwd

    def flat_forward(self):
        """
        Forward projected on the ground plane and re-normalised: (sin y, 0, -cos y).
        Movement uses this, so W/S never fly you up or down when you look up/down.
        """
        y = math.radians(self.yaw)
        return np.array([math.sin(y), 0.0, -math.cos(y)], dtype=np.float32)

    def flat_right(self):
        """Right vector (already horizontal): (cos y, 0, sin y). Strafing + grass billboarding."""
        return self._right

    def basis(self):
        """Full camera basis in world space: (right, up, forward)."""
        return self._right, self._up, self._fwd

    def update(self, keys, dt):
        """
        WASD movement. Because flat_forward()/flat_right() are rebuilt from the current
        yaw, "W" always moves toward where you are looking and "D" always strafes to
        your right, no matter how many full turns the camera has made.
        """
        speed = MOVE_SPEED * (2.5 if keys[pygame.K_LSHIFT] else 1.0) * dt
        fwd, right = self.flat_forward(), self.flat_right()
        if keys[pygame.K_w]: self.position += fwd * speed
        if keys[pygame.K_s]: self.position -= fwd * speed
        if keys[pygame.K_d]: self.position += right * speed
        if keys[pygame.K_a]: self.position -= right * speed
        if keys[pygame.K_SPACE]: self.position[1] += speed
        if keys[pygame.K_LCTRL]:  self.position[1] -= speed
        self.position[1] = max(0.25, self.position[1])   # stay above the ground

    def view_matrix(self):
        return look_along(self.position, self.forward())


def push_out_of_box(pos, bmin, bmax, margin):
    """
    Keep the player out of the house walls: if the camera is inside the (expanded) wall
    box, slide it out through the NEAREST face. Only active below the wall top, so
    flying over the roof still works.
    """
    if pos[1] > bmax[1] + 0.2:
        return
    lo_x, hi_x = bmin[0] - margin, bmax[0] + margin
    lo_z, hi_z = bmin[2] - margin, bmax[2] + margin
    if lo_x < pos[0] < hi_x and lo_z < pos[2] < hi_z:
        d = [pos[0] - lo_x, hi_x - pos[0], pos[2] - lo_z, hi_z - pos[2]]   # distance to each face
        k = int(np.argmin(d))
        if k == 0:   pos[0] = lo_x
        elif k == 1: pos[0] = hi_x
        elif k == 2: pos[2] = lo_z
        else:        pos[2] = hi_z


# ----------------------------------------------------------------------------
# Projectiles
# ----------------------------------------------------------------------------
class Fireball:
    """
    One Arcane Plasma Bolt: position, velocity, age and lifespan.

    `prev` is where the bolt was at the START of the frame; together with `pos`
    it forms the line SEGMENT swept this frame, which we ray-cast against the
    trees, house and creatures (so a fast bolt can never "tunnel" through a thin target).

    `solid=False` makes a harmless, stationary visual (used for impact flashes).
    """
    __slots__ = ("pos", "prev", "vel", "age", "life", "seed", "solid")

    def __init__(self, pos, vel, life, seed, solid=True):
        self.pos = np.array(pos, dtype=np.float32)
        self.prev = self.pos.copy()
        self.vel = np.array(vel, dtype=np.float32)
        self.age = 0.0
        self.life = life
        self.seed = seed
        self.solid = solid

    def fade(self):
        """Grow in over 0.08 s at birth, shrink out over the last 0.5 s."""
        fade_in = min(self.age / 0.08, 1.0)
        fade_out = min(max((self.life - self.age) / 0.5, 0.0), 1.0)
        return min(fade_in, fade_out)


class EnemyShot:
    """
    A Solar-Amber projectile fired by an artillery construct. It is harmless:
    when it reaches the player it BOUNCES away (see deflect_off_player).

    State machine:
        flying straight  ->  (touches player sphere)  ->  bounced: gravity ON, arcs to the
        ground, bounces once or twice, then fades out and despawns.
    Gravity is deliberately NOT applied before the bounce, so the shot flies in a straight,
    readable line toward the player's camera position at the moment of firing.
    """
    __slots__ = ("pos", "prev", "vel", "age", "life", "seed", "bounced")

    def __init__(self, pos, vel, seed):
        self.pos = np.array(pos, dtype=np.float64)
        self.prev = self.pos.copy()
        self.vel = np.array(vel, dtype=np.float64)
        self.age = 0.0
        self.life = ENEMY_SHOT_LIFE
        self.seed = seed
        self.bounced = False

    def fade(self):
        fade_in = min(self.age / 0.08, 1.0)
        fade_out = min(max((self.life - self.age) / 0.4, 0.0), 1.0)
        return min(fade_in, fade_out)

    def update(self, dt):
        self.prev[:] = self.pos                       # start of this frame's swept segment
        if self.bounced:
            self.vel[1] += GRAVITY * dt               # gravity only AFTER the deflection
        self.pos += self.vel * dt                     # semi-implicit Euler (new velocity first)
        self.age += dt

        # After a deflection the shot tumbles down and may bounce on the floor (y = 0).
        if self.bounced and self.pos[1] < ENEMY_SHOT_RADIUS:
            self.pos[1] = ENEMY_SHOT_RADIUS           # push back out of the floor
            if self.vel[1] < 0.0:
                self.vel[1] *= -0.45                  # floor bounce: reflect Y, keep 45 %
                self.vel[0] *= 0.7                    # friction on the horizontal speed
                self.vel[2] *= 0.7
            if abs(self.vel[1]) < 1.0:                # nearly at rest: start fading out soon
                self.life = min(self.life, self.age + 0.5)


def deflect_off_player(shot, center, radius, rng):
    """
    Test the shot against the player's collision sphere and, on contact, BOUNCE it.

    1) SWEPT SPHERE TEST (no tunnelling). The shot moved along the segment prev -> pos this
       frame. Find the point on that segment closest to the player's centre c:
            seg = pos - prev
            t   = clamp( dot(c - prev, seg) / dot(seg, seg), 0, 1 )
            closest = prev + seg * t
       If |closest - c| < radius + shot_radius the shot touched the player this frame.

    2) CONTACT NORMAL. n = (closest - c) / |closest - c| is the unit vector pointing from the
       player's centre out to the shot, i.e. the outward surface normal where it hit. (For an
       exactly head-on hit the distance is ~0, so we fall back to n = -normalize(v).)

    3) REFLECTION. Split the velocity into the part along the normal and the rest:
            v = (v . n) n  +  v_tangent
       A perfect mirror bounce flips only the normal part:
            v' = v_tangent - (v . n) n = v - 2 (v . n) n
       We only reflect when v . n < 0 (shot moving INTO the surface); otherwise it is
       already leaving and flipping it again would pull it back in. For a head-on hit
       n = -v/|v|, so v' = -v: the shot simply reverses.

    4) SCATTER + DAMPING. A mathematically perfect mirror looks robotic and would send the
       shot straight back at the artillery. We (a) multiply by 0.55 to lose energy,
       (b) add a random upward kick and (c) a random sideways kick. Gravity then (from this
       moment on) bends the path into an arc and the shot falls to the ground.

    5) DEPENETRATE. Move the shot to the sphere surface (centre + n * (radius + shot_radius))
       and reset `prev` to it, so the same frame can't register a second hit.
    Returns True if a bounce happened.
    """
    seg = shot.pos - shot.prev
    seg_len2 = float(np.dot(seg, seg))
    tt = 0.0 if seg_len2 < 1e-12 else min(max(float(np.dot(center - shot.prev, seg)) / seg_len2, 0.0), 1.0)
    closest = shot.prev + seg * tt
    off = closest - center
    dist = float(np.linalg.norm(off))
    if dist >= radius + ENEMY_SHOT_RADIUS:
        return False                                              # no contact

    if dist > 1e-5:
        n = off / dist                                            # outward normal at the contact point
    else:
        n = -shot.vel / max(np.linalg.norm(shot.vel), 1e-9)       # head-on fallback

    vn = float(np.dot(shot.vel, n))                               # speed component along the normal
    if vn < 0.0:                                                  # moving into the player: mirror it
        shot.vel = shot.vel - 2.0 * vn * n                        # v' = v - 2 (v.n) n
    shot.vel *= 0.55                                              # the bounce eats energy

    lateral = rng.normal(size=3) * np.array([1.6, 0.0, 1.6])      # random sideways scatter
    shot.vel += UP * rng.uniform(3.5, 6.5) + lateral              # random upward pop + scatter

    shot.pos = center + n * (radius + ENEMY_SHOT_RADIUS + 0.02)   # out of the sphere
    shot.prev = shot.pos.copy()
    shot.bounced = True                                           # gravity is applied from now on
    shot.life = min(shot.life, shot.age + 2.8)                    # it will despawn shortly
    return True


def staff_model_matrix(t, recoil):
    """
    Staff-local -> VIEW space (camera-relative) transform. Applied directly in
    view space and combined with the projection only, so the staff is locked
    to the screen whatever the camera does.
    """
    bob = 0.012 * math.sin(t * 1.7)
    return (translate(0.62, -0.95 + bob, -1.2 + 0.18 * recoil)
            @ rotate_z(math.radians(12.0))
            @ rotate_x(math.radians(-30.0 + 12.0 * recoil))
            @ scale(0.9))


# ----------------------------------------------------------------------------
# Ray vs. axis-aligned bounding box collision (the "slab method")
# ----------------------------------------------------------------------------
def raycast_boxes(origin, direction, box_min, box_max):
    """
    Cast the ray   P(t) = origin + direction * t   against EVERY box (AABB) at once.

    SLAB METHOD: an axis-aligned box is the intersection of three "slabs", one
    per axis (the space between its two parallel faces on that axis). For one
    axis the ray enters the slab at t1 = (min - origin) / direction and leaves
    it at t2 = (max - origin) / direction (swapped if the direction is
    negative). The ray is inside the BOX only while it is inside ALL THREE
    slabs at the same time, i.e. during
            [ t_near, t_far ] = [ max(entry t of x,y,z) , min(exit t of x,y,z) ].
    If t_near > t_far the ray leaves one slab before it enters another -> miss.

    Because `direction` here is the full movement vector of one frame
    (pos - prev), the segment itself is t in [0, 1]:
        * t_far  < 0  -> the box is behind the start point          -> no hit
        * t_near > 1  -> the box starts beyond the end of the frame  -> no hit (yet)
        * otherwise   -> the bolt touches the box THIS frame.
    The exact impact point is origin + direction * t_near.

    Axes where direction ~ 0 would divide by zero, so they get a tiny epsilon.

    Returns (box_index, t_near, t_far) for the NEAREST box hit, else None.
    Used for the monolith boxes, the creature boxes and the house boxes.
    """
    d = np.where(np.abs(direction) < 1e-9, 1e-9, direction)
    inv = 1.0 / d
    t1 = (box_min - origin) * inv
    t2 = (box_max - origin) * inv
    t_near = np.minimum(t1, t2).max(axis=1)
    t_far = np.maximum(t1, t2).min(axis=1)

    hit = (t_near <= t_far) & (t_far >= 0.0) & (t_near <= 1.0)
    if not hit.any():
        return None
    idx = np.where(hit)[0]
    best = idx[np.argmin(t_near[idx])]
    return int(best), float(t_near[best]), float(t_far[best])


# ----------------------------------------------------------------------------
# Creatures: part definitions, wander AI, shatter + debris physics
# ----------------------------------------------------------------------------
MESH_CUBE, MESH_SHARD = 0, 1
ROLE_BODY, ROLE_PLATE, ROLE_SPIKE = 0, 1, 2

# Each MELEE creature is 5 distinct primitives:
#   (mesh, offset from creature centre, half-extents, role, orbits_the_core)
PART_DEFS = [
    (MESH_CUBE,  (0.00,  0.00, 0.0), (0.34, 0.34, 0.34), ROLE_BODY,  False),   # central slate core cube
    (MESH_CUBE,  (0.62,  0.05, 0.0), (0.05, 0.36, 0.24), ROLE_PLATE, True),    # floating armour plate (right)
    (MESH_CUBE,  (-0.62, 0.05, 0.0), (0.05, 0.36, 0.24), ROLE_PLATE, True),    # floating armour plate (left)
    (MESH_SHARD, (0.00,  0.62, 0.0), (0.16, 0.40, 0.16), ROLE_SPIKE, False),   # crown spike
    (MESH_SHARD, (0.00, -0.55, 0.0), (0.13, 0.30, 0.13), ROLE_SPIKE, False),   # hanging shard
]

# Each ARTILLERY construct is also 5 primitives. Local +Z is the direction it faces.
#   (mesh, offset, half-extents, role)
ART_PART_DEFS = [
    (MESH_CUBE,  (0.00,  0.00,  0.00), (0.40, 0.40, 0.40), ROLE_BODY),    # heavy slate core with eye slit
    (MESH_CUBE,  (0.00, -0.22,  0.62), (0.10, 0.09, 0.36), ROLE_PLATE),   # long cannon barrel pointing forward
    (MESH_SHARD, (0.66,  0.05,  0.00), (0.11, 0.42, 0.11), ROLE_SPIKE),   # flanking spike (right)
    (MESH_SHARD, (-0.66, 0.05,  0.00), (0.11, 0.42, 0.11), ROLE_SPIKE),   # flanking spike (left)
    (MESH_CUBE,  (0.00,  0.52, -0.10), (0.36, 0.05, 0.26), ROLE_PLATE),   # armour plate on top
]


def random_target(rng):
    return rng.uniform(-MEADOW_HALF_SIZE + 4.0, MEADOW_HALF_SIZE - 4.0, 2)


def wrap_angle(a):
    """Wrap an angle difference into [-pi, pi]."""
    return (a + math.pi) % (2 * math.pi) - math.pi


class Creature:
    """A hovering violet-core construct: wanders between random waypoints, avoiding obstacles."""
    kind = "melee"
    palette = 0.0        # shader team: 0 = violet / magenta

    def __init__(self, xz, rng):
        self.pos = np.array([xz[0], CREATURE_HOVER, xz[1]], dtype=np.float64)
        self.yaw = rng.uniform(0, 2 * math.pi)
        self.target = random_target(rng)
        self.speed = CREATURE_SPEED * rng.uniform(0.8, 1.25)
        self.phase = rng.uniform(0, 2 * math.pi)
        self.seed = float(rng.random())
        self.alive = True

    def glow(self):
        """Energy multiplier uploaded to the shader (1 = normal glow)."""
        return 1.0

    def _avoid_and_clamp(self, dt, rng, tree_xz, tree_r):
        """Push away from obstacles (circles on the ground plane: monoliths + the house), stay in the meadow."""
        d = self.pos[[0, 2]] - tree_xz
        dist = np.linalg.norm(d, axis=1)
        close = np.where(dist < tree_r + 1.3)[0]
        for i in close:
            push = tree_r[i] + 1.3 - dist[i]
            self.pos[[0, 2]] += d[i] / max(dist[i], 1e-6) * push * min(1.0, 8.0 * dt)
            self.target = random_target(rng)

        lim = MEADOW_HALF_SIZE - 1.0
        self.pos[0] = max(-lim, min(lim, self.pos[0]))
        self.pos[2] = max(-lim, min(lim, self.pos[2]))

    def update(self, dt, t, rng, tree_xz, tree_r, player_pos):
        """Wander AI: steer toward a waypoint at a limited turn rate, hover, dodge obstacles."""
        to = self.target - self.pos[[0, 2]]
        if math.hypot(to[0], to[1]) < 1.5:                 # arrived: pick a new waypoint
            self.target = random_target(rng)
            to = self.target - self.pos[[0, 2]]

        # Heading uses forward = (sin yaw, cos yaw) on the XZ plane, so the angle
        # toward the waypoint is atan2(dx, dz). Wrap the difference into [-pi, pi].
        desired = math.atan2(to[0], to[1])
        diff = wrap_angle(desired - self.yaw)
        max_turn = 1.1 * dt                                # slow, menacing turning
        self.yaw += max(-max_turn, min(max_turn, diff))

        spd = self.speed * max(0.25, 1.0 - abs(diff) / math.pi)   # slow down in sharp turns
        self.pos[0] += math.sin(self.yaw) * spd * dt
        self.pos[2] += math.cos(self.yaw) * spd * dt

        self._avoid_and_clamp(dt, rng, tree_xz, tree_r)
        self.pos[1] = CREATURE_HOVER + 0.18 * math.sin(t * 1.6 + self.phase)   # hover bob
        return None                                        # melee constructs never shoot

    def part_transforms(self, t):
        """
        Current world pose of each part: list of (pos, R(3x3), half_extents, mesh, role).
        Plates orbit the core; spikes spin slowly; everything bobs a little so the
        pieces look like they float rather than being welded together.
        """
        out = []
        orbit = t * 0.9 + self.phase
        for i, (mesh, off, sc, role, orbits) in enumerate(PART_DEFS):
            off = np.array(off, dtype=np.float64)
            if orbits:
                side = 1.0 if off[0] > 0 else -1.0
                R = rot_y3(self.yaw + orbit) @ rot_z3(side * 0.30)   # jagged tilt
            elif role == ROLE_SPIKE:
                R = rot_y3(self.yaw + t * (1.2 if i == 3 else -1.2))
            else:
                R = rot_y3(self.yaw)
            ring = rot_y3(self.yaw + orbit) if orbits else rot_y3(self.yaw)
            p = self.pos + ring @ off
            p[1] += 0.06 * math.sin(t * 2.2 + self.phase + i)
            out.append((p, R, np.array(sc, dtype=np.float64), mesh, role))
        return out

    def aabb(self):
        """Bounding box used for bolt collision."""
        lo = self.pos - CREATURE_HALF
        hi = self.pos + np.array([CREATURE_HALF[0], CREATURE_TOP, CREATURE_HALF[2]])
        return lo, hi


class Artillery(Creature):
    """
    Ranged construct in Solar Amber. Behaviour:
      * it prioritises TURNING TO FACE THE PLAYER (a limited turn rate, so you can
        strafe around it and it has to keep swivelling),
      * it wanders slowly between waypoints and backs off if you get too close,
      * a cooldown timer counts down; once the player is in range, the cooldown is over
        and the cannon points at the player, it fires an EnemyShot aimed at the player's
        current camera position.
    """
    kind = "artillery"
    palette = 1.0        # shader team: 1 = solar amber / crimson gold

    def __init__(self, xz, rng):
        super().__init__(xz, rng)
        self.pos[1] = ARTILLERY_HOVER
        self.speed = 0.7 * rng.uniform(0.8, 1.2)       # slow drifters
        self.cooldown = rng.uniform(1.0, 3.0)          # seconds until the next shot may fire

    def glow(self):
        """Barrel/edges flare up during the last 0.7 s of the cooldown: a visible 'charging' telegraph."""
        return 1.0 + 1.4 * max(0.0, 1.0 - max(self.cooldown, 0.0) / 0.7)

    def update(self, dt, t, rng, tree_xz, tree_r, player_pos):
        # ---- 1) FACE THE PLAYER ----
        # Heading convention: forward = (sin yaw, cos yaw) on XZ, so the yaw that looks
        # at the player is atan2(dx, dz). Turn toward it at a limited angular speed.
        to_p = player_pos[[0, 2]] - self.pos[[0, 2]]
        dist = math.hypot(to_p[0], to_p[1])
        desired = math.atan2(to_p[0], to_p[1])
        diff = wrap_angle(desired - self.yaw)
        max_turn = ARTILLERY_TURN_RATE * dt
        self.yaw += max(-max_turn, min(max_turn, diff))
        aim_err = abs(wrap_angle(desired - self.yaw))    # remaining misalignment after turning

        # ---- 2) SLIGHT WANDER (independent of the facing direction: they strafe/hover) ----
        to = self.target - self.pos[[0, 2]]
        wd = math.hypot(to[0], to[1])
        if wd < 1.5:
            self.target = random_target(rng)
            to = self.target - self.pos[[0, 2]]
            wd = max(math.hypot(to[0], to[1]), 1e-6)
        self.pos[0] += to[0] / max(wd, 1e-6) * self.speed * dt
        self.pos[2] += to[1] / max(wd, 1e-6) * self.speed * dt
        if dist < 7.0 and dist > 1e-6:                   # too close: back away from the player
            self.pos[0] -= to_p[0] / dist * 1.6 * dt
            self.pos[2] -= to_p[1] / dist * 1.6 * dt

        self._avoid_and_clamp(dt, rng, tree_xz, tree_r)
        self.pos[1] = ARTILLERY_HOVER + 0.12 * math.sin(t * 1.3 + self.phase)

        # ---- 3) COOLDOWN + FIRE ----
        self.cooldown -= dt
        if dist < ARTILLERY_RANGE and self.cooldown <= 0.0 and aim_err < 0.30:
            self.cooldown = rng.uniform(*ARTILLERY_COOLDOWN)
            muzzle = self.pos + rot_y3(self.yaw) @ np.array([0.0, -0.22, 1.05])   # tip of the barrel
            aim = player_pos - muzzle                    # aimed at the player's CURRENT camera XYZ
            aim /= max(np.linalg.norm(aim), 1e-9)
            return EnemyShot(muzzle, aim * ENEMY_SHOT_SPEED, float(rng.random()))
        return None

    def part_transforms(self, t):
        """World pose of the 5 artillery parts. The body and barrel follow the yaw; the flanking spikes spin."""
        out = []
        base = rot_y3(self.yaw)
        for i, (mesh, off, sc, role) in enumerate(ART_PART_DEFS):
            off = np.array(off, dtype=np.float64)
            if role == ROLE_SPIKE:
                R = rot_y3(self.yaw + t * (1.6 if off[0] > 0 else -1.6))
            else:
                R = base
            p = self.pos + base @ off
            p[1] += 0.05 * math.sin(t * 2.0 + self.phase + i)
            out.append((p, R, np.array(sc, dtype=np.float64), mesh, role))
        return out


def spawn_entity(kind, rng, tree_xz, tree_r, avoid_xz):
    """Rejection-sample a spawn point: away from the player and from obstacles."""
    cls = Artillery if kind == "artillery" else Creature
    min_player = 14.0 if kind == "artillery" else 10.0
    for _ in range(80):
        xz = rng.uniform(-MEADOW_HALF_SIZE + 3, MEADOW_HALF_SIZE - 3, 2)
        if math.hypot(xz[0] - avoid_xz[0], xz[1] - avoid_xz[1]) < min_player:
            continue
        if np.any(np.linalg.norm(tree_xz - xz, axis=1) < tree_r + 2.5):
            continue
        return cls(xz, rng)
    return cls(np.array([20.0, -20.0]), rng)


class Debris:
    """
    One detached piece of a dead creature: a rigid body made only of
        position, linear velocity, orientation (3x3 matrix R) and angular velocity.
    No physics engine: update() is a handful of lines of kinematics.
    """
    __slots__ = ("pos", "vel", "R", "omega", "scale", "mesh", "role", "seed", "asleep")

    def __init__(self, pos, R, scale_, mesh, role, vel, omega, seed):
        self.pos = np.array(pos, dtype=np.float64)
        self.vel = np.array(vel, dtype=np.float64)
        self.R = np.array(R, dtype=np.float64)
        self.omega = np.array(omega, dtype=np.float64)   # angular velocity vector (rad/s)
        self.scale = np.array(scale_, dtype=np.float64)  # half-extents of the part
        self.mesh, self.role, self.seed = mesh, role, seed
        self.asleep = False

    def update(self, dt, rng):
        if self.asleep:
            return

        # ------------------------------------------------------------------
        # 1) LINEAR MOTION: semi-implicit (symplectic) Euler
        # ------------------------------------------------------------------
        # Gravity is a constant acceleration g along -Y. We update the velocity
        # FIRST and then use the NEW velocity to move the part:
        #       v <- v + g * dt
        #       p <- p + v * dt
        # (using the new v makes this stable and energy-friendly for bouncing.)
        self.vel[1] += GRAVITY * dt
        self.pos += self.vel * dt

        # ------------------------------------------------------------------
        # 2) ANGULAR MOTION: integrate the orientation matrix
        # ------------------------------------------------------------------
        # The angular velocity vector `omega` points along the spin axis and its
        # length is the spin rate in rad/s. Over one frame the part rotates by
        #       angle = |omega| * dt   about   axis = omega / |omega|.
        # We build that small rotation with Rodrigues' formula and LEFT-multiply
        # it onto the orientation (rotation about a WORLD axis => on the left).
        w = np.linalg.norm(self.omega)
        if w > 1e-6:
            self.R = orthonormalize(axis_angle_matrix(self.omega / w, w * dt) @ self.R)

        # ------------------------------------------------------------------
        # 3) FLOOR COLLISION (plane y = 0) for an ORIENTED box
        # ------------------------------------------------------------------
        # How far does the rotated box reach below its centre? Row 1 of R holds
        # the world-Y component of each local axis, so the box's half-height
        # along world Y is the support function
        #       extent = |R[1,0]|*sx + |R[1,1]|*sy + |R[1,2]|*sz.
        # A box lying flat has extent = its thin half-size; a box balanced on
        # a corner has a much bigger extent. The lowest point is pos.y - extent.
        extent = float(np.abs(self.R[1]) @ self.scale)
        if self.pos[1] <= extent:
            self.pos[1] = extent                         # push back out of the floor

            if self.vel[1] < 0.0:                        # moving INTO the floor: resolve the impact
                impact = -self.vel[1]
                if impact > BOUNCE_MIN_SPEED:
                    # Bounce: reflect the vertical velocity and keep only a fraction (restitution)
                    self.vel[1] = impact * RESTITUTION
                    # Friction: the contact steals part of the sideways speed
                    self.vel[0] *= FLOOR_FRICTION
                    self.vel[2] *= FLOOR_FRICTION
                    # Angular response, three pieces:
                    #  a) the impact absorbs a quarter of the spin,
                    #  b) ROLLING: a body rolling without slipping on a floor with
                    #     normal n and velocity v spins with  omega = (n x v) / r,
                    #     so we add that (scaled down) so pieces roll the way they travel,
                    #  c) a random kick proportional to impact speed, because real
                    #     bounces hit off-centre corners and make pieces tumble.
                    vh = np.array([self.vel[0], 0.0, self.vel[2]])
                    self.omega = (self.omega * 0.75
                                  + np.cross(UP, vh) / max(extent, 0.12) * 0.35
                                  + rng.normal(size=3) * impact * 0.25)
                else:
                    self.vel[1] = 0.0                    # too slow to bounce: resting contact

            # ---- Resting contact: continuous drag while touching the floor ----
            # exp(-k*dt) is a frame-rate-independent version of "multiply by 0.9 each step".
            self.vel[0] *= math.exp(-4.0 * dt)
            self.vel[2] *= math.exp(-4.0 * dt)
            self.omega *= math.exp(-2.5 * dt)

            horiz = math.hypot(self.vel[0], self.vel[2])
            if horiz < 2.0 and self.vel[1] < 0.5:
                # ---- Settling torque: let the piece topple onto a stable face ----
                # Pick the local axis that is most vertical, favouring SHORT axes
                # (weight 1/size) so thin plates lie flat and tall shards lie on
                # their side. `a` is that axis in world space, flipped to point up.
                # Rotating `a` toward world-up about axis (a x up) lays the part flat.
                j = int(np.argmax(np.abs(self.R[1]) / self.scale))
                a = self.R[:, j] * (1.0 if self.R[1, j] >= 0 else -1.0)
                ax = np.cross(a, UP)
                s = float(np.linalg.norm(ax))            # sin of the remaining tilt angle
                if s > 1e-6:
                    ang = math.asin(min(s, 1.0))
                    self.R = orthonormalize(
                        axis_angle_matrix(ax / s, ang * min(1.0, 6.0 * dt)) @ self.R)
                # Fall asleep once everything has (almost) stopped, to save CPU
                if (s < 0.03 and horiz < 0.15 and np.linalg.norm(self.omega) < 0.4
                        and abs(self.vel[1]) < 0.3):
                    self.asleep = True
                    self.vel[:] = 0.0
                    self.omega[:] = 0.0
                    self.pos[1] = float(np.abs(self.R[1]) @ self.scale)


def shatter_creature(creature, t, impact, bolt_dir, rng, debris):
    """
    Kinematic detachment: turn the creature's live parts into free rigid bodies.
    Works for BOTH construct types (it only asks the creature for its part poses).
    Every part is given
      * an OUTWARD velocity: the direction from the impact point to the part's
        centre (so pieces fly away from where the bolt struck), plus a share of
        the bolt's own momentum and an upward pop,
      * a random ANGULAR velocity (random unit axis * random spin rate).
    Gravity, bouncing and friction then take over in Debris.update().
    """
    for pos, R, sc, mesh, role in creature.part_transforms(t):
        out = pos - impact
        n = np.linalg.norm(out)
        out = out / n if n > 1e-3 else rng.normal(size=3) / 1.7   # degenerate: any direction
        vel = (out * rng.uniform(4.0, 8.0)                        # explosive outward burst
               + bolt_dir * rng.uniform(3.0, 6.0)                 # momentum of the bolt
               + UP * rng.uniform(2.0, 5.0))                      # upward pop
        axis = rng.normal(size=3)
        axis /= np.linalg.norm(axis)
        omega = axis * rng.uniform(4.0, 14.0)                     # tumbling spin (rad/s)
        debris.append(Debris(pos, R, sc, mesh, role, vel, omega, creature.seed))
    while len(debris) > MAX_DEBRIS:                               # recycle the oldest pieces
        debris.pop(0)


# ----------------------------------------------------------------------------
# Procedural geometry
# ----------------------------------------------------------------------------
def build_blade_mesh(segments=4):
    """
    One blade of grass: a tapered strip with `segments` quads whose width
    narrows to a single point at the tip.
    Vertex layout (x, y, z):  x = side offset [-0.5, 0.5], y = height fraction [0, 1]
    """
    verts = []
    for i in range(segments):
        y = i / segments
        half = 0.5 * (1.0 - y) ** 0.8
        verts.append((-half, y, 0.0))
        verts.append(( half, y, 0.0))
    verts.append((0.0, 1.0, 0.0))

    idx = []
    for i in range(segments - 1):
        bl, br = 2 * i, 2 * i + 1
        tl, tr = 2 * i + 2, 2 * i + 3
        idx += [bl, br, tl,  br, tr, tl]
    last_l, last_r = 2 * (segments - 1), 2 * (segments - 1) + 1
    idx += [last_l, last_r, 2 * segments]
    return np.array(verts, dtype=np.float32), np.array(idx, dtype=np.uint32)


def build_instance_data(count, half_size, seed=1337):
    """Per-instance data: [x, y, z, random] for every blade."""
    rng = np.random.default_rng(seed)
    x = rng.uniform(-half_size, half_size, count)
    z = rng.uniform(-half_size, half_size, count)
    y = np.zeros(count)
    r = rng.uniform(0.0, 1.0, count)
    return np.stack([x, y, z, r], axis=1).astype(np.float32)


def build_pillar_mesh():
    """
    Unit slate pillar: a stretched cube with x,z in [-1, 1] and y in [0, 1].
    Each face is CCW seen from OUTSIDE so gl_FrontFacing detects the hollow interior.
    Vertex layout (6 floats): position(3), normal(3).
    """
    faces = [
        ((1, 0, 0),  [(1, 0, -1), (1, 0, 1), (1, 1, 1), (1, 1, -1)]),
        ((-1, 0, 0), [(-1, 0, -1), (-1, 0, 1), (-1, 1, 1), (-1, 1, -1)]),
        ((0, 0, 1),  [(-1, 0, 1), (1, 0, 1), (1, 1, 1), (-1, 1, 1)]),
        ((0, 0, -1), [(-1, 0, -1), (1, 0, -1), (1, 1, -1), (-1, 1, -1)]),
        ((0, 1, 0),  [(-1, 1, -1), (1, 1, -1), (1, 1, 1), (-1, 1, 1)]),
        ((0, -1, 0), [(-1, 0, -1), (1, 0, -1), (1, 0, 1), (-1, 0, 1)]),
    ]
    out = []
    for n, (a, b, c, d) in faces:
        n = np.array(n, dtype=np.float32)
        for tri in ((a, b, c), (a, c, d)):
            p0, p1, p2 = (np.array(v, dtype=np.float32) for v in tri)
            if np.dot(np.cross(p1 - p0, p2 - p0), n) < 0:
                p1, p2 = p2, p1
            for p in (p0, p1, p2):
                out.append([*p, *n])
    return np.array(out, dtype=np.float32)


def build_tree_data(count, half_size, avoid_xz, avoid_circles=(), seed=77):
    """
    Scatter `count` monoliths by rejection sampling (away from the spawn point, from each
    other and from every (x, z, radius) circle in `avoid_circles`, e.g. the house).
    Per-instance layout (7 floats): x, y(=0), z, seed, half_x, height, half_z
    """
    rng = np.random.default_rng(seed)
    placed = []
    for _ in range(10_000):
        if len(placed) >= count:
            break
        x, z = rng.uniform(-half_size + 2, half_size - 2, 2)
        if math.hypot(x - avoid_xz[0], z - avoid_xz[1]) < 6.0:
            continue
        if any(math.hypot(x - cx, z - cz) < r for cx, cz, r in avoid_circles):
            continue
        if any(math.hypot(x - p[0], z - p[2]) < 5.0 for p in placed):
            continue
        hx, hz = rng.uniform(0.45, 0.85, 2)
        h = rng.uniform(6.0, 13.0)
        placed.append((x, 0.0, z, rng.random(), hx, h, hz))
    return np.array(placed, dtype=np.float32)


def build_house_mesh(cx, cz, hx, hz, wall_h, roof_h, overhang):
    """
    COMPOSITE GEOMETRY: the whole house is ONE static triangle mesh built from simple
    primitives, with its world position (cx, cz) baked straight into the vertices.

        Part 0  WALLS    4 side faces of a big box (the "large cube"; no top/bottom, the
                         roof covers the top and the ground plane is the floor)
        Part 1  ROOF     a TRIANGULAR PRISM lying on its side: 2 sloped quads, 1 underside
                         quad and 2 triangular gable ends (the gables use part 0 = wall)
        Part 2  WINDOWS  small flat rectangles floated 3 cm OUT from the wall, so they
                         never z-fight with it
        Part 3  DOOR     one tall flat rectangle on the front (+Z) wall

    Vertex layout (9 floats): position(3), normal(3), part(1), uv(2).

    WINDING / NORMALS: every triangle must be counter-clockwise seen from OUTSIDE (so
    gl_FrontFacing can tell inside from outside, and the lighting normal points outward).
    Rather than hand-ordering every corner, `add_tri` computes the geometric normal with a
    cross product and compares it to an "outward reference":
        * for CONVEX parts (box, prism) the reference is (triangle centroid - part centre),
          which always points outward,
        * for flat windows / the door it is the wall's known outward normal.
    If the cross product points the wrong way, two vertices (and their UVs) are swapped,
    which flips the winding. So the corner order given below does not have to be perfect.
    """
    out = []

    def add_tri(a, b, c, part, uvs, center=None, normal=None):
        a, b, c = (np.array(v, dtype=np.float32) for v in (a, b, c))
        uvs = list(uvs)
        n = np.cross(b - a, c - a)
        ref = normal if normal is not None else (a + b + c) / 3.0 - np.array(center, dtype=np.float32)
        if np.dot(n, ref) < 0:                        # wrong winding: swap two corners (and their UVs)
            b, c = c, b
            uvs[1], uvs[2] = uvs[2], uvs[1]
            n = -n
        n = n / (np.linalg.norm(n) + 1e-9)
        for v, uv in zip((a, b, c), uvs):
            out.append([*v, *n, float(part), *uv])

    def add_quad(p0, p1, p2, p3, part, center=None, normal=None):
        """A quad = two triangles; UVs run (0,0) (1,0) (1,1) (0,1) around the corners."""
        uv = ((0, 0), (1, 0), (1, 1), (0, 1))
        add_tri(p0, p1, p2, part, (uv[0], uv[1], uv[2]), center, normal)
        add_tri(p0, p2, p3, part, (uv[0], uv[2], uv[3]), center, normal)

    def add_panel(centre, u_axis, normal, w, h, part):
        """
        A flat rectangle (window or door) lying ON a wall: `centre` is on the wall surface,
        `u_axis` runs along the wall horizontally, world Y runs vertically, and `normal`
        is the outward direction of the wall. The panel is pushed 0.03 units out along the
        normal so it sits just in front of the wall.
        """
        c = np.array(centre, dtype=np.float32) + np.array(normal, dtype=np.float32) * 0.03
        u = np.array(u_axis, dtype=np.float32)
        v = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        add_quad(c - u * w / 2 - v * h / 2, c + u * w / 2 - v * h / 2,
                 c + u * w / 2 + v * h / 2, c - u * w / 2 + v * h / 2,
                 part, normal=np.array(normal, dtype=np.float32))

    x0, x1 = cx - hx, cx + hx          # wall extents on X
    z0, z1 = cz - hz, cz + hz          # wall extents on Z
    body_c = (cx, wall_h / 2, cz)      # centre of the box (orientation reference)

    # ------------------------------------------------------------------
    # Part 0: the main building, a big box. Four side faces as quads.
    # ------------------------------------------------------------------
    add_quad((x0, 0, z1), (x1, 0, z1), (x1, wall_h, z1), (x0, wall_h, z1), 0, center=body_c)   # front (+Z)
    add_quad((x1, 0, z0), (x0, 0, z0), (x0, wall_h, z0), (x1, wall_h, z0), 0, center=body_c)   # back  (-Z)
    add_quad((x0, 0, z0), (x0, 0, z1), (x0, wall_h, z1), (x0, wall_h, z0), 0, center=body_c)   # left  (-X)
    add_quad((x1, 0, z1), (x1, 0, z0), (x1, wall_h, z0), (x1, wall_h, z1), 0, center=body_c)   # right (+X)

    # ------------------------------------------------------------------
    # Part 1: the roof, a triangular prism. Its cross-section (in the XY... here ZY plane)
    # is a triangle: two eave corners at wall height and a ridge in the middle. The prism
    # is extruded along X, and is wider than the walls by `overhang` so the eaves stick out.
    #
    #                 ridge (top)                 ridge_L ------------ ridge_R
    #                  /\\                          /                      /
    #                 /  \\        extruded       /   (two sloped faces)  /
    #        eave_B  /____\\ eave_F   along X -> BL ----------------- BR   (and FL / FR in front)
    # ------------------------------------------------------------------
    ox, oz = hx + overhang, hz + overhang
    top = wall_h + roof_h
    FL, FR = (-ox + cx, wall_h, cz + oz), (ox + cx, wall_h, cz + oz)      # front eave, left / right end
    BL, BR = (-ox + cx, wall_h, cz - oz), (ox + cx, wall_h, cz - oz)      # back eave, left / right end
    RL, RR = (-ox + cx, top, cz), (ox + cx, top, cz)                       # ridge, left / right end
    roof_c = (cx, wall_h + roof_h / 3.0, cz)                               # centroid-ish point inside the prism

    add_quad(FL, FR, RR, RL, 1, center=roof_c)          # front slope
    add_quad(BR, BL, RL, RR, 1, center=roof_c)          # back slope
    add_quad(FL, FR, BR, BL, 1, center=roof_c)          # underside (visible under the overhang)
    uv3 = ((0, 0), (1, 0), (0.5, 1))
    add_tri(FL, BL, RL, 0, uv3, center=roof_c)          # left gable triangle (wall material)
    add_tri(FR, BR, RR, 0, uv3, center=roof_c)          # right gable triangle

    # ------------------------------------------------------------------
    # Part 2: windows (flat rectangles slightly offset from the walls).
    # ------------------------------------------------------------------
    win_y = 1.6
    add_panel((cx - 1.5, win_y, z1), (1, 0, 0), (0, 0, 1), 0.9, 0.95, 2)    # front, left of the door
    add_panel((cx + 1.5, win_y, z1), (1, 0, 0), (0, 0, 1), 0.9, 0.95, 2)    # front, right of the door
    add_panel((cx, win_y, z0), (1, 0, 0), (0, 0, -1), 1.2, 0.95, 2)         # back wall
    add_panel((x0, win_y, cz), (0, 0, 1), (-1, 0, 0), 1.0, 0.95, 2)         # left wall
    add_panel((x1, win_y, cz), (0, 0, 1), (1, 0, 0), 1.0, 0.95, 2)          # right wall

    # ------------------------------------------------------------------
    # Part 3: the front door.
    # ------------------------------------------------------------------
    add_panel((cx, 0.95, z1), (1, 0, 0), (0, 0, 1), 0.95, 1.9, 3)

    return np.array(out, dtype=np.float32)


def flat_shaded(tris):
    """
    Turn triangles of a CONVEX shape centred on the origin into flat-shaded
    vertices [position(3), normal(3)]. Winding is fixed so every face is CCW
    seen from outside (the normal must point away from the origin).
    """
    out = []
    for a, b, c in tris:
        a, b, c = (np.array(v, dtype=np.float32) for v in (a, b, c))
        n = np.cross(b - a, c - a)
        if np.dot(n, (a + b + c) / 3.0) < 0:
            b, c = c, b
            n = -n
        n = n / (np.linalg.norm(n) + 1e-9)
        for v in (a, b, c):
            out.append([*v, *n])
    return np.array(out, dtype=np.float32)


def build_cube_mesh():
    """Unit cube, half-extent 1, centred on the origin (12 triangles)."""
    tris = []
    for axis in range(3):
        u, v = (axis + 1) % 3, (axis + 2) % 3
        for s in (-1.0, 1.0):
            corners = []
            for cu, cv in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                p = [0.0, 0.0, 0.0]
                p[axis], p[u], p[v] = s, float(cu), float(cv)
                corners.append(tuple(p))
            tris += [(corners[0], corners[1], corners[2]), (corners[0], corners[2], corners[3])]
    return flat_shaded(tris)


def build_shard_mesh():
    """
    A jagged bipyramid ("crystal shard"): two needle tips at y = +-1 and a
    slightly irregular, non-planar middle ring, so no two faces look alike.
    """
    top, bot = (0.0, 1.0, 0.0), (0.0, -1.0, 0.0)
    ring = [(1.0, 0.12, 0.0), (0.0, -0.10, 0.9), (-0.85, 0.05, 0.0), (0.0, 0.08, -1.0)]
    tris = []
    for i in range(4):
        a, b = ring[i], ring[(i + 1) % 4]
        tris += [(top, a, b), (bot, b, a)]
    return flat_shaded(tris)


def build_staff_mesh():
    """
    Low-poly arcane staff: a tapered 6-sided slate shaft topped by a hexagonal
    glass crystal. Vertex layout (7 floats): position(3), normal(3), part(1).
    """
    out = []

    def add_convex(tris, center, part):
        center = np.array(center, dtype=np.float32)
        for a, b, c in tris:
            a, b, c = (np.array(v, dtype=np.float32) for v in (a, b, c))
            n = np.cross(b - a, c - a)
            if np.dot(n, (a + b + c) / 3.0 - center) < 0:
                b, c = c, b
                n = -n
            n = n / (np.linalg.norm(n) + 1e-9)
            for v in (a, b, c):
                out.append([*v, *n, part])

    def ring(radius, y, n, phase=0.0):
        return [(radius * math.cos(phase + 2 * math.pi * i / n), y,
                 radius * math.sin(phase + 2 * math.pi * i / n)) for i in range(n)]

    N = 6
    bot, top = ring(0.035, -0.90, N), ring(0.024, 0.58, N)
    cb, ct = (0.0, -0.90, 0.0), (0.0, 0.58, 0.0)
    tris = []
    for i in range(N):
        j = (i + 1) % N
        tris += [(bot[i], bot[j], top[j]), (bot[i], top[j], top[i]),
                 (cb, bot[j], bot[i]), (ct, top[i], top[j])]
    add_convex(tris, (0.0, -0.16, 0.0), 0.0)

    ra = ring(0.10, 0.80, N, phase=math.pi / N)
    rb = ring(0.10, 0.92, N, phase=math.pi / N)
    apex_lo, apex_hi = (0.0, 0.62, 0.0), (0.0, 1.22, 0.0)
    tris = []
    for i in range(N):
        j = (i + 1) % N
        tris += [(apex_lo, ra[j], ra[i]),
                 (ra[i], ra[j], rb[j]), (ra[i], rb[j], rb[i]),
                 (apex_hi, rb[i], rb[j])]
    add_convex(tris, (0.0, 0.92, 0.0), 1.0)

    return np.array(out, dtype=np.float32)


def build_crosshair_vertices(width, height, gap=6, length=9, thick=2):
    """Four small bars around the screen centre, converted from pixels to NDC."""
    sx, sy = 2.0 / width, 2.0 / height
    def rect(cx, cy, w, h):
        x0, x1, y0, y1 = (cx - w / 2) * sx, (cx + w / 2) * sx, (cy - h / 2) * sy, (cy + h / 2) * sy
        return [x0, y0, x1, y0, x1, y1,  x0, y0, x1, y1, x0, y1]
    off = gap + length / 2
    v = (rect(-off, 0, length, thick) + rect(off, 0, length, thick) +
         rect(0, -off, thick, length) + rect(0, off, thick, length))
    return np.array(v, dtype=np.float32)


def pack_part_instances(creatures, debris, t):
    """
    Build the per-instance float arrays for the two creature meshes.
    Row layout (19 floats): R col0(3), R col1(3), R col2(3), position(3),
                            half-extents(3), params(4) = [energy, seed, role, team]
    Alive constructs upload energy = their glow() (1.0, or more while charging a shot);
    debris ALWAYS uploads energy = 0.0, which is what instantly "turns off" the glow on death.
    `team` (0 violet / 1 amber) selects the palette in the fragment shader.
    """
    rows = {MESH_CUBE: [], MESH_SHARD: []}

    def add(mesh, pos, R, sc, energy, seed, role, team):
        rows[mesh].append([*R[:, 0], *R[:, 1], *R[:, 2], *pos, *sc, energy, seed, float(role), team])

    for c in creatures:
        g = c.glow()
        for pos, R, sc, mesh, role in c.part_transforms(t):
            add(mesh, pos, R, sc, g, c.seed, role, c.palette)
    for d in debris:
        add(d.mesh, d.pos, d.R, d.scale, 0.0, d.seed, d.role, 0.0)

    return {m: (np.array(r, dtype=np.float32) if r else np.zeros((0, 19), dtype=np.float32))
            for m, r in rows.items()}


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main():
    pygame.init()

    # Request a modern core-profile OpenGL 3.3 context (needed for #version 330 core)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK,
                                    pygame.GL_CONTEXT_PROFILE_CORE)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True)
    pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)

    pygame.display.set_mode((WIDTH, HEIGHT),
                            pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE)
    pygame.display.set_caption("Voxel Meadow Instancing")

    # ------------------------------------------------------------------
    # MOUSE CAPTURE  (the heart of the 360-degree fix)
    # ------------------------------------------------------------------
    # WHY THE OLD CAMERA GOT STUCK: a normal desktop cursor is an ABSOLUTE pointer. It
    # stops at the screen/window edge, so once it touches the edge the OS reports
    # dx = 0 no matter how far your hand keeps moving: you cannot turn any further.
    #
    # THE FIX: put the mouse in RELATIVE mode. The OS then reports raw hardware motion
    # (how far the mouse physically moved) and the cursor itself never travels, so
    # there is no edge to hit.
    #   * set_visible(False)  hides the cursor.
    #   * set_grab(True)      confines the pointer to our window (and, in pygame 2/SDL2,
    #                         hiding + grabbing together enables SDL's relative mode).
    #   * set_relative_mode() (pygame-ce) asks for relative mode explicitly where available.
    # If a platform still lets the cursor drift (some Linux/Wayland/VM setups), the
    # `recentre_if_near_edge()` guard below warps it back to the middle, so the
    # cursor can never reach an edge on any setup.
    has_relative_api = hasattr(pygame.mouse, "set_relative_mode")
    mouse_captured = False

    def capture_mouse(on):
        """Hide + lock (on=True) or show + release (on=False) the mouse."""
        nonlocal mouse_captured
        mouse_captured = on
        pygame.mouse.set_visible(not on)          # cursor hidden while playing
        pygame.event.set_grab(on)                 # confine the pointer to this window
        if has_relative_api:
            try:
                pygame.mouse.set_relative_mode(on)    # raw, unbounded motion deltas
            except pygame.error:
                pass
        pygame.mouse.get_rel()                    # DISCARD whatever motion accumulated before
                                                  # (otherwise the first frame would jump)

    def recentre_if_near_edge():
        """
        Safety net for platforms where grabbing does not give true relative motion.
        If the (hidden) cursor wandered into the outer part of the window, teleport it
        back to the centre. We then pump events and call get_rel() once to throw away
        the artificial "jump" the teleport itself generates, so the camera does not
        twitch. In true relative mode the cursor never moves, so this never fires.
        """
        w, h = pygame.display.get_window_size()
        x, y = pygame.mouse.get_pos()
        if x < w * 0.25 or x > w * 0.75 or y < h * 0.25 or y > h * 0.75:
            pygame.mouse.set_pos((w // 2, h // 2))
            pygame.event.pump()
            pygame.mouse.get_rel()

    capture_mouse(True)

    # ------------------------------------------------------------------
    # ModernGL context + programs
    # ------------------------------------------------------------------
    ctx = moderngl.create_context()
    ctx.enable(moderngl.DEPTH_TEST)

    sky_prog = ctx.program(vertex_shader=prep(SKY_VERTEX_SHADER),
                           fragment_shader=prep(SKY_FRAGMENT_SHADER))
    grass_prog = ctx.program(vertex_shader=prep(GRASS_VERTEX_SHADER),
                             fragment_shader=prep(GRASS_FRAGMENT_SHADER))
    ground_prog = ctx.program(vertex_shader=prep(GROUND_VERTEX_SHADER),
                              fragment_shader=prep(GROUND_FRAGMENT_SHADER))
    tree_prog = ctx.program(vertex_shader=prep(TREE_VERTEX_SHADER),
                            fragment_shader=prep(TREE_FRAGMENT_SHADER))
    house_prog = ctx.program(vertex_shader=prep(HOUSE_VERTEX_SHADER),
                             fragment_shader=prep(HOUSE_FRAGMENT_SHADER))
    creature_prog = ctx.program(vertex_shader=prep(CREATURE_VERTEX_SHADER),
                                fragment_shader=prep(CREATURE_FRAGMENT_SHADER))
    # Two programs from the SAME bolt shaders: only the palette uniforms differ.
    bolt_prog = ctx.program(vertex_shader=prep(BOLT_VERTEX_SHADER),
                            fragment_shader=prep(BOLT_FRAGMENT_SHADER))
    enemy_bolt_prog = ctx.program(vertex_shader=prep(BOLT_VERTEX_SHADER),
                                  fragment_shader=prep(BOLT_FRAGMENT_SHADER))
    staff_prog = ctx.program(vertex_shader=prep(STAFF_VERTEX_SHADER),
                             fragment_shader=prep(STAFF_FRAGMENT_SHADER))
    cross_prog = ctx.program(vertex_shader=prep(CROSS_VERTEX_SHADER),
                             fragment_shader=prep(CROSS_FRAGMENT_SHADER))

    # Player bolts: arcane cyan + emerald. Enemy shots: crimson + solar amber.
    bolt_prog["u_col_a"].value = (0.00, 0.85, 1.00)
    bolt_prog["u_col_b"].value = (0.05, 1.00, 0.40)
    bolt_prog["u_core"].value = (0.65, 1.00, 0.92)
    bolt_prog["u_size"].value = 0.6
    enemy_bolt_prog["u_col_a"].value = (1.00, 0.12, 0.05)
    enemy_bolt_prog["u_col_b"].value = (1.00, 0.62, 0.02)
    enemy_bolt_prog["u_core"].value = (1.00, 0.92, 0.55)
    enemy_bolt_prog["u_size"].value = 0.45

    # ------------------------------------------------------------------
    # Sky: one oversized triangle that covers the whole screen
    # ------------------------------------------------------------------
    sky_tri = np.array([-1, -1,  3, -1,  -1, 3], dtype=np.float32)
    sky_vbo = ctx.buffer(sky_tri.tobytes())
    sky_vao = ctx.vertex_array(sky_prog, [(sky_vbo, "2f", "in_pos")])
    sky_prog["u_sun_dir"].value = tuple(SUN_DIR)
    sky_prog["u_tan_half_fov"].value = math.tan(math.radians(FOV_Y_DEG) / 2.0)

    # ------------------------------------------------------------------
    # HARDWARE INSTANCING SETUP: grass meadow
    # ------------------------------------------------------------------
    blade_verts, blade_indices = build_blade_mesh(segments=4)
    blade_vbo = ctx.buffer(blade_verts.tobytes())
    blade_ibo = ctx.buffer(blade_indices.tobytes())

    instance_data = build_instance_data(BLADE_COUNT, MEADOW_HALF_SIZE)
    instance_vbo = ctx.buffer(instance_data.tobytes())

    # '3f' advances per VERTEX; '4f/i' (the "/i" suffix = divisor 1) advances per INSTANCE.
    grass_vao = ctx.vertex_array(
        grass_prog,
        [
            (blade_vbo,    "3f",   "in_vert"),
            (instance_vbo, "4f/i", "in_offset"),
        ],
        index_buffer=blade_ibo,
    )

    # Ground plane
    g, gy = GROUND_HALF_SIZE, -0.01
    ground_verts = np.array([
        -g, gy, -g,   g, gy, -g,   g, gy,  g,
        -g, gy, -g,   g, gy,  g,  -g, gy,  g,
    ], dtype=np.float32)
    ground_vbo = ctx.buffer(ground_verts.tobytes())
    ground_vao = ctx.vertex_array(ground_prog, [(ground_vbo, "3f", "in_position")])

    # ------------------------------------------------------------------
    # The cozy house: one static composite mesh + its collision boxes
    # ------------------------------------------------------------------
    hcx, hcz = HOUSE_CENTER
    hhx, hhz = HOUSE_HALF
    house_data = build_house_mesh(hcx, hcz, hhx, hhz, HOUSE_WALL_H, HOUSE_ROOF_H, HOUSE_OVERHANG)
    house_vbo = ctx.buffer(house_data.tobytes())
    house_vao = ctx.vertex_array(
        house_prog, [(house_vbo, "3f 3f 1f 2f", "in_pos", "in_normal", "in_part", "in_uv")])
    house_vertex_count = len(house_data)

    # Two AABBs: the wall box, and the roof's bounding box (it also contains the empty triangle
    # corners above the slopes: a tiny inaccuracy that is fine for bolt collision).
    ov = HOUSE_OVERHANG
    house_min = np.array([[hcx - hhx, 0.0, hcz - hhz],
                          [hcx - hhx - ov, HOUSE_WALL_H, hcz - hhz - ov]], dtype=np.float64)
    house_max = np.array([[hcx + hhx, HOUSE_WALL_H, hcz + hhz],
                          [hcx + hhx + ov, HOUSE_WALL_H + HOUSE_ROOF_H, hcz + hhz + ov]], dtype=np.float64)

    house_prog["u_sun_dir"].value = tuple(SUN_DIR)
    house_prog["u_light_pos"].value = (hcx, 1.6, hcz + hhz + 1.2)    # warm light just in front of the door
    ground_prog["u_house_rect"].value = (hcx, hcz, hhx, hhz)

    # ------------------------------------------------------------------
    # HARDWARE INSTANCING SETUP: slate monoliths ("trees")
    # ------------------------------------------------------------------
    pillar_data = build_pillar_mesh()
    pillar_vbo = ctx.buffer(pillar_data.tobytes())

    tree_data = build_tree_data(TREE_COUNT, MEADOW_HALF_SIZE, avoid_xz=(0.0, 12.0),
                                avoid_circles=[(hcx, hcz, 7.5)])      # keep pillars away from the house
    tree_count = len(tree_data)
    tree_instance_vbo = ctx.buffer(tree_data.tobytes())
    tree_vao = ctx.vertex_array(
        tree_prog,
        [
            (pillar_vbo,        "3f 3f",  "in_vert", "in_normal"),
            (tree_instance_vbo, "4f 3f/i", "in_base", "in_size"),
        ],
    )

    # Collision boxes (AABBs), float64 for robust slab math.
    t64 = tree_data.astype(np.float64)
    box_min = np.stack([t64[:, 0] - t64[:, 4], np.zeros(tree_count), t64[:, 2] - t64[:, 6]], axis=1)
    box_max = np.stack([t64[:, 0] + t64[:, 4], t64[:, 5],            t64[:, 2] + t64[:, 6]], axis=1)

    # Everything solid for ENEMY shots: monoliths + house boxes
    solid_min = np.vstack([box_min, house_min])
    solid_max = np.vstack([box_max, house_max])

    # Circles on the ground plane for the constructs' obstacle avoidance: monoliths + the house
    tree_xz = np.vstack([t64[:, [0, 2]], [[hcx, hcz]]])
    tree_r = np.append(np.maximum(t64[:, 4], t64[:, 6]) * 1.42,    # radius that encloses the box corners
                       math.hypot(hhx + ov, hhz + ov))             # radius that encloses the roof

    # ------------------------------------------------------------------
    # HARDWARE INSTANCING SETUP: creature parts (cube mesh + shard mesh)
    # ------------------------------------------------------------------
    # Both meshes use the SAME shader and the SAME 19-float instance layout, and each
    # has its own dynamic instance buffer that is rewritten every frame.
    cube_vbo = ctx.buffer(build_cube_mesh().tobytes())
    shard_mesh_data = build_shard_mesh()
    shard_vbo = ctx.buffer(shard_mesh_data.tobytes())
    cube_vertex_count = len(build_cube_mesh())
    shard_vertex_count = len(shard_mesh_data)

    inst_fmt = "3f 3f 3f 3f 3f 4f/i"
    inst_names = ("in_r0", "in_r1", "in_r2", "in_ipos", "in_scale", "in_params")
    cube_inst_vbo = ctx.buffer(reserve=MAX_PART_INSTANCES * 19 * 4, dynamic=True)
    shard_inst_vbo = ctx.buffer(reserve=MAX_PART_INSTANCES * 19 * 4, dynamic=True)
    cube_vao = ctx.vertex_array(
        creature_prog,
        [(cube_vbo, "3f 3f", "in_vert", "in_normal"), (cube_inst_vbo, inst_fmt, *inst_names)])
    shard_vao = ctx.vertex_array(
        creature_prog,
        [(shard_vbo, "3f 3f", "in_vert", "in_normal"), (shard_inst_vbo, inst_fmt, *inst_names)])
    creature_vaos = {MESH_CUBE: (cube_vao, cube_inst_vbo, cube_vertex_count),
                     MESH_SHARD: (shard_vao, shard_inst_vbo, shard_vertex_count)}

    # ------------------------------------------------------------------
    # HARDWARE INSTANCING SETUP: plasma orbs (DYNAMIC instance buffers)
    # ------------------------------------------------------------------
    quad = np.array([-1, -1,  1, -1,  1, 1,
                     -1, -1,  1,  1, -1, 1], dtype=np.float32)
    quad_vbo = ctx.buffer(quad.tobytes())

    # Player bolts
    bolt_instance_vbo = ctx.buffer(reserve=MAX_FIREBALLS * 5 * 4, dynamic=True)
    bolt_vao = ctx.vertex_array(
        bolt_prog,
        [
            (quad_vbo,          "2f",         "in_quad"),
            (bolt_instance_vbo, "3f 1f 1f/i", "in_center", "in_seed", "in_fade"),
        ],
    )
    # Enemy shots: same layout, separate buffer and program (amber palette)
    enemy_instance_vbo = ctx.buffer(reserve=MAX_ENEMY_SHOTS * 5 * 4, dynamic=True)
    enemy_bolt_vao = ctx.vertex_array(
        enemy_bolt_prog,
        [
            (quad_vbo,            "2f",         "in_quad"),
            (enemy_instance_vbo,  "3f 1f 1f/i", "in_center", "in_seed", "in_fade"),
        ],
    )

    # ------------------------------------------------------------------
    # Staff view-model + crosshair buffers
    # ------------------------------------------------------------------
    staff_data = build_staff_mesh()
    staff_vbo = ctx.buffer(staff_data.tobytes())
    staff_vao = ctx.vertex_array(staff_prog,
                                 [(staff_vbo, "3f 3f 1f", "in_pos", "in_normal", "in_part")])
    staff_vertex_count = len(staff_data)

    cross_vbo = ctx.buffer(build_crosshair_vertices(WIDTH, HEIGHT).tobytes())
    cross_vao = ctx.vertex_array(cross_prog, [(cross_vbo, "2f", "in_pos")])
    cross_vertex_count = 24

    # ------------------------------------------------------------------
    # Scene state
    # ------------------------------------------------------------------
    camera = FPSCamera(position=(0.0, 1.6, 12.0))
    clock = pygame.time.Clock()
    start_ms = pygame.time.get_ticks()
    rng = np.random.default_rng(2024)

    fireballs = []     # live player Fireball objects
    enemy_shots = []   # SEPARATE list: live enemy projectiles (EnemyShot)
    deflections = 0    # how many enemy shots have bounced off the player so far
    hit_points = []    # world-space impact coordinates handed to the tree shader (capped)
    recoil = 0.0
    running = True

    spawn_avoid = (camera.position[0], camera.position[2])
    creatures = ([spawn_entity("melee", rng, tree_xz, tree_r, spawn_avoid) for _ in range(CREATURE_COUNT)]
                 + [spawn_entity("artillery", rng, tree_xz, tree_r, spawn_avoid) for _ in range(ARTILLERY_COUNT)])
    debris = []             # tumbling pieces of dead constructs
    respawn_timers = []     # [seconds left, kind] for each destroyed construct

    # ------------------------------------------------------------------
    # Window size / FULLSCREEN handling
    # ------------------------------------------------------------------
    win_w, win_h = pygame.display.get_window_size()
    projection = perspective(FOV_Y_DEG, win_w / win_h, 0.1, 300.0)
    proj_bytes = to_gl_bytes(projection)
    fullscreen = False

    def apply_size(w, h):
        """
        Called whenever the drawable size changes (F11, or the user resizing the window).
        Refreshes the GL viewport, the projection matrix (aspect ratio), the sky's
        aspect uniform and the pixel-sized crosshair bars.
        """
        nonlocal win_w, win_h, projection, proj_bytes
        if w < 1 or h < 1:          # minimised window: nothing sensible to do
            return
        win_w, win_h = w, h
        ctx.viewport = (0, 0, w, h)
        projection = perspective(FOV_Y_DEG, w / h, 0.1, 300.0)
        proj_bytes = to_gl_bytes(projection)
        sky_prog["u_aspect"].value = w / h
        cross_vbo.write(build_crosshair_vertices(w, h).tobytes())

    apply_size(win_w, win_h)

    def toggle_fullscreen():
        """
        F11. pygame.display.toggle_fullscreen() (SDL2) flips the EXISTING window in
        place, so the OpenGL context and every ModernGL buffer/VAO stay valid.
        If a platform cannot do that, fall back to set_mode() with new flags.
        """
        nonlocal fullscreen
        fullscreen = not fullscreen
        ok = False
        try:
            ok = pygame.display.toggle_fullscreen()
        except pygame.error:
            ok = False
        if not ok:
            flags = pygame.OPENGL | pygame.DOUBLEBUF
            if fullscreen:
                pygame.display.set_mode((0, 0), flags | pygame.FULLSCREEN)
            else:
                pygame.display.set_mode((WIDTH, HEIGHT), flags | pygame.RESIZABLE)
        # A window-mode switch can silently drop the grab / relative mode, so re-assert
        # the full capture state (this also flushes get_rel()).
        capture_mouse(True)
        w, h = pygame.display.get_window_size()
        apply_size(w, h)

    def cast_fireball(t):
        """Spawn one plasma bolt at the staff's crystal, flying toward where the player aims."""
        nonlocal recoil
        right, up, fwd = camera.basis()

        # Crystal tip in the WORLD: staff model matrix -> view-space point, then
        #     world = cam_pos + right * vx + up * vy + forward * (-vz)
        tip = staff_model_matrix(t, recoil) @ np.array([*STAFF_CRYSTAL_TIP, 1.0], dtype=np.float32)
        spawn = camera.position + right * tip[0] + up * tip[1] + fwd * (-tip[2])

        # Aim at the point 40 units down the camera's forward ray so the bolt
        # converges on the crosshair even though the staff is off to the side.
        target = camera.position + fwd * 40.0
        aim = target - spawn
        aim /= np.linalg.norm(aim)
        vel = aim * BOLT_SPEED

        if len(fireballs) >= MAX_FIREBALLS:
            fireballs.pop(0)
        fireballs.append(Fireball(spawn, vel, BOLT_LIFESPAN, float(rng.random())))
        recoil = 1.0

    while running:
        dt = min(clock.tick(60) / 1000.0, 0.05)     # clamp: a long hitch must not explode the physics
        t = (pygame.time.get_ticks() - start_ms) / 1000.0

        # ---- Input events (also pumps the OS queue, which updates get_rel()'s counters) ----
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                toggle_fullscreen()
            elif event.type == getattr(pygame, "WINDOWFOCUSLOST", -1):
                capture_mouse(False)            # alt-tabbed away: give the cursor back
            elif event.type == getattr(pygame, "WINDOWFOCUSGAINED", -1):
                capture_mouse(True)             # came back: hide + lock + flush again
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:   # left click
                if mouse_captured:
                    cast_fireball(t)
                else:
                    capture_mouse(True)         # first click after losing focus just re-locks

        # Size poll: catches F11, manual window resizing and desktop-driven changes alike
        cur = pygame.display.get_window_size()
        if cur != (win_w, win_h):
            apply_size(*cur)

        # ------------------------------------------------------------------
        # MOUSE LOOK: pygame.mouse.get_rel()
        # ------------------------------------------------------------------
        # get_rel() returns (dx, dy): how many pixels the mouse moved since the PREVIOUS
        # call to get_rel(), then resets its internal counter. We never look at the
        # absolute cursor position, so the result is independent of where the cursor is
        # and a long, continuous sweep of the hand gives a long continuous turn.
        #   dx > 0 : mouse moved right  -> yaw increases   -> view turns right
        #   dy < 0 : mouse moved up     -> pitch increases -> view looks up
        # camera.rotate() multiplies by MOUSE_SENSITIVITY (degrees per pixel), adds to
        # yaw WITHOUT any limit (infinite 360-degree spins), clamps pitch to +-89 degrees,
        # then rebuilds the Forward/Right/Up vectors with sin/cos.
        dx, dy = pygame.mouse.get_rel()
        if mouse_captured:
            camera.rotate(dx, dy)
            recentre_if_near_edge()             # no-op in true relative mode (cursor never moves)
        camera.update(pygame.key.get_pressed(), dt)
        push_out_of_box(camera.position, house_min[0], house_max[0], 0.4)   # the house walls are solid
        player_pos = camera.position.astype(np.float64)                      # sphere centre for deflection

        # ---- Simulation: constructs (wander AI; artillery also fire) + respawns ----
        for c in creatures:
            shot = c.update(dt, t, rng, tree_xz, tree_r, player_pos)
            if shot is not None and len(enemy_shots) < MAX_ENEMY_SHOTS:
                enemy_shots.append(shot)

        for r in respawn_timers:
            r[0] -= dt
        ready = [r for r in respawn_timers if r[0] <= 0.0]
        respawn_timers[:] = [r for r in respawn_timers if r[0] > 0.0]
        for r in ready:
            creatures.append(spawn_entity(r[1], rng, tree_xz, tree_r, (camera.position[0], camera.position[2])))

        # ---- Simulation: integrate player projectiles (explicit Euler: p += v * dt) ----
        recoil *= math.exp(-9.0 * dt)
        for fb in fireballs:
            fb.prev[:] = fb.pos
            fb.pos += fb.vel * dt
            fb.age += dt

        # Construct AABBs for this frame's collision tests
        alive_list = [c for c in creatures if c.alive]
        if alive_list:
            boxes = [c.aabb() for c in alive_list]
            cb_min = np.array([b[0] for b in boxes])
            cb_max = np.array([b[1] for b in boxes])
        else:
            cb_min = cb_max = None

        # ---- Collision: swept ray-vs-AABB of every solid bolt vs trees, constructs AND the house ----
        survivors, spawned = [], []
        for fb in fireballs:
            if fb.age >= fb.life:
                continue
            if fb.solid:
                origin = fb.prev.astype(np.float64)
                segment = fb.pos.astype(np.float64) - origin    # this frame's movement (t in [0,1])
                seg_len = np.linalg.norm(segment)

                cands = []     # (t_near, kind, result): whichever object is entered FIRST takes the hit
                if seg_len > 1e-9:
                    r = raycast_boxes(origin, segment, box_min, box_max)
                    if r is not None: cands.append((r[1], "tree", r))
                    if cb_min is not None:
                        r = raycast_boxes(origin, segment, cb_min, cb_max)
                        if r is not None: cands.append((r[1], "creature", r))
                    r = raycast_boxes(origin, segment, house_min, house_max)
                    if r is not None: cands.append((r[1], "house", r))

                if cands:
                    _, kind, res = min(cands, key=lambda c: c[0])
                    _, t_near, t_far = res
                    # EXACT impact point: where the segment first pierces the box surface.
                    impact = origin + segment * max(t_near, 0.0)

                    if kind == "creature":
                        victim = alive_list[res[0]]
                        if victim.alive:
                            victim.alive = False                     # state: ALIVE -> DEAD
                            shatter_creature(victim, t, impact, segment / seg_len, rng, debris)
                            respawn_timers.append([RESPAWN_DELAY, victim.kind])
                    elif kind == "tree":
                        hit_points.append(impact.astype(np.float32))
                        if CARVE_EXIT_HOLE:
                            # Follow the same ray to where it LEAVES the box: a second hole
                            # in the far wall makes the blast truly see-through.
                            exit_pt = origin + segment * t_far
                            hit_points.append(exit_pt.astype(np.float32))
                        while len(hit_points) > MAX_HIT_POINTS:
                            hit_points.pop(0)
                    # kind == "house": the bolt just splashes harmlessly on the slate

                    spawned.append(Fireball(impact, (0, 0, 0), 0.35, float(rng.random()), solid=False))
                    continue                                         # bolt consumed

                if not (fb.pos[1] > 0.03 and abs(fb.pos[0]) < 250 and abs(fb.pos[2]) < 250):
                    continue
            survivors.append(fb)
        fireballs[:] = (survivors + spawned)[-MAX_FIREBALLS:]
        creatures[:] = [c for c in creatures if c.alive]

        # ---- Simulation: ENEMY projectiles (separate list) ----
        kept = []
        for s in enemy_shots:
            s.update(dt)                                        # straight flight, or arc after a bounce
            if s.age >= s.life:
                continue                                        # despawn

            # Player collision: distance to the camera sphere < PLAYER_RADIUS -> BOUNCE (no damage!)
            if not s.bounced and deflect_off_player(s, player_pos, PLAYER_RADIUS, rng):
                deflections += 1

            # World collision: monoliths and the house stop (and remove) the shot
            seg = s.pos - s.prev
            if np.linalg.norm(seg) > 1e-9 and raycast_boxes(s.prev, seg, solid_min, solid_max) is not None:
                continue
            if not s.bounced and s.pos[1] < 0.03:               # a straight shot that hit the floor
                continue
            if abs(s.pos[0]) > 250 or abs(s.pos[2]) > 250:
                continue
            kept.append(s)
        enemy_shots[:] = kept

        # ---- Simulation: tumbling debris ----
        for d in debris:
            d.update(dt, rng)

        # ---- Matrices ----
        view = camera.view_matrix()
        mvp = projection @ view
        mvp_bytes = to_gl_bytes(mvp)
        right, up, fwd = camera.basis()

        # ---- Render ----
        ctx.fbo.depth_mask = True
        ctx.enable(moderngl.DEPTH_TEST)
        ctx.disable(moderngl.BLEND)
        ctx.disable(moderngl.CULL_FACE)
        ctx.clear(0.0, 0.0, 0.0, 1.0)

        # (0) Sky + sun: drawn FIRST with the depth test disabled.
        ctx.disable(moderngl.DEPTH_TEST)
        sky_prog["u_cam_right"].value = tuple(right)
        sky_prog["u_cam_up"].value = tuple(up)
        sky_prog["u_cam_fwd"].value = tuple(fwd)
        sky_prog["u_time"].value = t
        sky_vao.render(moderngl.TRIANGLES)
        ctx.enable(moderngl.DEPTH_TEST)

        # (1) Ground
        ground_prog["u_mvp"].write(mvp_bytes)
        ground_prog["u_time"].value = t
        ground_prog["u_cam_pos"].value = tuple(camera.position)
        ground_vao.render(moderngl.TRIANGLES)

        # (2) Slate monoliths: ONE instanced draw call; face culling OFF so the hollow
        # interior is visible through the holes.
        hit_array = np.zeros((MAX_HIT_POINTS, 3), dtype=np.float32)
        if hit_points:
            hit_array[:len(hit_points)] = np.array(hit_points, dtype=np.float32)
        tree_prog["hit_points"].write(hit_array.tobytes())
        tree_prog["u_hit_count"].value = len(hit_points)
        tree_prog["u_hole_radius"].value = HOLE_RADIUS
        tree_prog["u_mvp"].write(mvp_bytes)
        tree_prog["u_time"].value = t
        tree_prog["u_cam_pos"].value = tuple(camera.position)
        tree_prog["u_sun_dir"].value = tuple(SUN_DIR)
        tree_vao.render(moderngl.TRIANGLES, instances=tree_count)

        # (3) The cozy house: ONE draw call for the whole composite mesh (culling stays off,
        # the shader flips normals when it sees a back face).
        house_prog["u_mvp"].write(mvp_bytes)
        house_prog["u_time"].value = t
        house_prog["u_cam_pos"].value = tuple(camera.position)
        house_vao.render(moderngl.TRIANGLES, vertices=house_vertex_count)

        # (4) Constructs + debris: one instanced call per primitive type.
        part_rows = pack_part_instances(creatures, debris, t)
        creature_prog["u_mvp"].write(mvp_bytes)
        creature_prog["u_time"].value = t
        creature_prog["u_cam_pos"].value = tuple(camera.position)
        creature_prog["u_sun_dir"].value = tuple(SUN_DIR)
        ctx.enable(moderngl.CULL_FACE)
        for mesh_id, (vao, inst_vbo, vcount) in creature_vaos.items():
            rows = part_rows[mesh_id][:MAX_PART_INSTANCES]
            if len(rows):
                inst_vbo.write(rows.tobytes())
                vao.render(moderngl.TRIANGLES, vertices=vcount, instances=len(rows))
        ctx.disable(moderngl.CULL_FACE)

        # (5) Meadow: a SINGLE draw call renders every blade.
        bolt_lights = np.zeros((MAX_BOLT_LIGHTS, 4), dtype=np.float32)
        for i, fb in enumerate(fireballs[-MAX_BOLT_LIGHTS:]):
            bolt_lights[i, :3] = fb.pos
            bolt_lights[i, 3] = max(fb.fade(), 0.001)
        grass_prog["u_bolts"].write(bolt_lights.tobytes())
        grass_prog["u_mvp"].write(mvp_bytes)
        grass_prog["u_time"].value = t
        grass_prog["u_cam_pos"].value = tuple(camera.position)
        grass_prog["u_cam_right"].value = tuple(camera.flat_right())
        grass_vao.render(moderngl.TRIANGLES, instances=BLADE_COUNT)

        # (6) Plasma orbs: player bolts (cyan/emerald) and enemy shots (amber/crimson).
        # Additive blending: result = src * 1 + dst * 1, so overlapping light just adds up.
        if fireballs or enemy_shots:
            ctx.enable(moderngl.BLEND)
            ctx.blend_func = moderngl.ONE, moderngl.ONE
            ctx.fbo.depth_mask = False                        # test depth, but don't write it

            for items, prog, vao, inst_vbo in ((fireballs, bolt_prog, bolt_vao, bolt_instance_vbo),
                                               (enemy_shots, enemy_bolt_prog, enemy_bolt_vao, enemy_instance_vbo)):
                if not items:
                    continue
                data = np.array([[*it.pos, it.seed, it.fade()] for it in items], dtype=np.float32)
                inst_vbo.write(data.tobytes())
                prog["u_mvp"].write(mvp_bytes)
                prog["u_time"].value = t
                prog["u_cam_right"].value = tuple(right)
                prog["u_cam_up"].value = tuple(up)
                vao.render(moderngl.TRIANGLES, instances=len(items))

            ctx.fbo.depth_mask = True
            ctx.disable(moderngl.BLEND)

        # (7) Staff view-model: separate pass, locked to the camera (projection only, no view matrix).
        ctx.disable(moderngl.DEPTH_TEST)
        ctx.enable(moderngl.CULL_FACE)
        staff_prog["u_proj"].write(proj_bytes)
        staff_prog["u_model"].write(to_gl_bytes(staff_model_matrix(t, recoil)))
        staff_prog["u_time"].value = t
        staff_vao.render(moderngl.TRIANGLES, vertices=staff_vertex_count)
        ctx.disable(moderngl.CULL_FACE)

        # (8) Crosshair overlay (additive)
        ctx.enable(moderngl.BLEND)
        ctx.blend_func = moderngl.ONE, moderngl.ONE
        cross_vao.render(moderngl.TRIANGLES, vertices=cross_vertex_count)
        ctx.disable(moderngl.BLEND)

        pygame.display.flip()
        n_art = sum(1 for c in creatures if c.kind == "artillery")
        pygame.display.set_caption(
            f"Voxel Meadow | {tree_count} monoliths | {len(creatures) - n_art} violet + {n_art} amber constructs | "
            f"{len(debris)} shards | {len(enemy_shots)} enemy shots | deflected {deflections} | "
            f"{win_w}x{win_h} | {clock.get_fps():.0f} FPS")

    capture_mouse(False)
    pygame.quit()


if __name__ == "__main__":
    main()