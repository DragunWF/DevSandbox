#!/usr/bin/env python3
"""
Voxel Meadow Instancing: Arcane Tech Edition
  + Arcane Staff & Plasma Bolts
  + Procedural Sky & Emerald Sun
  + Destructible Slate Monoliths (fragment-shader holes)
=============================================================================
Dependencies:  pip install pygame moderngl numpy

Controls:
    W/A/S/D      move (on the ground plane, relative to where you look)
    Mouse        look around (mouse is captured)
    Left click   cast an Arcane Plasma Bolt from the staff
    Space / Ctrl move up / down
    Shift        sprint
    Esc          quit

Render passes per frame:
    0. Sky + sun                        (full-screen triangle, depth test OFF, drawn first)
    1. Ground plane                     (opaque, depth tested)
    2. Slate monoliths (trees)          (ONE instanced draw call, fragment-shader `discard` holes)
    3. Grass meadow                     (ONE instanced draw call, 60k blades)
    4. Plasma bolts                     (ONE instanced draw call, additive blend, spherical billboards)
    5. Staff view-model                 (separate pass: static "view space" matrix, locked to the camera)
    6. Crosshair                        (additive 2D overlay)

Everything (geometry, colours, noise, sky, patterns) is generated procedurally.
"""

import math
import numpy as np
import pygame
import moderngl

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------
WIDTH, HEIGHT = 800, 600
FOV_Y_DEG = 70.0
BLADE_COUNT = 60_000          # number of instanced grass blades
MEADOW_HALF_SIZE = 32.0       # meadow spans [-32, 32] on X and Z
GROUND_HALF_SIZE = 120.0      # ground plane is bigger than the meadow (fog hides the edge)
MOVE_SPEED = 6.0
MOUSE_SENS = 0.0022           # radians per pixel

# --- Projectile settings ---
BOLT_SPEED = 30.0             # world units per second
BOLT_LIFESPAN = 4.5           # seconds before a bolt dissipates
MAX_FIREBALLS = 64            # capacity of the dynamic instance buffer
MAX_BOLT_LIGHTS = 16          # how many bolts can disturb/light the grass at once
STAFF_CRYSTAL_TIP = (0.0, 0.92, 0.0)   # staff-local point where bolts are born

# --- Tree / destruction settings ---
TREE_COUNT = 40               # number of instanced monoliths
MAX_HIT_POINTS = 48           # size of the `uniform vec3 hit_points[]` array (oldest overwritten)
HOLE_RADIUS = 0.50            # world-space radius of every blasted hole
CARVE_EXIT_HOLE = True        # also punch a hole where the bolt WOULD have left the pillar,
                              # so the blast is genuinely see-through (both walls)

