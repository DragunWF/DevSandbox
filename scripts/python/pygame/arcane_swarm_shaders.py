"""
Arcane Swarm Disintegration (Entity Dissolve)
=============================================
PyGame (state + 2D sprite drawing) + ModernGL (noise dissolve + glowing embers)

Controls:
    SPACE  - kill the enemy (starts the dissolve)
    R      - respawn the enemy (reset)
    ESC    - quit

Requirements:
    pip install pygame-ce moderngl numpy
"""

import sys
import math
import array

import pygame
import moderngl

WIDTH, HEIGHT = 800, 600
DISSOLVE_DURATION = 2.5   # seconds for dissolve_progress to go 0.0 -> 1.0


# =============================================================================
# GLSL SHADERS
# =============================================================================

VERTEX_SHADER = """
#version 330 core

// Full-screen quad: positions are in clip space (-1..1), uvs in (0..1)
in vec2 in_position;
in vec2 in_uv;

out vec2 v_uv;

void main() {
    v_uv = in_uv;
    gl_Position = vec4(in_position, 0.0, 1.0);
}
"""

FRAGMENT_SHADER = """
#version 330 core

uniform sampler2D u_texture;            // PyGame surface uploaded as a texture
uniform float     u_time;               // seconds since start (animates the noise)
uniform vec2      u_resolution;         // window size in pixels
uniform float     u_dissolve_threshold; // 0.0 = intact, 1.0 = fully dissolved

in  vec2 v_uv;
out vec4 f_color;

// -----------------------------------------------------------------------------
// TWEAKABLE LOOK PARAMETERS
// -----------------------------------------------------------------------------
// Dark slate void background
const vec3  BG_COLOR        = vec3(0.07, 0.09, 0.12);

// EDGE_WIDTH: thickness of the glowing burn band (in noise-value units, 0..1).
//   Bigger = thicker, more dramatic burning rim. Smaller = thin sharp ember line.
const float EDGE_WIDTH      = 0.10;

// GLOW_WIDTH: extra soft falloff band outside the hot edge (fades ember -> body).
const float GLOW_WIDTH      = 0.12;

// Ember colors. Swap these to change the "magic school":
//   emerald: vec3(0.1, 1.0, 0.4)   cyan: vec3(0.1, 0.9, 1.0)
const vec3  EMBER_CORE      = vec3(0.75, 1.00, 0.90);  // white-hot center of the edge
const vec3  EMBER_EMERALD   = vec3(0.05, 1.00, 0.45);  // saturated emerald
const vec3  EMBER_CYAN      = vec3(0.00, 0.85, 1.00);  // arcane cyan

// EMBER_INTENSITY: HDR-ish multiplier so the edge looks like it's blazing.
const float EMBER_INTENSITY = 2.2;

// NOISE_SCALE: size of the dissolve "blobs". Higher = finer, more granular decay.
const float NOISE_SCALE     = 5.0;

// -----------------------------------------------------------------------------
// 2D SIMPLEX NOISE (Ian McEwan / Stefan Gustavson)
// Returns roughly -1..1. Smooth, isotropic, cheap: ideal for dissolve masks.
// -----------------------------------------------------------------------------
vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec2 mod289(vec2 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec3 permute(vec3 x) { return mod289(((x * 34.0) + 1.0) * x); }

float snoise(vec2 v) {
    const vec4 C = vec4(0.211324865405187,   // (3.0 - sqrt(3.0)) / 6.0
                        0.366025403784439,   // 0.5 * (sqrt(3.0) - 1.0)
                       -0.577350269189626,   // -1.0 + 2.0 * C.x
                        0.024390243902439);  // 1.0 / 41.0
    // First corner
    vec2 i  = floor(v + dot(v, C.yy));
    vec2 x0 = v - i + dot(i, C.xx);

    // Other corners
    vec2 i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
    vec4 x12 = x0.xyxy + C.xxzz;
    x12.xy -= i1;

    // Permutations
    i = mod289(i);
    vec3 p = permute(permute(i.y + vec3(0.0, i1.y, 1.0))
                           + i.x + vec3(0.0, i1.x, 1.0));

    vec3 m = max(0.5 - vec3(dot(x0, x0), dot(x12.xy, x12.xy), dot(x12.zw, x12.zw)), 0.0);
    m = m * m;
    m = m * m;

    // Gradients
    vec3 x  = 2.0 * fract(p * C.www) - 1.0;
    vec3 h  = abs(x) - 0.5;
    vec3 ox = floor(x + 0.5);
    vec3 a0 = x - ox;

    m *= 1.79284291400159 - 0.85373472095314 * (a0 * a0 + h * h);

    vec3 g;
    g.x  = a0.x  * x0.x   + h.x  * x0.y;
    g.yz = a0.yz * x12.xz + h.yz * x12.yw;
    return 130.0 * dot(m, g);
}

// -----------------------------------------------------------------------------
// FRACTAL BROWNIAN MOTION: layer several octaves of simplex noise.
// Low octaves = big chunks eaten away; high octaves = crumbly ragged edges.
// Output remapped to 0..1.
// -----------------------------------------------------------------------------
float fbm(vec2 p) {
    float value     = 0.0;
    float amplitude = 0.5;
    for (int i = 0; i < 5; i++) {
        value     += amplitude * snoise(p);
        p         *= 2.0;     // lacunarity: each octave doubles frequency
        amplitude *= 0.5;     // gain: each octave halves contribution
    }
    return value * 0.5 + 0.5; // remap approx (-1..1) -> (0..1)
}

void main() {
    // PyGame surfaces are top-down; OpenGL textures are bottom-up. Flip Y.
    vec2 tex_uv = vec2(v_uv.x, 1.0 - v_uv.y);

    // Aspect-corrected coordinates so noise blobs aren't stretched on 800x600
    vec2 aspect_uv = v_uv * vec2(u_resolution.x / u_resolution.y, 1.0);

    vec4 sprite = texture(u_texture, tex_uv);

    // Start from the dark slate void
    vec3 color = BG_COLOR;

    // Only process pixels that actually belong to the enemy (alpha mask)
    if (sprite.a > 0.01) {

        // ---------------------------------------------------------------------
        // 1) PROCEDURAL NOISE FIELD
        //    Drifts slowly with u_time so the decay "crawls" and shimmers.
        //    Each pixel gets a value 0..1 that decides WHEN it burns.
        // ---------------------------------------------------------------------
        float noise = fbm(aspect_uv * NOISE_SCALE + vec2(0.0, u_time * 0.35));

        // Slightly bias dissolve so the rim erodes first and the core last.
        float radial = length(v_uv - 0.5) * 0.35;
        noise = clamp(noise * 0.85 + radial, 0.0, 1.0);

        // ---------------------------------------------------------------------
        // 2) THRESHOLD COMPARISON
        //    Remap progress so that at progress = 0 NOTHING is eaten, and at
        //    progress = 1 EVERYTHING (including the glow band) is gone.
        //    The extra (EDGE_WIDTH + GLOW_WIDTH) headroom guarantees the
        //    burning rim finishes passing over the last pixels.
        // ---------------------------------------------------------------------
        float band      = EDGE_WIDTH + GLOW_WIDTH;
        float threshold = u_dissolve_threshold * (1.0 + band);

        // dist > 0 : pixel survives.  dist < 0 : pixel is dissolved.
        // (the + band offset keeps the sprite fully intact at progress = 0)
        float dist = noise - threshold + band;

        // ---------------------------------------------------------------------
        // 3) DISCARD: noise fell below the threshold -> pixel is burned away
        //    (we draw the background instead of the sprite).
        // ---------------------------------------------------------------------
        if (dist < 0.0) {
            f_color = vec4(BG_COLOR, 1.0);
            return;
        }

        // ---------------------------------------------------------------------
        // 4) GLOWING EMBER EDGE
        //    Pixels with 0 < dist < EDGE_WIDTH are "just barely" alive: they
        //    are being burned right now. Make them blaze.
        //
        //    edge_t = 0.0 at the very burn front (hottest, white-emerald)
        //    edge_t = 1.0 at the inner side of the band (cooler, cyan)
        //
        //    -> Increase EDGE_WIDTH for a thicker burning rim.
        //    -> Increase GLOW_WIDTH for a wider soft halo blending into the body.
        // ---------------------------------------------------------------------
        float edge_t = clamp(dist / EDGE_WIDTH, 0.0, 1.0);
        float glow_t = clamp((dist - EDGE_WIDTH) / GLOW_WIDTH, 0.0, 1.0);

        // Base enemy color from the PyGame texture
        vec3 body = sprite.rgb;

        // Ember gradient: white-hot core -> emerald -> cyan as we move inward
        vec3 ember = mix(EMBER_CORE, EMBER_EMERALD, smoothstep(0.0, 0.35, edge_t));
        ember      = mix(ember,      EMBER_CYAN,    smoothstep(0.35, 1.0, edge_t));
        ember     *= EMBER_INTENSITY;

        // Flicker so the embers crackle (tiny high-frequency noise in time)
        float flicker = 0.85 + 0.30 * snoise(aspect_uv * 40.0 + u_time * 6.0);
        ember *= flicker;

        // Blend: inside the edge band -> pure ember.
        //        In the glow band     -> ember fades into the real body color.
        //        Past the glow band   -> untouched body color.
        float in_edge    = 1.0 - step(1.0, edge_t);   // 1 inside edge band
        vec3  glow_blend = mix(ember * 0.55 + body * 0.45, body, glow_t);
        color = mix(glow_blend, ember, in_edge);

        // Only apply the burning look once the dissolve has actually begun,
        // otherwise a living enemy would show a faint green rim.
        // NOTE: 'active' is a reserved word in GLSL, so we call it burn_on.
        float burn_on = smoothstep(0.0, 0.02, u_dissolve_threshold);
        color = mix(body, color, burn_on);
    }

    // Soft emissive halo around the surviving swarm (cheap fake bloom):
    // brighten the background slightly near burning pixels by sampling the
    // texture at a few offsets. Only while dissolving.
    // textureLod is used because we are inside divergent control flow.
    if (sprite.a <= 0.01 && u_dissolve_threshold > 0.0) {
        float halo = 0.0;
        for (int i = 0; i < 8; i++) {
            float a = float(i) * 0.785398;
            vec2 off = vec2(cos(a), sin(a)) * 0.012;
            halo += textureLod(u_texture, tex_uv + off, 0.0).a;
        }
        halo /= 8.0;
        // Fade the halo out as the entity vanishes completely
        float fade = 1.0 - smoothstep(0.85, 1.0, u_dissolve_threshold);
        color += EMBER_EMERALD * halo * 0.12 * fade
                 * smoothstep(0.0, 0.1, u_dissolve_threshold);
    }

    f_color = vec4(color, 1.0);
}
"""


