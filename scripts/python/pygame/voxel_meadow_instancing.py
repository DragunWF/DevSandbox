#!/usr/bin/env python3
"""
Voxel Meadow Instancing: Arcane Tech Edition
============================================
Dependencies:  pip install pygame moderngl numpy

Controls:
    W/A/S/D      move (on the ground plane, relative to where you look)
    Mouse        look around (mouse is captured)
    Space / Ctrl move up / down
    Shift        sprint
    Esc          quit

Everything (geometry, colours, grid) is generated procedurally.
Tens of thousands of grass blades are drawn in ONE instanced draw call.
"""

import math
import numpy as np
import pygame
import moderngl

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------
WIDTH, HEIGHT = 800, 600
BLADE_COUNT = 60_000          # number of instanced grass blades
MEADOW_HALF_SIZE = 32.0       # meadow spans [-32, 32] on X and Z
GROUND_HALF_SIZE = 120.0      # ground plane is bigger than the meadow (fog hides the edge)
MOVE_SPEED = 6.0
MOUSE_SENS = 0.0022           # radians per pixel

# ----------------------------------------------------------------------------
# GLSL: Grass shaders
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

    // ---------------- Outputs ----------------
    gl_Position = u_mvp * vec4(world, 1.0);

    v_height = in_vert.y;
    v_rand   = rnd;
    // Brightness driven by how strongly the wind is bending this blade
    v_energy = clamp(0.5 + 0.35 * wave1 + 0.25 * wave2 + pulse * 0.9, 0.0, 1.0);

    float dist = length(world - u_cam_pos);
    v_fog = exp(-dist * dist * 0.00045);   // exponential-squared fog into the black void
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

    // Fade into the pitch-black void
    col *= v_fog;

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

    col *= exp(-dist * dist * 0.00045);           // same fog as the grass
    fragColor = vec4(col, 1.0);
}
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
    # ModernGL context + state
    # ------------------------------------------------------------------
    ctx = moderngl.create_context()
    ctx.enable(moderngl.DEPTH_TEST)   # nearer fragments hide farther ones

    grass_prog = ctx.program(vertex_shader=GRASS_VERTEX_SHADER,
                             fragment_shader=GRASS_FRAGMENT_SHADER)
    ground_prog = ctx.program(vertex_shader=GROUND_VERTEX_SHADER,
                              fragment_shader=GROUND_FRAGMENT_SHADER)

    # ------------------------------------------------------------------
    # HARDWARE INSTANCING SETUP
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
    #    All blades share the same 9 or so vertices, while each instance reads its own
    #    offset from instance_vbo.
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
    # Scene state
    # ------------------------------------------------------------------
    camera = FPSCamera(position=(0.0, 1.6, 12.0))
    projection = perspective(70.0, WIDTH / HEIGHT, 0.1, 300.0)
    clock = pygame.time.Clock()
    start_ms = pygame.time.get_ticks()
    running = True

    while running:
        dt = clock.tick(60) / 1000.0
        t = (pygame.time.get_ticks() - start_ms) / 1000.0

        # ---- Input ----
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        dx, dy = pygame.mouse.get_rel()     # mouse movement since last frame
        camera.rotate(dx, dy)
        camera.update(pygame.key.get_pressed(), dt)

        # ---- Matrices ----
        # clip = Projection * View * (model = identity, since instance offsets are world space)
        mvp = projection @ camera.view_matrix()
        mvp_bytes = to_gl_bytes(mvp)

        # ---- Render ----
        ctx.clear(0.0, 0.0, 0.0, 1.0)       # pitch-black void sky

        # Ground
        ground_prog["u_mvp"].write(mvp_bytes)
        ground_prog["u_time"].value = t
        ground_prog["u_cam_pos"].value = tuple(camera.position)
        ground_vao.render(moderngl.TRIANGLES)

        # Meadow: a SINGLE draw call renders every blade.
        # `instances=` tells the GPU to run the blade mesh BLADE_COUNT times;
        # for instance k the vertex shader receives instance_data[k] as in_offset.
        grass_prog["u_mvp"].write(mvp_bytes)
        grass_prog["u_time"].value = t
        grass_prog["u_cam_pos"].value = tuple(camera.position)
        grass_prog["u_cam_right"].value = tuple(camera.flat_right())
        grass_vao.render(moderngl.TRIANGLES, instances=BLADE_COUNT)

        pygame.display.flip()
        pygame.display.set_caption(
            f"Voxel Meadow Instancing | {BLADE_COUNT:,} blades | {clock.get_fps():.0f} FPS")

    pygame.quit()


if __name__ == "__main__":
    main()