# --- Sky ---
# A static sun direction (unit vector pointing FROM the camera TOWARD the sun).
# Slightly right of straight ahead and ~13 deg above the horizon, so it is
# visible from the spawn point.
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
uniform float u_aspect;         // width / height
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
    // Dark slate void at the zenith -> hazy glowing cyan at the horizon.
    // Below the horizon we clamp to the horizon colour (== fog colour).
    float h = max(dir.y, 0.0);
    vec3 zenith  = vec3(0.004, 0.008, 0.016);
    vec3 horizon = __FOG_COLOR__;
    float blend  = 1.0 - exp(-h * 4.2);              // fast rise near the horizon, long soft tail
    vec3 sky = mix(horizon, zenith, blend);

    // ---------------- Sun ----------------
    // dot(dir, sun_dir) == cos(angle between them); it approaches 1.0 when the
    // pixel looks straight at the sun. We convert to an actual angle (radians)
    // so disc size and halo falloff are easy to tune.
    float d   = dot(dir, u_sun_dir);
    float ang = acos(clamp(d, -1.0, 1.0));

    // A basis around the sun direction lets us measure the polar angle of the
    // pixel AROUND the sun (for rays and the swirling surface).
    vec3  sr = normalize(cross(u_sun_dir, vec3(0.0, 1.0, 0.0)));
    vec3  su = cross(sr, u_sun_dir);
    float around = atan(dot(dir, su), dot(dir, sr));

    // (a) The disc: hard-ish edge at ~1.8 degrees.
    float disc = 1.0 - smoothstep(0.030, 0.034, ang);

    // Energy sphere surface: swirling emerald <-> cyan, white-mint hot centre.
    float swirl = 0.5 + 0.5 * sin(around * 5.0 + ang * 170.0 - u_time * 2.0);
    vec3  disc_col = mix(vec3(0.05, 1.00, 0.50), vec3(0.00, 0.90, 1.00), swirl * 0.7);
    disc_col = mix(disc_col, vec3(0.85, 1.0, 0.95), (1.0 - smoothstep(0.0, 0.030, ang)) * 0.85);
    disc_col *= 1.6;                                  // overexposed: "blinding"

    // (b) Halo: a tight bright glow + a wide soft glow, both exponential falloffs.
    float halo_tight = exp(-ang * 16.0);
    float halo_wide  = exp(-ang * 4.0);

    // (c) Faint radial god-ray streaks that slowly rotate.
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
// The grass bends away from them and lights up as they fly past.
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
    // The blade's width axis is the camera's horizontal right vector, so
    // every flat blade always faces the viewer and never looks paper thin.
    vec3 world = root;
    world += u_cam_right * (in_vert.x * blade_width);
    world.y += in_vert.y * blade_height;

    // ---------------- WIND DISPLACEMENT ----------------
    // Only the upper part of the blade should move; the root stays pinned.
    // Squaring the height fraction gives a natural curve: stiff at the base,
    // floppy at the tip.
    float bend = in_vert.y * in_vert.y;

    // (1) Main travelling wave. The phase depends on the instance's WORLD
    //     position projected on a wind direction, so neighbouring blades get
    //     neighbouring phases and the ripple sweeps over the field as a coherent
    //     wavefront. "- u_time" makes the wavefront travel along +direction.
    vec2  wind_dir = normalize(vec2(1.0, 0.45));
    float phase1   = dot(root.xz, wind_dir) * 0.55 - u_time * 2.2;
    float wave1    = sin(phase1);

    // (2) A faster, shorter cross-wave at a different angle -> interference
    //     patterns so the field doesn't look like a uniform sine sheet.
    float phase2   = dot(root.xz, vec2(-0.4, 1.0)) * 1.3 - u_time * 3.6 + rnd * 6.2831;
    float wave2    = sin(phase2) * 0.35;

    // (3) A pulsing radial shockwave emanating from the origin: "arcane energy"
    //     rings that expand outward and sweep over the meadow.
    float radial   = length(root.xz);
    float ring     = sin(radial * 0.45 - u_time * 2.8);
    float pulse    = smoothstep(0.55, 1.0, ring);        // keep only the sharp crests

    float wave     = wave1 + wave2 + pulse * 1.2;

    // Horizontal sway, pushed along the wind direction (and a bit sideways)
    float amplitude = 0.55;
    vec2  sway = wind_dir * wave * amplitude * bend;
    sway += vec2(-wind_dir.y, wind_dir.x) * wave2 * 0.25 * bend;  // perpendicular flutter
    world.xz += sway;

    // When a blade bends sideways its tip must dip a little (it's a rigid-ish
    // length, not a stretchy one), otherwise blades look like they grow longer.
    world.y -= length(sway) * 0.35 * bend;

    // ---------------- PLASMA BOLT INTERACTION ----------------
    // For every live bolt: blades within ~4.5 units are shoved radially away
    // from it (stronger at the tip thanks to `bend`) and flare with energy.
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
    // Brightness driven by how strongly the wind is bending this blade
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

    // Two-stage gradient along the blade
    vec3 col = mix(root_cyan, mid_cyan, smoothstep(0.0, 0.55, v_height));
    col      = mix(col, tip_emerald, smoothstep(0.45, 1.0, v_height));

    // Per-blade hue nudge: some blades lean more cyan, others more emerald
    col = mix(col, col.gbr * vec3(0.6, 1.0, 1.0), (v_rand - 0.5) * 0.35);

    // Energy waves: crests of wind flash brighter near the tips
    float glow = v_energy * v_energy * (0.35 + 0.9 * v_height);
    col += vec3(0.05, 0.55, 0.35) * glow;
    col += vec3(0.6, 1.0, 0.9) * pow(v_energy, 6.0) * v_height * 0.6;  // white-hot crest highlight

    // Dark roots: fake ambient occlusion at the base
    col *= mix(0.35, 1.0, smoothstep(0.0, 0.35, v_height));

    // Distance fog now fades into the sky's horizon haze (not into black)
    col = mix(__FOG_COLOR__, col, v_fog);

    fragColor = vec4(col, 1.0);
}
"""

# ----------------------------------------------------------------------------
# GLSL: Ground shaders (dark polished slate with a faint arcane grid)
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
out vec4 fragColor;

void main() {
    // Base: dark blue-grey slate
    vec3 slate = vec3(0.018, 0.026, 0.034);

    // Faint polished-stone sheen: brighter reflection near the camera's look area
    vec3  to_cam = u_cam_pos - v_world;
    float dist   = length(to_cam);
    float sheen  = pow(clamp(normalize(to_cam).y, 0.0, 1.0), 3.0);
    slate += vec3(0.01, 0.025, 0.03) * sheen;

    // Antialiased grid lines (1 unit cells) using screen-space derivatives
    vec2 cell = v_world.xz;
    vec2 g    = abs(fract(cell - 0.5) - 0.5) / fwidth(cell);
    float line = 1.0 - clamp(min(g.x, g.y), 0.0, 1.0);

    // Same radial energy ring as the grass wind, so the ground pulses in sync
    float radial = length(v_world.xz);
    float ring   = smoothstep(0.55, 1.0, sin(radial * 0.45 - u_time * 2.8));

    vec3 col = slate;
    col += vec3(0.0, 0.22, 0.28) * line * (0.10 + 0.9 * ring);
    col += vec3(0.0, 0.10, 0.12) * ring * 0.35;   // soft glow under the pulse

    // Same fog as the grass: dissolve into the sky's horizon haze
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

out vec3  v_world;      // world-space position, used for the hole distance test
out vec3  v_normal;
out float v_hfrac;      // 0 at the base, 1 at the top
out float v_seed;

void main() {
    // Scale the unit pillar to this instance's size and move it into the world.
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
    // there, which means (a) the background / interior behind it shows
    // through and (b) later passes (grass, bolts) depth-test against whatever
    // is really visible. Because the test is done in 3D world space, the same
    // sphere carves every face it touches (front, back, edges, even a
    // neighbouring pillar) as one consistent hole.
    //
    // To avoid a perfectly smooth, CG-looking circle, the radius is
    // perturbed by a product of sines of the position relative to the impact,
    // so the rim becomes ragged, like melted stone.
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

    // =====================================================================
    // Shading (only pixels that survived the discard get here)
    // =====================================================================
    vec3 N = normalize(v_normal);
    bool front = gl_FrontFacing;
    // Face culling is OFF for trees. If we are looking at the INSIDE of the
    // shell (visible only through a hole) the geometric normal points away
    // from the eye, so flip it.
    if (!front) N = -N;

    vec3 V = normalize(u_cam_pos - v_world);
    vec3 cyan    = vec3(0.00, 0.85, 1.00);
    vec3 emerald = vec3(0.05, 1.00, 0.40);

    vec3 col;
    if (front) {
        // ---- Dark slate monolith, lit by the emerald-cyan sun ----
        float diff   = max(dot(N, u_sun_dir), 0.0);
        float strata = 0.5 + 0.5 * sin(v_world.y * 9.0 + v_seed * 20.0);
        col  = vec3(0.030, 0.042, 0.055) * (0.8 + 0.4 * strata);
        col += vec3(0.02, 0.16, 0.14) * diff * 0.55;

        // Vertical seams: pick the horizontal axis that runs ALONG this face.
        float u = (abs(N.x) > 0.5) ? v_world.z : v_world.x;
        col += cyan * smoothstep(0.94, 1.0, sin(u * 6.0 + v_seed * 10.0)) * 0.10;

        // Rune bands crawling up the pillar
        float band = smoothstep(0.95, 1.0, sin(v_world.y * 2.2 - u_time * 1.4 + v_seed * 6.2831));
        col += cyan * band * 0.45;

        // Glowing cap at the very top, plus a bright plate on the top face
        col += cyan * smoothstep(0.955, 0.985, v_hfrac) * (0.5 + 0.2 * sin(u_time * 2.0 + v_seed * 6.0));
        if (N.y > 0.9) col = mix(col, cyan * (0.55 + 0.25 * sin(u_time * 2.0 + v_seed * 6.0)), 0.85);

        // Fresnel rim
        col += cyan * pow(1.0 - max(dot(N, V), 0.0), 3.0) * 0.18;
    } else {
        // ---- Hollow interior (only seen through holes): dark, glowing emerald near the wound ----
        col  = vec3(0.004, 0.018, 0.020);
        col += emerald * exp(-gap * 2.5) * (0.55 + 0.15 * sin(u_time * 5.0));
    }

    // ---- Superheated arcane slag on the rim of every hole ----
    // Pixels that are JUST outside the hole radius (gap < rim_w) are painted
    // a blazing, saturated emerald, white-hot at the very edge, then they
    // cool off into the normal slate.
    float rim_w = 0.18;
    if (gap < rim_w) {
        float k = 1.0 - gap / rim_w;                        // 1 at the hole edge, 0 at the outer rim
        vec3 slag = mix(vec3(0.00, 1.00, 0.35), vec3(0.80, 1.00, 0.90), k * k);
        slag *= 1.8 + 0.5 * sin(u_time * 9.0 + v_world.y * 20.0);   // flickering
        col = mix(col, slag, pow(k, 0.6));
    }
    // Soft heat bloom radiating a little further out
    col += emerald * exp(-gap * 7.0) * 0.45;

    // Fog into the sky haze
    float dist = length(v_world - u_cam_pos);
    col = mix(__FOG_COLOR__, col, exp(-dist * dist * 0.00045));
    fragColor = vec4(col, 1.0);
}
"""

