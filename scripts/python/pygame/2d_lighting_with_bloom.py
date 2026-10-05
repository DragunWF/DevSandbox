"""
Interactive 2D Lighting with Bloom
==================================
PyGame (geometry + input) + ModernGL (GPU lighting / bloom via fragment shader)

Requirements:
    pip install pygame moderngl numpy

Controls:
    Mouse        - move the arcane point light
    Left click   - toggle light color (emerald <-> cyan)
    Mouse wheel  - adjust light radius
    ESC          - quit
"""

import math
import sys

import moderngl
import numpy as np
import pygame

WIDTH, HEIGHT = 800, 600

# --------------------------------------------------------------------------
# GLSL SHADERS
# --------------------------------------------------------------------------

VERTEX_SHADER = """
#version 330 core

// Full-screen quad: positions are in clip space (-1..1), UVs are 0..1.
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

in vec2 v_uv;
out vec4 fragColor;

uniform sampler2D u_scene;      // The PyGame surface uploaded as a texture
uniform float     u_time;       // Seconds since start
uniform vec2      u_resolution; // Window size in pixels
uniform vec2      u_mouse;      // Mouse position in pixels, Y already flipped for OpenGL
uniform vec3      u_light_color;// Light color (emerald or cyan), HDR-friendly
uniform float     u_radius;     // Light radius in pixels

// ----------------------------------------------------------------------
// TWEAKABLE CONSTANTS
// ----------------------------------------------------------------------
const float LIGHT_INTENSITY   = 2.2;   // Overall brightness of the light
const float FALLOFF_SHARPNESS = 2.0;   // Higher = tighter, more focused hotspot
const float AMBIENT           = 0.35;  // How much of the dark scene is visible unlit
const float BLOOM_THRESHOLD   = 0.18;  // Light level required before objects start to bloom
const float BLOOM_STRENGTH    = 1.6;   // Multiplier for bloom on lit objects
const float OBJECT_EDGE_GLOW  = 1.2;   // Strength of the crisp edge highlight
const int   BLOOM_TAPS        = 24;    // Samples for the blur (more = smoother, slower)
const float BLOOM_SPREAD      = 14.0;  // Blur radius in pixels

// Helper: perceptual luminance of a color
float luma(vec3 c) {
    return dot(c, vec3(0.2126, 0.7152, 0.0722));
}

// Helper: cheap pseudo-random hash used to rotate the blur kernel per pixel
float hash(vec2 p) {
    return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}

// Helper: ACES-ish filmic tonemap so additive blending doesn't clip harshly
vec3 tonemap(vec3 x) {
    const float a = 2.51, b = 0.03, c = 2.43, d = 0.59, e = 0.14;
    return clamp((x * (a * x + b)) / (x * (c * x + d) + e), 0.0, 1.0);
}

// ----------------------------------------------------------------------
// LIGHT FALLOFF
// Returns 0..~1+ brightness of the light at pixel position 'p'.
// ----------------------------------------------------------------------
float lightAt(vec2 p, vec2 lightPos) {
    // Distance in pixels from this pixel to the light
    float dist = distance(p, lightPos);

    // Normalize distance by radius: 0 at the light, 1 at the edge of its reach.
    float d = dist / u_radius;

    // (1) Smooth window: smoothstep fades the light to EXACTLY zero at the radius
    //     edge, so there is no hard cutoff ring.
    float window = 1.0 - smoothstep(0.0, 1.0, d);

    // (2) Inverse-square-style falloff: 1 / (1 + k*d^2) is the classic
    //     physically-inspired curve, softened with +1 so it doesn't blow up
    //     at d = 0. FALLOFF_SHARPNESS controls how quickly it drops.
    float invSq = 1.0 / (1.0 + FALLOFF_SHARPNESS * 8.0 * d * d);

    // (3) Multiply both: inverse-square gives the bright core, the window
    //     guarantees a clean fade-out to darkness.
    float falloff = invSq * window;

    // (4) Subtle "arcane" pulse - the light breathes slowly over time.
    float pulse = 1.0 + 0.08 * sin(u_time * 3.0) + 0.04 * sin(u_time * 7.3);

    return falloff * LIGHT_INTENSITY * pulse;
}

void main() {
    vec2 uv = v_uv;
    vec2 pixel = uv * u_resolution;  // Current pixel in pixel coordinates (Y-up)

    // ------------------------------------------------------------------
    // 1. SAMPLE THE BASE SCENE
    // ------------------------------------------------------------------
    vec3 scene = texture(u_scene, uv).rgb;

    // Detect "object" pixels. The background is very dark slate, objects are
    // lighter slate, so luminance separates them cleanly.
    // smoothstep gives a soft mask in 0..1 (0 = background, 1 = object).
    float objectMask = smoothstep(0.10, 0.16, luma(scene));

    // ------------------------------------------------------------------
    // 2. BASE ILLUMINATION (diffuse-style lighting)
    // ------------------------------------------------------------------
    float light = lightAt(pixel, u_mouse);

    // Tint the light with our emerald/cyan color. The scene is multiplied by
    // the light: surfaces only reflect what the light gives them.
    vec3 lit = scene * AMBIENT                 // dim ambient so the scene isn't pitch black
             + scene * u_light_color * light;  // colored diffuse lighting

    // Pure atmospheric glow: light scatters in the air even where no object
    // exists, giving a volumetric "fog of light" around the cursor.
    vec3 atmosphere = u_light_color * light * 0.55;

    // ------------------------------------------------------------------
    // 3. BLOOM (localized to lit geometry)
    // ------------------------------------------------------------------
    // We blur the *lit object brightness* by sampling neighboring pixels in a
    // spiral (Vogel disk) pattern. Bright, lit objects bleed light into the
    // surrounding area, which is what makes the glow look "hot".
    vec3 bloom = vec3(0.0);
    float angleJitter = hash(pixel + u_time) * 6.2831853; // per-pixel rotation hides banding

    for (int i = 0; i < BLOOM_TAPS; i++) {
        // Vogel disk: evenly distributed samples inside a unit circle.
        float r = sqrt((float(i) + 0.5) / float(BLOOM_TAPS));
        float theta = float(i) * 2.399963 + angleJitter; // golden angle
        vec2 offset = vec2(cos(theta), sin(theta)) * r * BLOOM_SPREAD;

        vec2 samplePx = pixel + offset;
        vec2 sampleUV = samplePx / u_resolution;

        vec3 s = texture(u_scene, sampleUV).rgb;
        float sMask = smoothstep(0.10, 0.16, luma(s)); // is the neighbor an object?
        float sLight = lightAt(samplePx, u_mouse);     // how lit is the neighbor?

        // Brightness threshold: only neighbors that are objects AND receive
        // enough light contribute. This keeps bloom crisp and localized,
        // not a global blur of the whole screen.
        float contribution = sMask * max(sLight - BLOOM_THRESHOLD, 0.0);

        // Weight samples near the center a bit more (soft kernel).
        float weight = 1.0 - r * 0.6;
        bloom += u_light_color * contribution * weight;
    }
    bloom /= float(BLOOM_TAPS);
    bloom *= BLOOM_STRENGTH * 3.0;

    // ------------------------------------------------------------------
    // 4. CRISP OBJECT HIGHLIGHT (additive "hot" core on lit geometry)
    // ------------------------------------------------------------------
    // Where an object is strongly lit, add a bright, near-white tinted hotspot
    // on top. This is the additive blend that makes lit walls look like they
    // are emitting energy.
    float hot = objectMask * max(light - BLOOM_THRESHOLD, 0.0);
    vec3 hotColor = mix(u_light_color, vec3(1.0), 0.45); // push toward white-hot
    vec3 highlight = hotColor * hot * OBJECT_EDGE_GLOW;

    // ------------------------------------------------------------------
    // 5. COMBINE (additive blending)
    // ------------------------------------------------------------------
    vec3 color = lit + atmosphere + bloom + highlight;

    // Soft vignette to add depth to the dark slate backdrop.
    vec2 centered = uv - 0.5;
    float vignette = 1.0 - dot(centered, centered) * 0.8;
    color *= vignette;

    // Tonemap HDR sum back into displayable range, preserving saturation.
    color = tonemap(color);

    // Tiny gamma tweak for a punchier look.
    color = pow(color, vec3(0.95));

    fragColor = vec4(color, 1.0);
}
"""