# =============================================================================
# PYGAME SPRITE DRAWING
# =============================================================================

def draw_enemy(surface: pygame.Surface, t: float) -> None:
    """
    Draw a simple 'swarm' enemy onto an RGBA surface.
    Fully transparent background (alpha = 0) so the shader can treat alpha
    as the entity mask.
    """
    surface.fill((0, 0, 0, 0))
    cx, cy = WIDTH // 2, HEIGHT // 2

    # Pulsing main body: thick spiky polygon (a "swarm core")
    points = []
    spikes = 10
    for i in range(spikes * 2):
        angle = math.pi * i / spikes + t * 0.6
        radius = 130 + (35 if i % 2 == 0 else -20) + math.sin(t * 3 + i) * 5
        points.append((cx + math.cos(angle) * radius,
                       cy + math.sin(angle) * radius))
    pygame.draw.polygon(surface, (150, 40, 190, 255), points)
    pygame.draw.polygon(surface, (220, 120, 255, 255), points, 6)

    # Inner ring and core
    pygame.draw.circle(surface, (70, 15, 95, 255), (cx, cy), 80)
    pygame.draw.circle(surface, (255, 80, 120, 255), (cx, cy), 80, 5)
    pygame.draw.circle(surface, (255, 220, 90, 255), (cx, cy), 28)

    # Orbiting swarm "drones"
    for i in range(8):
        a = t * 1.4 + i * (math.tau / 8)
        px = cx + math.cos(a) * 185
        py = cy + math.sin(a) * 185
        pygame.draw.circle(surface, (200, 70, 160, 255), (int(px), int(py)), 16)
        pygame.draw.circle(surface, (255, 180, 220, 255), (int(px), int(py)), 16, 3)