# ----------------------------------------------------------------------------
# GLSL: Plasma bolt shaders (instanced, spherically billboarded quads)
# ----------------------------------------------------------------------------
BOLT_VERTEX_SHADER = """
#version 330 core

// ---- Per-VERTEX: one shared unit quad, corners in [-1, 1] ----
in vec2  in_quad;

// ---- Per-INSTANCE: one record per live bolt (divisor = 1) ----
in vec3  in_center;   // world-space centre of the bolt
in float in_seed;     // random 0..1: de-synchronises the swirl of each bolt
in float in_fade;     // 0..1: grows in at birth, shrinks at the end of the lifespan

uniform mat4  u_mvp;        // projection * view
uniform float u_time;
uniform vec3  u_cam_right;  // camera's TRUE right vector (row 0 of the view rotation)
uniform vec3  u_cam_up;     // camera's TRUE up vector    (row 1 of the view rotation)

out vec2  v_uv;
out float v_seed;
out float v_fade;

void main() {
    // ---------------- SPHERICAL BILLBOARDING ----------------
    // We want the flat quad to face the camera from ANY angle, including
    // when looking up or down. Instead of building a model matrix, we
    // expand the quad along the camera's own right/up axes:
    //
    //     corner_world = centre + right * (qx * size) + up * (qy * size)
    //
    // Because right/up are the basis vectors of the camera's image plane,
    // the quad ends up exactly parallel to the screen => always faces the
    // viewer. (The grass uses CYLINDRICAL billboarding, which only uses the
    // horizontal right vector and keeps blades upright. Here both camera axes
    // are used, which is the "spherical" variant.)
    float size = 0.6 * (0.92 + 0.12 * sin(u_time * 14.0 + in_seed * 30.0)) * in_fade;
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
out vec4 fragColor;

// ---- Tiny procedural value-noise toolkit (no textures needed) ----
float hash(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);                      // smooth interpolation curve
    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

float fbm(vec2 p) {                                   // 4 octaves of noise
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
    if (r > 1.0) discard;                             // quad -> round orb

    // ---------------- SWIRL ----------------
    // Rotate the sampling coordinates by an angle that is LARGER near the
    // centre than at the rim. This differential rotation drags the noise
    // into a spiral vortex. u_time makes it spin; v_seed gives every bolt
    // its own phase.
    float twist = (1.0 - r) * 5.0 - u_time * 4.0 + v_seed * 6.2831;
    vec2  p = rot(twist) * uv * 2.2;

    // Domain-warped fBm: noise fed into noise gives liquid, plasma-like tendrils
    float n1 = fbm(p + vec2(u_time * 0.8, -u_time * 0.6));
    float n2 = fbm(p * 1.7 - n1 * 1.5 + vec2(-u_time * 1.1, u_time * 0.7));

    // Spiral energy arms that wind outward and spin with time
    float ang  = atan(uv.y, uv.x);
    float arms = 0.5 + 0.5 * sin(ang * 3.0 + r * 9.0 - u_time * 7.0 + v_seed * 6.2831);

    // ---------------- COLOUR: emerald <-> cyan, never orange ----------------
    vec3 cyan    = vec3(0.00, 0.85, 1.00);
    vec3 emerald = vec3(0.05, 1.00, 0.40);
    vec3 col = mix(cyan, emerald, smoothstep(0.30, 0.70, n2));
    col *= 0.35 + 1.7 * n2;                           // dark pockets, hot filaments

    float falloff = 1.0 - smoothstep(0.30, 1.0, r);   // soft round edge
    float core    = exp(-r * r * 7.0);                // hot centre

    col += cyan * arms * falloff * 0.45;              // spiral arms
    col += vec3(0.65, 1.00, 0.92) * core * 1.7;       // white-emerald heart
    col += vec3(0.0, 0.5, 0.6) * smoothstep(0.6, 0.95, r) * (1.0 - smoothstep(0.95, 1.0, r)) * 0.6; // thin halo rim

    // Premultiplied by falloff: used with ONE/ONE additive blending
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
        // Crystal: slowly spin around the staff axis and breathe with u_time.
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
    v_normal = mat3(u_model) * n;    // uniform scale + rotation only, so this is safe
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
    vec3 V = normalize(-v_view);                       // from surface toward the eye (view space)
    vec3 L = normalize(vec3(-0.4, 0.7, 0.6));          // fixed key light in view space
    float diff = max(dot(N, L), 0.0);
    float fres = pow(1.0 - max(dot(N, V), 0.0), 3.0);  // rim/fresnel term

    vec3 cyan    = vec3(0.00, 0.85, 1.00);
    vec3 emerald = vec3(0.05, 1.00, 0.45);
    float beat   = 0.5 + 0.5 * sin(u_time * 3.0);      // matches the vertex pulse

    vec3 col;
    if (v_part < 0.5) {
        // Dark polished slate shaft with glowing cyan rune bands crawling upward
        col  = vec3(0.025, 0.04, 0.055) + diff * vec3(0.035, 0.055, 0.07);
        col += cyan * fres * 0.30;
        float band = smoothstep(0.94, 1.0, sin(v_h * 38.0 - u_time * 2.5));
        col += cyan * band * 0.55;
    } else {
        // Tech-glass crystal: emissive gradient + fresnel + travelling shimmer
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
    The rows of the rotation part are the camera's basis vectors:
        right   = forward x up
        cam_up  = right   x forward
    The camera looks down its local -Z axis, so the third row is -forward.
    The translation part moves the world so the eye sits at the origin.
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
    """
    NumPy stores our matrices row-major; GLSL expects column-major data.
    Transposing before serialising gives OpenGL exactly what it expects.
    """
    return mat.T.astype("f4").tobytes()


# ----------------------------------------------------------------------------
# First-person camera
# ----------------------------------------------------------------------------
class FPSCamera:
    def __init__(self, position):
        self.position = np.array(position, dtype=np.float32)
        self.yaw = 0.0     # rotation about the world Y axis (0 => looking toward -Z)
        self.pitch = -0.15  # rotation up/down (radians)

    def rotate(self, dx, dy):
        """Mouse deltas -> yaw/pitch. Pitch is clamped to avoid flipping over the poles."""
        self.yaw += dx * MOUSE_SENS
        self.pitch -= dy * MOUSE_SENS
        limit = math.radians(89.0)
        self.pitch = max(-limit, min(limit, self.pitch))

    def forward(self):
        """
        Spherical -> Cartesian conversion for the look direction.
        With yaw = 0 and pitch = 0 this gives (0, 0, -1), i.e. OpenGL's default view direction.
            x =  cos(pitch) * sin(yaw)
            y =  sin(pitch)
            z = -cos(pitch) * cos(yaw)
        """
        cp = math.cos(self.pitch)
        return np.array([cp * math.sin(self.yaw),
                         math.sin(self.pitch),
                         -cp * math.cos(self.yaw)], dtype=np.float32)

    def flat_forward(self):
        """Forward direction projected on the ground (so W/S never fly you up or down)."""
        return np.array([math.sin(self.yaw), 0.0, -math.cos(self.yaw)], dtype=np.float32)

    def flat_right(self):
        """
        Right vector on the ground: forward x up, with the pitch term removed:
            right = (cos(yaw), 0, sin(yaw))
        Also handed to the grass shader for billboarding.
        """
        return np.array([math.cos(self.yaw), 0.0, math.sin(self.yaw)], dtype=np.float32)

    def basis(self):
        """
        Full camera basis in world space: (right, up, forward).
        `right` never tilts (we have no roll), and up = right x forward is
        automatically perpendicular to both, so it tilts with the pitch.
        These are exactly the rows of the view matrix's rotation part. The bolt
        billboards and the sky's per-pixel view direction are both built from them.
        """
        fwd = self.forward()
        right = self.flat_right()
        up = np.cross(right, fwd).astype(np.float32)
        return right, up, fwd

    def update(self, keys, dt):
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


# ----------------------------------------------------------------------------
# Projectiles
# ----------------------------------------------------------------------------
class Fireball:
    """
    One Arcane Plasma Bolt: position, velocity, age and lifespan.

    `prev` is where the bolt was at the START of the frame; together with `pos`
    it forms the line SEGMENT swept this frame, which we ray-cast against the
    trees (so a fast bolt can never "tunnel" through a thin pillar between frames).

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