# --------------------------------------------------------------------------
# PYGAME SCENE
# --------------------------------------------------------------------------

BG_COLOR = (14, 18, 24)        # very dark slate
OBJ_COLOR = (52, 64, 80)       # lighter slate (walls / objects)
OBJ_COLOR_ALT = (62, 76, 94)   # slightly different slate for variety


def draw_scene(surface: pygame.Surface) -> None:
    """Draw static 'walls' and 'objects' onto the off-screen surface."""
    surface.fill(BG_COLOR)

    # Outer frame walls
    pygame.draw.rect(surface, OBJ_COLOR, (0, 0, WIDTH, 16))
    pygame.draw.rect(surface, OBJ_COLOR, (0, HEIGHT - 16, WIDTH, 16))
    pygame.draw.rect(surface, OBJ_COLOR, (0, 0, 16, HEIGHT))
    pygame.draw.rect(surface, OBJ_COLOR, (WIDTH - 16, 0, 16, HEIGHT))

    # Interior walls / blocks
    pygame.draw.rect(surface, OBJ_COLOR, (120, 100, 180, 28), border_radius=4)
    pygame.draw.rect(surface, OBJ_COLOR, (500, 140, 28, 220), border_radius=4)
    pygame.draw.rect(surface, OBJ_COLOR_ALT, (180, 300, 220, 36), border_radius=4)
    pygame.draw.rect(surface, OBJ_COLOR, (560, 440, 160, 28), border_radius=4)
    pygame.draw.rect(surface, OBJ_COLOR_ALT, (80, 440, 28, 100), border_radius=4)

    # Circular pillars / orbs
    pygame.draw.circle(surface, OBJ_COLOR_ALT, (400, 200), 46)
    pygame.draw.circle(surface, OBJ_COLOR, (660, 240), 34)
    pygame.draw.circle(surface, OBJ_COLOR, (300, 480), 40)
    pygame.draw.circle(surface, OBJ_COLOR_ALT, (130, 220), 28)

    # Ring (hollow circle) for variety
    pygame.draw.circle(surface, OBJ_COLOR, (450, 400), 56, width=10)

    # A little rune-like diamond
    pygame.draw.polygon(
        surface, OBJ_COLOR_ALT, [(690, 100), (730, 140), (690, 180), (650, 140)]
    )


