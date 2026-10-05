"""
Low-Poly Tech Core (Normals & Dynamic Lighting)
-----------------------------------------------
PyGame  -> window + events only
ModernGL-> GPU context, buffers, shaders, draw calls
pyrr    -> Model / View / Projection matrices
NumPy   -> hardcoded geometry

Install:  pip install pygame moderngl pyrr numpy
Controls: ESC or close window to quit.
"""

import sys
import math
import numpy as np
import pygame
import moderngl
from pyrr import Matrix44

WIDTH, HEIGHT = 800, 600

# ----------------------------------------------------------------------------
# GLSL SHADERS
# ----------------------------------------------------------------------------
VERTEX_SHADER = """
#version 330 core

// Per-vertex data coming from the VBO
in vec3 in_position;   // vertex position in MODEL (object) space
in vec3 in_normal;     // vertex normal in MODEL space (unit length)

// Matrices. Kept separate so each stage of the pipeline is easy to see.
uniform mat4 u_model;       // object space -> world space (rotation)
uniform mat4 u_view;        // world space  -> camera space
uniform mat4 u_projection;  // camera space -> clip space (perspective)

// Data interpolated across the triangle and sent to the fragment shader
out vec3 v_world_pos;   // fragment position in WORLD space
out vec3 v_normal;      // surface normal in WORLD space

void main() {
    // 1) Move the vertex into world space. We need the world position in the
    //    fragment shader to build the "surface -> light" and "surface -> eye"
    //    vectors, because both the light and camera are defined in world space.
    vec4 world_pos = u_model * vec4(in_position, 1.0);
    v_world_pos = world_pos.xyz;

    // 2) Transform the NORMAL into world space.
    //    Normals are directions, not points, so they must NOT be moved
    //    like positions when the model is scaled or sheared. The correct
    //    transform is the "normal matrix" = transpose(inverse(model)).
    //    (For pure rotation this equals the model matrix, but this is
    //    the habit that keeps lighting right when you add scaling.)
    mat3 normal_matrix = transpose(inverse(mat3(u_model)));
    v_normal = normalize(normal_matrix * in_normal);

    // 3) Full MVP chain: Projection * View * Model * position.
    //    Read right-to-left: model -> world -> camera -> clip space.
    //    The GPU then divides by w (perspective divide) to reach the screen.
    gl_Position = u_projection * u_view * world_pos;
}
"""

FRAGMENT_SHADER = """
#version 330 core

in vec3 v_world_pos;
in vec3 v_normal;

uniform vec3  u_light_pos;     // point light position (world space)
uniform vec3  u_light_color;   // emerald <-> cyan, animated on the CPU
uniform vec3  u_camera_pos;    // eye position (world space)
uniform vec3  u_base_color;    // dark polished slate albedo

out vec4 f_color;

void main() {
    // ---- Geometry vectors (all normalized, so dot() == cos(angle)) --------
    vec3 N = normalize(v_normal);                    // surface normal
    vec3 L = normalize(u_light_pos - v_world_pos);   // surface -> light
    vec3 V = normalize(u_camera_pos - v_world_pos);  // surface -> eye

    // ---- AMBIENT -----------------------------------------------------------
    // A tiny constant glow so faces turned away from the light are not
    // pure black. It is tinted slightly by the light for a cohesive mood.
    vec3 ambient = 0.06 * u_base_color + 0.015 * u_light_color;

    // ---- DIFFUSE (Lambert) -------------------------------------------------
    // dot(N, L) = cos(theta), where theta is the angle between the normal and
    // the direction to the light:
    //   * facing the light head-on  -> theta = 0   -> dot = 1  (brightest)
    //   * light grazing the surface -> theta = 90  -> dot = 0  (dark)
    //   * facing away               -> dot < 0     -> clamp to 0 with max()
    // Because this mesh uses FLAT normals (one normal per face), every pixel
    // on a facet gets the same N, giving crisp low-poly shading.
    float n_dot_l = max(dot(N, L), 0.0);
    vec3 diffuse = n_dot_l * u_light_color * u_base_color * 2.2;

    // ---- SPECULAR (Blinn-Phong) -------------------------------------------
    // The "half vector" H lies exactly between the light and eye directions.
    // A mirror-like reflection toward the eye occurs when the surface normal
    // points along H, so dot(N, H) measures how close we are to the perfect
    // reflection angle:  1 = perfect mirror alignment, 0 = 90 degrees off.
    vec3 H = normalize(L + V);
    float n_dot_h = max(dot(N, H), 0.0);

    // Raising to a high power (shininess) shrinks the highlight to a small,
    // tight spot. 128 gives a hard, polished-stone glint.
    float spec = pow(n_dot_h, 128.0);

    // Extra crispness: add a hard-edged smoothstep "glint" on top of the
    // smooth falloff so highlights look like cut facets catching light.
    float crisp = spec * 0.8 + smoothstep(0.35, 0.45, spec) * 1.2;

    // Only light up the specular if the face actually faces the light,
    // otherwise back-facing H alignment could leak a highlight.
    crisp *= step(0.0001, n_dot_l);

    // Specular color: the light's color pushed toward white for a hot core.
    vec3 spec_color = mix(u_light_color, vec3(1.0), 0.35);
    vec3 specular = crisp * spec_color * 2.5;

    // ---- Distance attenuation (inverse-square-ish falloff) ----------------
    float dist = length(u_light_pos - v_world_pos);
    float attenuation = 1.0 / (1.0 + 0.09 * dist + 0.03 * dist * dist);
    attenuation *= 4.0;  // overall light intensity

    // ---- Combine -----------------------------------------------------------
    vec3 color = ambient + (diffuse + specular) * attenuation;

    // Simple tone-map to avoid harsh clipping, then gamma-correct to sRGB.
    color = color / (color + vec3(1.0)) * 1.35;
    color = pow(color, vec3(1.0 / 2.2));

    f_color = vec4(color, 1.0);
}
"""