def staff_model_matrix(t, recoil):
    """
    Staff-local -> VIEW space (camera-relative) transform.

    Because this is applied directly in view space and combined with the
    projection only (no camera view matrix), the staff is "locked" to the
    screen: it never moves relative to the camera, whatever you do.

    The view space convention is: camera at the origin looking down -Z,
    +X right, +Y up. So (0.62, -0.95, -1.2) is right of centre, below centre,
    and 1.2 units in front of the lens. The shaft is tilted so the crystal
    tip leans inward and forward, and the handle runs off the bottom edge.
    """
    bob = 0.012 * math.sin(t * 1.7)                            # idle floating motion
    return (translate(0.62, -0.95 + bob, -1.2 + 0.18 * recoil)  # recoil pushes it back toward the eye
            @ rotate_z(math.radians(12.0))
            @ rotate_x(math.radians(-30.0 + 12.0 * recoil))     # recoil also kicks the tip up
            @ scale(0.9))


# ----------------------------------------------------------------------------
# Ray vs. axis-aligned bounding box collision (the "slab method")
# ----------------------------------------------------------------------------
def raycast_boxes(origin, direction, box_min, box_max):
    """
    Cast the ray   P(t) = origin + direction * t   against EVERY tree's AABB at once.

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

    Axes where direction ~ 0 would divide by zero, so they get a tiny epsilon:
    t1/t2 then become huge values of equal sign when the origin is outside that
    slab (-> miss) or of opposite sign when inside (-> slab never limits the ray).

    Returns (tree_index, t_near, t_far) for the NEAREST box hit, else None.
    """
    d = np.where(np.abs(direction) < 1e-9, 1e-9, direction)
    inv = 1.0 / d
    t1 = (box_min - origin) * inv                 # (N,3) entry/exit candidates per axis
    t2 = (box_max - origin) * inv
    t_near = np.minimum(t1, t2).max(axis=1)       # latest entry among the 3 slabs
    t_far = np.maximum(t1, t2).min(axis=1)        # earliest exit among the 3 slabs

    hit = (t_near <= t_far) & (t_far >= 0.0) & (t_near <= 1.0)
    if not hit.any():
        return None
    idx = np.where(hit)[0]
    best = idx[np.argmin(t_near[idx])]            # several boxes may be hit: take the closest
    return int(best), float(t_near[best]), float(t_far[best])