# --------------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------------

def main() -> None:
    pygame.init()
    pygame.display.set_caption("Arcane Tech - 2D Lighting with Bloom")

    # Request an OpenGL 3.3 core context.
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
    pygame.display.gl_set_attribute(
        pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE
    )
    pygame.display.set_mode((WIDTH, HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF)
    clock = pygame.time.Clock()

    # ModernGL context bound to PyGame's OpenGL window
    ctx = moderngl.create_context()

    # Compile shaders
    prog = ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=FRAGMENT_SHADER)

    # Full-screen quad (triangle strip): x, y, u, v
    quad = np.array(
        [
            -1.0, -1.0, 0.0, 0.0,
             1.0, -1.0, 1.0, 0.0,
            -1.0,  1.0, 0.0, 1.0,
             1.0,  1.0, 1.0, 1.0,
        ],
        dtype="f4",
    )
    vbo = ctx.buffer(quad.tobytes())
    vao = ctx.vertex_array(prog, [(vbo, "2f 2f", "in_position", "in_uv")])

    # Off-screen PyGame surface containing our scene
    scene_surface = pygame.Surface((WIDTH, HEIGHT))
    draw_scene(scene_surface)

    # ModernGL texture to receive the surface pixels every frame
    texture = ctx.texture((WIDTH, HEIGHT), 3)  # RGB, 8 bits per channel
    texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
    texture.repeat_x = False
    texture.repeat_y = False

    # Light colors
    EMERALD = (0.05, 1.0, 0.45)
    CYAN = (0.10, 0.85, 1.0)
    light_colors = [EMERALD, CYAN]
    color_index = 0
    radius = 260.0

    prog["u_scene"].value = 0
    prog["u_resolution"].value = (float(WIDTH), float(HEIGHT))

    running = True
    while running:
        # ---------------- Input ----------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    color_index = (color_index + 1) % len(light_colors)
                elif event.button == 4:   # wheel up (legacy)
                    radius = min(radius + 20.0, 600.0)
                elif event.button == 5:   # wheel down (legacy)
                    radius = max(radius - 20.0, 80.0)
            elif event.type == pygame.MOUSEWHEEL:
                radius = float(np.clip(radius + event.y * 20.0, 80.0, 600.0))

        mx, my = pygame.mouse.get_pos()
        # PyGame has Y=0 at the top; OpenGL has Y=0 at the bottom, so flip Y.
        mouse_gl = (float(mx), float(HEIGHT - my))

        t = pygame.time.get_ticks() / 1000.0

        # ---------------- Surface -> GPU ----------------
        # Redraw the scene each frame (cheap here, and allows animation later).
        draw_scene(scene_surface)

        # Extract raw pixel bytes. The 'flipped=True' flag flips vertically so
        # row 0 of the data is the BOTTOM of the image, matching OpenGL's
        # texture coordinate convention (v=0 at bottom).
        raw = pygame.image.tobytes(scene_surface, "RGB", True)
        texture.write(raw)

        # ---------------- Uniforms ----------------
        prog["u_time"].value = t
        prog["u_mouse"].value = mouse_gl
        prog["u_light_color"].value = light_colors[color_index]
        prog["u_radius"].value = radius

        # ---------------- Draw ----------------
        ctx.clear(0.0, 0.0, 0.0)
        texture.use(location=0)
        vao.render(moderngl.TRIANGLE_STRIP)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()