# ----------------------------------------------------------------------------
# GEOMETRY: flat-shaded icosahedron (20 triangular faces)
# ----------------------------------------------------------------------------
def build_icosahedron():
    """Return interleaved float32 array [px,py,pz, nx,ny,nz] per vertex.

    Vertices are NOT shared between faces: each triangle gets its own 3
    vertices with the same face normal. This gives the faceted flat-shaded
    look (sharing vertices would average normals and look smooth).
    """
    t = (1.0 + math.sqrt(5.0)) / 2.0  # golden ratio

    base = np.array([
        (-1,  t,  0), ( 1,  t,  0), (-1, -t,  0), ( 1, -t,  0),
        ( 0, -1,  t), ( 0,  1,  t), ( 0, -1, -t), ( 0,  1, -t),
        ( t,  0, -1), ( t,  0,  1), (-t,  0, -1), (-t,  0,  1),
    ], dtype=np.float32)
    base /= np.linalg.norm(base, axis=1, keepdims=True)  # put on unit sphere

    faces = [
        (0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
        (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
        (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
        (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1),
    ]

    data = []
    for i0, i1, i2 in faces:
        a, b, c = base[i0], base[i1], base[i2]
        # Face normal = cross product of two triangle edges.
        n = np.cross(b - a, c - a)
        n /= np.linalg.norm(n)
        # Guarantee counter-clockwise winding as seen from outside, so
        # CULL_FACE removes only the back faces. The shape is centered on
        # the origin, so a correct outward normal points away from the
        # triangle's centroid.
        centroid = (a + b + c) / 3.0
        if np.dot(n, centroid) < 0:
            b, c = c, b
            n = -n
        for v in (a, b, c):
            data.append(np.concatenate([v, n]))

    return np.array(data, dtype=np.float32)


# ----------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------
def main():
    pygame.init()
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
    pygame.display.gl_set_attribute(
        pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
    pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)
    pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
    pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 4)
    pygame.display.set_mode((WIDTH, HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF)
    pygame.display.set_caption("Low-Poly Tech Core")
    clock = pygame.time.Clock()

    # --- ModernGL context: depth testing + back-face culling ----------------
    ctx = moderngl.create_context()
    ctx.enable(moderngl.DEPTH_TEST | moderngl.CULL_FACE)

    prog = ctx.program(vertex_shader=VERTEX_SHADER,
                       fragment_shader=FRAGMENT_SHADER)

    # --- Pack geometry into a VBO and bind it to a VAO ----------------------
    vertices = build_icosahedron()
    vbo = ctx.buffer(vertices.tobytes())
    vao = ctx.vertex_array(prog, [(vbo, "3f 3f", "in_position", "in_normal")])

    # --- Static matrices -----------------------------------------------------
    # PROJECTION: perspective frustum. Squashes the 3D view volume into clip
    # space so far things look smaller. Args: vertical FOV (deg), aspect
    # ratio, near plane, far plane.
    projection = Matrix44.perspective_projection(
        45.0, WIDTH / HEIGHT, 0.1, 100.0, dtype="f4")

    # VIEW: the camera. look_at(eye, target, up) builds the matrix that moves
    # the whole world so the camera sits at the origin looking down -Z.
    # Here the camera is fixed at z=5, staring at the center of the core.
    camera_pos = np.array([0.0, 0.8, 5.0], dtype="f4")
    view = Matrix44.look_at(
        camera_pos,                                  # eye
        np.array([0.0, 0.0, 0.0], dtype="f4"),       # target (center)
        np.array([0.0, 1.0, 0.0], dtype="f4"),       # up
        dtype="f4")

    # Palette
    emerald = np.array([0.05, 1.00, 0.35], dtype="f4")  # saturated green
    cyan = np.array([0.00, 0.85, 1.00], dtype="f4")     # arcane cyan

    # Constant uniforms
    # NOTE: pyrr matrices are stored so that .tobytes() is already in the
    # layout OpenGL expects, so we can upload them directly.
    prog["u_projection"].write(projection.astype("f4").tobytes())
    prog["u_view"].write(view.astype("f4").tobytes())
    prog["u_camera_pos"].value = tuple(camera_pos)
    prog["u_base_color"].value = (0.14, 0.17, 0.21)  # dark polished slate

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        t = pygame.time.get_ticks() / 1000.0

        # --- Animated MODEL matrix -------------------------------------------
        # Rotate around Y and a little around X so every facet eventually
        # sweeps through the light. Matrix multiplication order matters.
        model = (Matrix44.from_x_rotation(t * 0.35, dtype="f4") *
                 Matrix44.from_y_rotation(t * 0.60, dtype="f4"))

        # --- Orbiting point light --------------------------------------------
        # Circle in the XZ plane with a vertical bob, radius 3 so it stays
        # outside the core (radius 1).
        radius = 3.0
        light_pos = (radius * math.cos(t * 1.1),
                     1.4 * math.sin(t * 0.8),
                     radius * math.sin(t * 1.1))

        # Light color slides between emerald and cyan (0..1 sine blend).
        blend = 0.5 + 0.5 * math.sin(t * 0.9)
        light_color = emerald * (1.0 - blend) + cyan * blend

        prog["u_model"].write(model.astype("f4").tobytes())
        prog["u_light_pos"].value = light_pos
        prog["u_light_color"].value = tuple(light_color)

        # --- Render ------------------------------------------------------------
        ctx.clear(0.035, 0.045, 0.065, 1.0)  # deep dark slate void (+ depth)
        vao.render(moderngl.TRIANGLES)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()