# ----------------------------------------------------------------------------
# Procedural geometry
# ----------------------------------------------------------------------------
def build_blade_mesh(segments=4):
    """
    One blade of grass: a tapered strip with `segments` quads whose width
    narrows to a single point at the tip. Extra rows of vertices give the wind
    something to bend, so the blade curves smoothly instead of shearing.

    Vertex layout (x, y, z):  x = side offset [-0.5, 0.5], y = height fraction [0, 1]
    Returns (vertices float32 [N,3], indices uint32 [M]).
    """
    verts = []
    for i in range(segments):
        y = i / segments
        half = 0.5 * (1.0 - y) ** 0.8         # taper toward the tip
        verts.append((-half, y, 0.0))         # left vertex of this row
        verts.append(( half, y, 0.0))         # right vertex of this row
    verts.append((0.0, 1.0, 0.0))             # single tip vertex

    idx = []
    for i in range(segments - 1):             # full quads between consecutive rows
        bl, br = 2 * i, 2 * i + 1
        tl, tr = 2 * i + 2, 2 * i + 3
        idx += [bl, br, tl,  br, tr, tl]
    last_l, last_r = 2 * (segments - 1), 2 * (segments - 1) + 1
    idx += [last_l, last_r, 2 * segments]     # final triangle up to the tip
    return np.array(verts, dtype=np.float32), np.array(idx, dtype=np.uint32)


def build_instance_data(count, half_size, seed=1337):
    """
    Per-instance data: [x, y, z, random] for every blade, uniformly scattered
    over the flat meadow. Packed as one flat float32 array (4 floats / blade).
    """
    rng = np.random.default_rng(seed)
    x = rng.uniform(-half_size, half_size, count)
    z = rng.uniform(-half_size, half_size, count)
    y = np.zeros(count)                       # flat ground: grass roots sit at y = 0
    r = rng.uniform(0.0, 1.0, count)
    return np.stack([x, y, z, r], axis=1).astype(np.float32)