# =============================================================================
# MAIN
# =============================================================================

def surface_to_bytes(surface: pygame.Surface) -> bytes:
    """pygame-ce renamed tostring -> tobytes; support both."""
    if hasattr(pygame.image, "tobytes"):
        return pygame.image.tobytes(surface, "RGBA", False)
    return pygame.image.tostring(surface, "RGBA", False)


def main() -> None:
    pygame.init()

    # --- macOS FIX: request a 3.3 CORE profile context BEFORE set_mode -------
    # Without these, macOS gives a legacy 2.1 context and ModernGL fails with
    # "Requested OpenGL version 330, got version 0".
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK,
                                    pygame.GL_CONTEXT_PROFILE_CORE)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True)

    pygame.display.set_caption("Arcane Swarm Disintegration  |  SPACE = kill, R = respawn")
    pygame.display.set_mode((WIDTH, HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF)
    clock = pygame.time.Clock()

    ctx = moderngl.create_context()

    # --- Shader program -------------------------------------------------------
    program = ctx.program(vertex_shader=VERTEX_SHADER,
                          fragment_shader=FRAGMENT_SHADER)

    # --- Full-screen quad (VBO + VAO) ----------------------------------------
    # Interleaved: x, y, u, v   (triangle strip, 4 verts)
    quad = array.array('f', [
        -1.0, -1.0, 0.0, 0.0,
         1.0, -1.0, 1.0, 0.0,
        -1.0,  1.0, 0.0, 1.0,
         1.0,  1.0, 1.0, 1.0,
    ])
    vbo = ctx.buffer(quad.tobytes())
    vao = ctx.vertex_array(program, [(vbo, '2f 2f', 'in_position', 'in_uv')])

    # --- Off-screen PyGame surface + GPU texture ------------------------------
    sprite_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA, 32)
    texture = ctx.texture((WIDTH, HEIGHT), 4)
    texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
    texture.repeat_x = False
    texture.repeat_y = False
    texture.use(location=0)
    program['u_texture'].value = 0
    program['u_resolution'].value = (float(WIDTH), float(HEIGHT))

    # --- State ----------------------------------------------------------------
    dissolving = False
    dissolve_progress = 0.0
    running = True

    while running:
        dt = clock.tick(60) / 1000.0
        t = pygame.time.get_ticks() / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    dissolving = True               # trigger death state
                elif event.key == pygame.K_r:
                    dissolving = False              # respawn
                    dissolve_progress = 0.0

        # Advance dissolve 0.0 -> 1.0 over DISSOLVE_DURATION seconds
        if dissolving:
            dissolve_progress = min(1.0, dissolve_progress + dt / DISSOLVE_DURATION)

        # Draw the enemy with PyGame, then upload to the GPU every frame
        draw_enemy(sprite_surface, t)
        texture.write(surface_to_bytes(sprite_surface))

        # Uniforms
        program['u_time'].value = t
        program['u_dissolve_threshold'].value = dissolve_progress

        # Render: dark slate void clear + full-screen quad
        ctx.clear(0.07, 0.09, 0.12, 1.0)
        texture.use(location=0)
        vao.render(moderngl.TRIANGLE_STRIP)

        pygame.display.flip()

    # Cleanup
    vao.release()
    vbo.release()
    texture.release()
    program.release()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()