def build_pillar_mesh():
    """
    Unit slate pillar: a stretched cube with x,z in [-1, 1] and y in [0, 1].
    The vertex shader scales it per instance to (half_x, height, half_z).

    Using a BOX (not a hexagonal prism) means the collision AABB is EXACTLY the
    visible shape, so the ray/box impact point always lies on the real surface.

    Each face is two triangles; the winding is verified against the face normal
    and flipped if needed, so every face is CCW seen from OUTSIDE (this is what
    lets the fragment shader use gl_FrontFacing to detect the hollow interior).

    Vertex layout (6 floats): position(3), normal(3).
    """
    faces = [  # (normal, 4 corners in cyclic order)
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
            if np.dot(np.cross(p1 - p0, p2 - p0), n) < 0:    # wrong winding -> swap
                p1, p2 = p2, p1
            for p in (p0, p1, p2):
                out.append([*p, *n])
    return np.array(out, dtype=np.float32)


def build_tree_data(count, half_size, avoid_xz, seed=77):
    """
    Scatter `count` monoliths by rejection sampling (not too close to the
    player's spawn point, not too close to each other).
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
        if any(math.hypot(x - p[0], z - p[2]) < 5.0 for p in placed):
            continue
        hx, hz = rng.uniform(0.45, 0.85, 2)
        h = rng.uniform(6.0, 13.0)
        placed.append((x, 0.0, z, rng.random(), hx, h, hz))
    return np.array(placed, dtype=np.float32)


def build_staff_mesh():
    """
    Low-poly arcane staff: a tapered 6-sided slate shaft topped by a hexagonal
    glass crystal (short prism capped with two pyramids).

    Every triangle is FLAT shaded (its own face normal) and wound CCW as seen
    from outside, so back-face culling can stand in for a depth buffer: both
    parts are convex. Winding is enforced by checking each face normal against
    the direction from the part's centre and swapping vertices if needed.

    Vertex layout (7 floats): position(3), normal(3), part(1)  [part: 0 shaft, 1 crystal]
    """
    out = []

    def add_convex(tris, center, part):
        center = np.array(center, dtype=np.float32)
        for a, b, c in tris:
            a, b, c = (np.array(v, dtype=np.float32) for v in (a, b, c))
            n = np.cross(b - a, c - a)
            if np.dot(n, (a + b + c) / 3.0 - center) < 0:   # facing inward -> flip winding
                b, c = c, b
                n = -n
            n = n / (np.linalg.norm(n) + 1e-9)
            for v in (a, b, c):
                out.append([*v, *n, part])

    def ring(radius, y, n, phase=0.0):
        return [(radius * math.cos(phase + 2 * math.pi * i / n), y,
                 radius * math.sin(phase + 2 * math.pi * i / n)) for i in range(n)]

    N = 6

    # ---- Shaft: tapered hexagonal prism, y from -0.9 to 0.58 ----
    bot, top = ring(0.035, -0.90, N), ring(0.024, 0.58, N)
    cb, ct = (0.0, -0.90, 0.0), (0.0, 0.58, 0.0)
    tris = []
    for i in range(N):
        j = (i + 1) % N
        tris += [(bot[i], bot[j], top[j]), (bot[i], top[j], top[i]),   # side quad
                 (cb, bot[j], bot[i]), (ct, top[i], top[j])]           # end caps
    add_convex(tris, (0.0, -0.16, 0.0), 0.0)

    # ---- Crystal: lower pyramid + short prism + upper pyramid ----
    ra = ring(0.10, 0.80, N, phase=math.pi / N)    # lower equator ring
    rb = ring(0.10, 0.92, N, phase=math.pi / N)    # upper equator ring
    apex_lo, apex_hi = (0.0, 0.62, 0.0), (0.0, 1.22, 0.0)
    tris = []
    for i in range(N):
        j = (i + 1) % N
        tris += [(apex_lo, ra[j], ra[i]),           # bottom point
                 (ra[i], ra[j], rb[j]), (ra[i], rb[j], rb[i]),   # band
                 (apex_hi, rb[i], rb[j])]           # top point
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

    pygame.display.set_mode((WIDTH, HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF)
    pygame.display.set_caption("Voxel Meadow Instancing")

    # Capture the mouse for first-person look
    pygame.event.set_grab(True)
    pygame.mouse.set_visible(False)
    pygame.mouse.get_rel()   # discard the initial jump

    # ------------------------------------------------------------------
    # ModernGL context + programs
    # ------------------------------------------------------------------
    ctx = moderngl.create_context()
    ctx.enable(moderngl.DEPTH_TEST)   # nearer fragments hide farther ones

    sky_prog = ctx.program(vertex_shader=prep(SKY_VERTEX_SHADER),
                           fragment_shader=prep(SKY_FRAGMENT_SHADER))
    grass_prog = ctx.program(vertex_shader=prep(GRASS_VERTEX_SHADER),
                             fragment_shader=prep(GRASS_FRAGMENT_SHADER))
    ground_prog = ctx.program(vertex_shader=prep(GROUND_VERTEX_SHADER),
                              fragment_shader=prep(GROUND_FRAGMENT_SHADER))
    tree_prog = ctx.program(vertex_shader=prep(TREE_VERTEX_SHADER),
                            fragment_shader=prep(TREE_FRAGMENT_SHADER))
    bolt_prog = ctx.program(vertex_shader=prep(BOLT_VERTEX_SHADER),
                            fragment_shader=prep(BOLT_FRAGMENT_SHADER))
    staff_prog = ctx.program(vertex_shader=prep(STAFF_VERTEX_SHADER),
                             fragment_shader=prep(STAFF_FRAGMENT_SHADER))
    cross_prog = ctx.program(vertex_shader=prep(CROSS_VERTEX_SHADER),
                             fragment_shader=prep(CROSS_FRAGMENT_SHADER))

    # ------------------------------------------------------------------
    # Sky: one oversized triangle that covers the whole screen
    # ------------------------------------------------------------------
    sky_tri = np.array([-1, -1,  3, -1,  -1, 3], dtype=np.float32)
    sky_vbo = ctx.buffer(sky_tri.tobytes())
    sky_vao = ctx.vertex_array(sky_prog, [(sky_vbo, "2f", "in_pos")])
    sky_prog["u_sun_dir"].value = tuple(SUN_DIR)
    sky_prog["u_aspect"].value = WIDTH / HEIGHT
    sky_prog["u_tan_half_fov"].value = math.tan(math.radians(FOV_Y_DEG) / 2.0)

    # ------------------------------------------------------------------
    # HARDWARE INSTANCING SETUP: grass meadow
    # ------------------------------------------------------------------
    # 1) Base geometry buffers: ONE blade, shared by every instance.
    blade_verts, blade_indices = build_blade_mesh(segments=4)
    blade_vbo = ctx.buffer(blade_verts.tobytes())
    blade_ibo = ctx.buffer(blade_indices.tobytes())

    # 2) Instance buffer: one (x, y, z, random) record per blade, 10,000+ in total.
    instance_data = build_instance_data(BLADE_COUNT, MEADOW_HALF_SIZE)
    instance_vbo = ctx.buffer(instance_data.tobytes())

    # 3) Bind both buffers into one VAO.
    #    - '3f'    : advances once PER VERTEX   (the blade's shape)
    #    - '4f/i'  : the "/i" suffix sets the attribute divisor to 1, so the GPU
    #                advances this attribute once PER INSTANCE instead of per vertex.
    grass_vao = ctx.vertex_array(
        grass_prog,
        [
            (blade_vbo,    "3f",   "in_vert"),
            (instance_vbo, "4f/i", "in_offset"),
        ],
        index_buffer=blade_ibo,
    )

    # Ground plane: one big quad slightly below the grass roots to avoid z-fighting
    g, gy = GROUND_HALF_SIZE, -0.01
    ground_verts = np.array([
        -g, gy, -g,   g, gy, -g,   g, gy,  g,
        -g, gy, -g,   g, gy,  g,  -g, gy,  g,
    ], dtype=np.float32)
    ground_vbo = ctx.buffer(ground_verts.tobytes())
    ground_vao = ctx.vertex_array(ground_prog, [(ground_vbo, "3f", "in_position")])

    # ------------------------------------------------------------------
    # HARDWARE INSTANCING SETUP: slate monoliths ("trees")
    # ------------------------------------------------------------------
    # Shared geometry: ONE unit pillar (36 vertices: position + normal).
    pillar_data = build_pillar_mesh()
    pillar_vbo = ctx.buffer(pillar_data.tobytes())

    # Per-instance data (7 floats = 28 bytes per tree):
    #   in_base = (x, y, z, seed)      in_size = (half_x, height, half_z)
    tree_data = build_tree_data(TREE_COUNT, MEADOW_HALF_SIZE, avoid_xz=(0.0, 12.0))
    tree_count = len(tree_data)
    tree_instance_vbo = ctx.buffer(tree_data.tobytes())
    tree_vao = ctx.vertex_array(
        tree_prog,
        [
            (pillar_vbo,        "3f 3f",  "in_vert", "in_normal"),
            (tree_instance_vbo, "4f 3f/i", "in_base", "in_size"),   # '/i' -> once per instance
        ],
    )

    # Collision boxes (AABBs), float64 for robust slab math.
    # Pillar i occupies  [x - hx, x + hx] x [0, h] x [z - hz, z + hz].
    t64 = tree_data.astype(np.float64)
    box_min = np.stack([t64[:, 0] - t64[:, 4], np.zeros(tree_count), t64[:, 2] - t64[:, 6]], axis=1)
    box_max = np.stack([t64[:, 0] + t64[:, 4], t64[:, 5],            t64[:, 2] + t64[:, 6]], axis=1)

    # ------------------------------------------------------------------
    # HARDWARE INSTANCING SETUP: plasma bolts (DYNAMIC instance buffer)
    # ------------------------------------------------------------------
    # Shared geometry: one unit quad (two triangles) with corners in [-1, 1].
    quad = np.array([-1, -1,  1, -1,  1, 1,
                     -1, -1,  1,  1, -1, 1], dtype=np.float32)
    quad_vbo = ctx.buffer(quad.tobytes())

    # Per-instance data (x, y, z, seed, fade) = 5 floats = 20 bytes per bolt.
    # Unlike the grass, bolts change every frame, so we reserve a fixed-size
    # buffer once and overwrite it each frame with .write() (no reallocation).
    bolt_instance_vbo = ctx.buffer(reserve=MAX_FIREBALLS * 5 * 4, dynamic=True)
    bolt_vao = ctx.vertex_array(
        bolt_prog,
        [
            (quad_vbo,          "2f",         "in_quad"),
            # '/i' at the end of the format applies to the WHOLE buffer: all three
            # attributes advance once per instance.
            (bolt_instance_vbo, "3f 1f 1f/i", "in_center", "in_seed", "in_fade"),
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

    cross_data = build_crosshair_vertices(WIDTH, HEIGHT)
    cross_vbo = ctx.buffer(cross_data.tobytes())
    cross_vao = ctx.vertex_array(cross_prog, [(cross_vbo, "2f", "in_pos")])
    cross_vertex_count = len(cross_data) // 2

    # ------------------------------------------------------------------
    # Scene state
    # ------------------------------------------------------------------
    camera = FPSCamera(position=(0.0, 1.6, 12.0))
    projection = perspective(FOV_Y_DEG, WIDTH / HEIGHT, 0.1, 300.0)
    proj_bytes = to_gl_bytes(projection)
    clock = pygame.time.Clock()
    start_ms = pygame.time.get_ticks()
    rng = np.random.default_rng(2024)

    fireballs = []     # live Fireball objects
    hit_points = []    # world-space impact coordinates handed to the tree shader (capped)
    recoil = 0.0       # staff kick animation, 1 right after casting, decays to 0
    running = True

    def cast_fireball(t):
        """Spawn one plasma bolt at the staff's crystal, flying toward where the player aims."""
        nonlocal recoil
        right, up, fwd = camera.basis()

        # --- Where is the crystal tip in the WORLD? ---
        # The staff lives in VIEW space (camera at origin, looking down -Z).
        # Transform the crystal tip by the staff model matrix -> view-space point,
        # then convert view -> world using the camera basis:
        #     world = cam_pos + right * vx + up * vy + forward * (-vz)
        # (-vz because view space looks along -Z while 'forward' is +look direction.)
        tip = staff_model_matrix(t, recoil) @ np.array([*STAFF_CRYSTAL_TIP, 1.0], dtype=np.float32)
        spawn = camera.position + right * tip[0] + up * tip[1] + fwd * (-tip[2])

        # --- Velocity from the camera's forward vector ---
        # forward = (cos(pitch)*sin(yaw), sin(pitch), -cos(pitch)*cos(yaw)) is a unit
        # vector, so  velocity = forward * speed  moves exactly BOLT_SPEED units/sec
        # along the line of sight. The staff is off to the side, so a bolt flying
        # strictly parallel to `forward` would miss the crosshair. We therefore aim
        # at the point 40 units down the camera's forward ray and normalise the
        # (target - spawn) vector: it still follows the camera's look direction,
        # but converges on the crosshair.
        target = camera.position + fwd * 40.0
        aim = target - spawn
        aim /= np.linalg.norm(aim)
        vel = aim * BOLT_SPEED

        if len(fireballs) >= MAX_FIREBALLS:
            fireballs.pop(0)                      # drop the oldest if the buffer is full
        fireballs.append(Fireball(spawn, vel, BOLT_LIFESPAN, float(rng.random())))
        recoil = 1.0

    while running:
        dt = clock.tick(60) / 1000.0
        t = (pygame.time.get_ticks() - start_ms) / 1000.0

        # ---- Input ----
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:   # left click
                cast_fireball(t)

        dx, dy = pygame.mouse.get_rel()     # mouse movement since last frame
        camera.rotate(dx, dy)
        camera.update(pygame.key.get_pressed(), dt)

        # ---- Simulation: integrate projectiles (explicit Euler: p += v * dt) ----
        recoil *= math.exp(-9.0 * dt)       # exponential decay of the staff kick
        for fb in fireballs:
            fb.prev[:] = fb.pos             # remember where we were: start of the swept segment
            fb.pos += fb.vel * dt
            fb.age += dt

        # ---- Collision: swept ray-vs-AABB test of every solid bolt against every tree ----
        survivors, spawned = [], []
        for fb in fireballs:
            if fb.age >= fb.life:
                continue                                        # expired
            if fb.solid:
                origin = fb.prev.astype(np.float64)
                segment = fb.pos.astype(np.float64) - origin    # this frame's movement (t in [0,1])
                if np.linalg.norm(segment) > 1e-9:
                    res = raycast_boxes(origin, segment, box_min, box_max)
                else:
                    res = None
                if res is not None:
                    _, t_near, t_far = res
                    # EXACT impact point: where the segment first pierces the box surface.
                    # (t_near < 0 means the bolt started inside the box -> hit at its start.)
                    impact = origin + segment * max(t_near, 0.0)
                    hit_points.append(impact.astype(np.float32))

                    if CARVE_EXIT_HOLE:
                        # The same ray, followed on to where it LEAVES the box, gives the
                        # exit point on the far wall. Carving a second hole there makes
                        # the blast truly see-through instead of just a dent in the near wall.
                        exit_pt = origin + segment * t_far
                        hit_points.append(exit_pt.astype(np.float32))

                    while len(hit_points) > MAX_HIT_POINTS:     # cap: stay inside the uniform array
                        hit_points.pop(0)                       # oldest scars heal first

                    # Impact flash: a short-lived, motionless, non-colliding plasma burst
                    spawned.append(Fireball(impact, (0, 0, 0), 0.35, float(rng.random()), solid=False))
                    continue                                    # bolt consumed: delete the fireball

                # Not hit: still remove bolts that hit the ground or flew out of the world
                if not (fb.pos[1] > 0.03 and abs(fb.pos[0]) < 250 and abs(fb.pos[2]) < 250):
                    continue
            survivors.append(fb)
        fireballs[:] = (survivors + spawned)[-MAX_FIREBALLS:]

        # ---- Matrices ----
        # clip = Projection * View * (model = identity, since instance offsets are world space)
        view = camera.view_matrix()
        mvp = projection @ view
        mvp_bytes = to_gl_bytes(mvp)
        right, up, fwd = camera.basis()     # for billboarding the bolts and for the sky rays

        # ---- Render ----
        ctx.fbo.depth_mask = True
        ctx.enable(moderngl.DEPTH_TEST)
        ctx.disable(moderngl.BLEND)
        ctx.disable(moderngl.CULL_FACE)
        ctx.clear(0.0, 0.0, 0.0, 1.0)

        # (0) Sky + sun: drawn FIRST with the depth test disabled, so it paints the whole
        # background, writes no depth, and every later pass simply draws on top of it.
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

        # (2) Slate monoliths: ONE instanced draw call. Face culling stays OFF so the
        # hollow interior is visible through the holes (the shader flips the normal).
        hit_array = np.zeros((MAX_HIT_POINTS, 3), dtype=np.float32)
        if hit_points:
            hit_array[:len(hit_points)] = np.array(hit_points, dtype=np.float32)
        tree_prog["hit_points"].write(hit_array.tobytes())      # the whole vec3[] array at once
        tree_prog["u_hit_count"].value = len(hit_points)
        tree_prog["u_hole_radius"].value = HOLE_RADIUS
        tree_prog["u_mvp"].write(mvp_bytes)
        tree_prog["u_time"].value = t
        tree_prog["u_cam_pos"].value = tuple(camera.position)
        tree_prog["u_sun_dir"].value = tuple(SUN_DIR)
        tree_vao.render(moderngl.TRIANGLES, instances=tree_count)

        # (3) Meadow: a SINGLE draw call renders every blade.
        # Hand the newest bolts to the grass shader so blades react to them.
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

        # (4) Plasma bolts: ONE instanced draw call, additive blending.
        if fireballs:
            data = np.array([[*fb.pos, fb.seed, fb.fade()] for fb in fireballs], dtype=np.float32)
            bolt_instance_vbo.write(data.tobytes())

            ctx.enable(moderngl.BLEND)
            # Additive blending: result = src * 1 + dst * 1. Overlapping bolts and
            # bolts over bright grass simply ADD light, so they glow intensely.
            ctx.blend_func = moderngl.ONE, moderngl.ONE
            # Still depth-TEST (the ground/grass/trees hide bolts behind them), but don't
            # depth-WRITE, otherwise one bolt's soft edge would wrongly mask another.
            ctx.fbo.depth_mask = False

            bolt_prog["u_mvp"].write(mvp_bytes)
            bolt_prog["u_time"].value = t
            bolt_prog["u_cam_right"].value = tuple(right)
            bolt_prog["u_cam_up"].value = tuple(up)
            bolt_vao.render(moderngl.TRIANGLES, instances=len(fireballs))

            ctx.fbo.depth_mask = True
            ctx.disable(moderngl.BLEND)

        # (5) Staff view-model: separate pass, locked to the camera.
        # No depth test: the staff must ALWAYS draw over the world (it is "held" in
        # front of the lens). Its parts are convex, so back-face culling alone
        # resolves self-overlap correctly.
        ctx.disable(moderngl.DEPTH_TEST)
        ctx.enable(moderngl.CULL_FACE)
        staff_prog["u_proj"].write(proj_bytes)                                 # projection only, NO view matrix
        staff_prog["u_model"].write(to_gl_bytes(staff_model_matrix(t, recoil)))
        staff_prog["u_time"].value = t
        staff_vao.render(moderngl.TRIANGLES, vertices=staff_vertex_count)
        ctx.disable(moderngl.CULL_FACE)

        # (6) Crosshair overlay (additive)
        ctx.enable(moderngl.BLEND)
        ctx.blend_func = moderngl.ONE, moderngl.ONE
        cross_vao.render(moderngl.TRIANGLES, vertices=cross_vertex_count)
        ctx.disable(moderngl.BLEND)

        pygame.display.flip()
        pygame.display.set_caption(
            f"Voxel Meadow Instancing | {BLADE_COUNT:,} blades | {tree_count} monoliths | "
            f"{len(fireballs)} bolts | {len(hit_points)}/{MAX_HIT_POINTS} hit points | "
            f"{clock.get_fps():.0f} FPS")

    pygame.quit()


if __name__ == "__main__":
    main()