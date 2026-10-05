"""
Fluid Dash & Weapon Trailing (Temporal Blending)  --  "Arcane Tech" edition
===========================================================================
Requirements:  pip install pygame moderngl numpy   (numpy is only used for the quad)

Controls:
    Mouse        - the player chases the cursor (fast, snappy dash)
    SPACE (hold) - overdrive: even faster chase
    ESC          - quit
    (If you don't touch the mouse, the player auto-dashes in a Lissajous
     pattern so you can see the effect immediately.)

HOW THE EFFECT WORKS (read this first!)
---------------------------------------
Temporal blending = "remember what was on screen last frame, fade it a bit,
then draw the new stuff on top." We keep that memory in an *accumulation
buffer*: a texture attached to a Framebuffer Object (FBO).

A GPU cannot safely read from and write to the SAME texture in one draw call,
so we use TWO FBOs and "ping-pong" between them:

    frame N  : read  accum[0]  ->  write accum[1]
    frame N+1: read  accum[1]  ->  write accum[0]
    ...

Each frame has two passes:

  PASS 1 (build accumulation):
     a) Draw previous accumulation texture into the *write* FBO through the
        TRAIL shader (decay + tint + tiny blur).  Blending OFF (we overwrite).
     b) Draw this frame's PyGame sprite texture on top with ADDITIVE blending
        (src + dst), so the fresh player glows hot over the fading trail.

  PASS 2 (present):
     Clear the real screen to a deep slate color, then additively draw the
     accumulation texture over it.

To avoid "stuttering ghost sprites" when the player moves many pixels per
frame, we (1) draw the sprite as a dense chain of circles along the path
travelled this frame, and (2) blur the trail slightly every frame, so the
history diffuses into continuous plasma.
"""

import math
import array
import pygame
import moderngl

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------
WIDTH, HEIGHT = 800, 600
FPS = 60

# Trail look.  u_decay is "fraction of brightness kept per 1/60 s".
# 0.0 = instantly gone, 1.0 = never fades.  ~0.93 gives a long, silky tail.
DECAY_PER_FRAME = 0.93
TRAIL_SPREAD = 1.2              # blur radius in texels (higher = gooier plasma)
SLATE_BG = (0.020, 0.035, 0.050)  # deep dark slate void (linear 0..1)

# Colors (0..1 RGB).
CYAN_TINT = (0.00, 0.85, 1.00)     # arcane cyan   -> u_tint_color (old/dim trail)
EMERALD_HOT = (0.10, 1.00, 0.45)   # luminous emerald -> u_hot_color (fresh/bright trail)

# --------------------------------------------------------------------------
# GLSL
# --------------------------------------------------------------------------
# One shared vertex shader: just draws a fullscreen quad and passes UVs along.
VERTEX_SHADER = """
#version 330 core
in vec2 in_pos;   // clip-space position  (-1..1)
in vec2 in_uv;    // texture coordinate   ( 0..1)
out vec2 v_uv;
void main() {
    v_uv = in_uv;
    gl_Position = vec4(in_pos, 0.0, 1.0);
}
"""

# TRAIL shader: reads LAST frame's accumulation and produces the NEXT,
# slightly dimmer, re-colored, slightly blurred version of it.
TRAIL_FRAGMENT_SHADER = """
#version 330 core
uniform sampler2D u_prev;       // previous frame's accumulation texture
uniform float     u_decay;      // brightness multiplier per frame (0..1)
uniform vec3      u_tint_color; // cyan   : what the trail turns into as it fades
uniform vec3      u_hot_color;  // emerald: what bright, young trail looks like
uniform vec2      u_texel;      // 1.0 / resolution (size of one pixel in UV)
uniform float     u_spread;     // blur radius in pixels

in  vec2 v_uv;
out vec4 f_color;

void main() {
    // --- 1. Fluid diffusion --------------------------------------------
    // A tiny 5-tap cross blur (weights sum to 1.0, so no energy is added).
    // Applied EVERY frame, the history keeps smearing outward, which turns
    // a chain of discrete sprite stamps into smooth, flowing plasma.
    vec2 o = u_texel * u_spread;
    vec3 c = texture(u_prev, v_uv).rgb * 0.40;
    c += texture(u_prev, v_uv + vec2( o.x, 0.0)).rgb * 0.15;
    c += texture(u_prev, v_uv + vec2(-o.x, 0.0)).rgb * 0.15;
    c += texture(u_prev, v_uv + vec2(0.0,  o.y)).rgb * 0.15;
    c += texture(u_prev, v_uv + vec2(0.0, -o.y)).rgb * 0.15;

    // --- 2. Brightness -> "age" ----------------------------------------
    // The trail only stores light, not age. But light fades monotonically,
    // so BRIGHTNESS is a free proxy for age: bright = young, dim = old.
    float lum = dot(c, vec3(0.299, 0.587, 0.114));
    float heat = smoothstep(0.02, 0.60, lum);   // 0 = old/dim, 1 = young/bright

    // --- 3. Re-color the trail -----------------------------------------
    // Palette: young pixels -> blazing emerald, old pixels -> arcane cyan.
    vec3 palette = mix(u_tint_color, u_hot_color, heat);
    // Re-tint using luminance only (discard the original sprite colors),
    // then boost slightly so the plasma looks self-illuminated.
    vec3 tinted = palette * lum * 1.15;
    // Keep a little of the original color so the transition isn't harsh.
    c = mix(c, tinted, 0.35);

    // --- 4. DECAY MATH -------------------------------------------------
    // (a) Multiplicative decay: exponential falloff, the "natural" look.
    //     After n frames brightness = original * u_decay^n.
    c *= u_decay;
    // (b) Tiny linear subtraction: pure multiplication only approaches zero
    //     asymptotically, leaving a faint permanent haze. Subtracting a
    //     sliver guarantees the trail fully disappears. (The accumulation
    //     buffer is half-float, so such small values are representable and
    //     don't get stuck from 8-bit rounding.)
    c = max(c - vec3(0.0015), vec3(0.0));

    f_color = vec4(c, 1.0);
}
"""

# SPRITE shader: draws the PyGame surface texture (straight RGBA) as
# premultiplied light so additive blending behaves correctly.
SPRITE_FRAGMENT_SHADER = """
#version 330 core
uniform sampler2D u_tex;
in  vec2 v_uv;
out vec4 f_color;
void main() {
    vec4 s = texture(u_tex, v_uv);
    f_color = vec4(s.rgb * s.a, 1.0);   // alpha acts as intensity of light
}
"""

# PRESENT shader: draws the accumulation buffer to the screen with a soft
# tone-map so overlapping additive light rolls off to white instead of clipping.
PRESENT_FRAGMENT_SHADER = """
#version 330 core
uniform sampler2D u_tex;
in  vec2 v_uv;
out vec4 f_color;
void main() {
    vec3 c = texture(u_tex, v_uv).rgb;
    c = 1.0 - exp(-c * 1.8);            // filmic-ish soft shoulder
    f_color = vec4(c, 1.0);
}
"""


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def surface_to_bytes(surf):
    """Raw RGBA bytes, flipped vertically (PyGame is top-left, GL is bottom-left)."""
    fn = getattr(pygame.image, "tobytes", None) or pygame.image.tostring
    return fn(surf, "RGBA", True)


def draw_player(surf, prev_pos, pos, angle):
    """
    Draw the player onto a transparent PyGame surface.

    Fast movement means the player jumps many pixels per frame. If we only
    drew one shape at `pos`, the trail would be a row of separate stamps.
    Instead we stamp circles along the whole segment prev_pos -> pos so the
    path is continuous before the shader even touches it.
    """
    surf.fill((0, 0, 0, 0))  # fully transparent background

    dx, dy = pos[0] - prev_pos[0], pos[1] - prev_pos[1]
    dist = math.hypot(dx, dy)
    radius = 13
    steps = max(1, int(dist / (radius * 0.35)))   # dense overlap along the path
    for i in range(steps + 1):
        t = i / steps
        x = prev_pos[0] + dx * t
        y = prev_pos[1] + dy * t
        # Dim body stamps so the "head" outshines the swept path.
        pygame.draw.circle(surf, (60, 230, 170, 150), (int(x), int(y)), radius)

    # Head: a bright arrow/dart pointing along the travel direction + white core.
    cx, cy = pos
    pts = []
    for ang, r in ((0.0, 26), (2.45, 18), (math.pi, 6), (-2.45, 18)):
        pts.append((cx + math.cos(angle + ang) * r, cy + math.sin(angle + ang) * r))
    pygame.draw.polygon(surf, (150, 255, 220, 255), pts)
    pygame.draw.circle(surf, (255, 255, 255, 255), (int(cx), int(cy)), 6)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main():
    pygame.init()
    pygame.display.set_caption("Fluid Dash - Temporal Blending (ModernGL)")
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK,
                                    pygame.GL_CONTEXT_PROFILE_CORE)
    pygame.display.set_mode((WIDTH, HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF)
    clock = pygame.time.Clock()

    ctx = moderngl.create_context()

    # ---- Shader programs ------------------------------------------------
    trail_prog = ctx.program(vertex_shader=VERTEX_SHADER,
                             fragment_shader=TRAIL_FRAGMENT_SHADER)
    sprite_prog = ctx.program(vertex_shader=VERTEX_SHADER,
                              fragment_shader=SPRITE_FRAGMENT_SHADER)
    present_prog = ctx.program(vertex_shader=VERTEX_SHADER,
                               fragment_shader=PRESENT_FRAGMENT_SHADER)

    # ---- Fullscreen quad (triangle strip): x, y, u, v -------------------
    quad = ctx.buffer(array.array("f", [
        -1.0, -1.0, 0.0, 0.0,
         1.0, -1.0, 1.0, 0.0,
        -1.0,  1.0, 0.0, 1.0,
         1.0,  1.0, 1.0, 1.0,
    ]).tobytes())
    trail_vao = ctx.vertex_array(trail_prog, [(quad, "2f 2f", "in_pos", "in_uv")])
    sprite_vao = ctx.vertex_array(sprite_prog, [(quad, "2f 2f", "in_pos", "in_uv")])
    present_vao = ctx.vertex_array(present_prog, [(quad, "2f 2f", "in_pos", "in_uv")])

    # ---- Accumulation buffers: the ping-pong FBO pair -------------------
    # dtype="f2" = 16-bit float per channel. With 8-bit textures, the small
    # per-frame decay (e.g. 200 * 0.93 = 186) would round and eventually get
    # STUCK at low values, leaving ugly permanent banding/ghosts. Floats keep
    # sub-1/255 precision, so the trail fades smoothly all the way to black.
    accum_tex = []
    accum_fbo = []
    for _ in range(2):
        tex = ctx.texture((WIDTH, HEIGHT), 4, dtype="f2")
        tex.filter = (moderngl.LINEAR, moderngl.LINEAR)   # smooth sampling for the blur
        tex.repeat_x = False                               # clamp at the borders so
        tex.repeat_y = False                               # the trail doesn't wrap
        fbo = ctx.framebuffer(color_attachments=[tex])     # render target wrapping tex
        fbo.use()
        fbo.clear(0.0, 0.0, 0.0, 1.0)                      # start with an empty history
        accum_tex.append(tex)
        accum_fbo.append(fbo)

    read_idx = 0   # which buffer holds "last frame"; the other one is written to

    # ---- Sprite texture (PyGame surface uploaded every frame) -----------
    player_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA, 32)
    sprite_tex = ctx.texture((WIDTH, HEIGHT), 4)
    sprite_tex.filter = (moderngl.LINEAR, moderngl.LINEAR)

    # ---- Constant uniforms ----------------------------------------------
    trail_prog["u_tint_color"].value = CYAN_TINT
    trail_prog["u_hot_color"].value = EMERALD_HOT
    trail_prog["u_texel"].value = (1.0 / WIDTH, 1.0 / HEIGHT)
    trail_prog["u_spread"].value = TRAIL_SPREAD
    trail_prog["u_prev"].value = 0       # texture unit 0
    sprite_prog["u_tex"].value = 0
    present_prog["u_tex"].value = 0

    # ---- Player state ---------------------------------------------------
    pos = [WIDTH / 2, HEIGHT / 2]
    prev_pos = list(pos)
    angle = 0.0
    last_mouse = pygame.mouse.get_pos()
    last_mouse_move_time = -999.0
    t_total = 0.0

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        dt = min(dt, 0.05)
        t_total += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        # ---------------- Movement (PyGame side) ----------------
        mouse = pygame.mouse.get_pos()
        if mouse != last_mouse:
            last_mouse = mouse
            last_mouse_move_time = t_total

        if t_total - last_mouse_move_time < 3.0:
            target = mouse
        else:
            # Idle demo: wide Lissajous figure so the trail is visible.
            target = (WIDTH / 2 + math.sin(t_total * 1.7) * 300,
                      HEIGHT / 2 + math.sin(t_total * 2.3 + 1.0) * 210)

        # Exponential chase = frame-rate independent, very snappy "dash" feel.
        speed = 26.0 if pygame.key.get_pressed()[pygame.K_SPACE] else 13.0
        k = 1.0 - math.exp(-speed * dt)
        prev_pos = list(pos)
        pos[0] += (target[0] - pos[0]) * k
        pos[1] += (target[1] - pos[1]) * k

        vx, vy = pos[0] - prev_pos[0], pos[1] - prev_pos[1]
        if math.hypot(vx, vy) > 0.5:
            angle = math.atan2(vy, vx)

        # ---------------- PyGame surface -> GPU texture ----------------
        draw_player(player_surf, prev_pos, pos, angle)
        sprite_tex.write(surface_to_bytes(player_surf))

        # ======================================================================
        # PASS 1: build the new accumulation buffer (ping-pong step)
        # ======================================================================
        write_idx = 1 - read_idx
        accum_fbo[write_idx].use()          # all draws now go into the write FBO

        # (a) Re-draw LAST frame's history through the decay/tint shader.
        #     Blending is OFF: we want to REPLACE whatever is in the write FBO
        #     (which holds stale data from two frames ago) with the processed copy.
        ctx.disable(moderngl.BLEND)
        # Frame-rate independent decay: DECAY_PER_FRAME is defined at 60 FPS;
        # pow() rescales it to the real frame time so the trail length is constant.
        trail_prog["u_decay"].value = DECAY_PER_FRAME ** (dt * 60.0)
        accum_tex[read_idx].use(location=0)
        trail_vao.render(moderngl.TRIANGLE_STRIP)

        # (b) Add the NEW player sprite on top with ADDITIVE blending:
        #       result = src.rgb * 1 + dst.rgb * 1
        #     so the fresh player stacks light onto the fading trail instead of
        #     covering it up.
        ctx.enable(moderngl.BLEND)
        ctx.blend_func = moderngl.ONE, moderngl.ONE
        sprite_tex.use(location=0)
        sprite_vao.render(moderngl.TRIANGLE_STRIP)

        # ======================================================================
        # PASS 2: present to the real window
        # ======================================================================
        ctx.screen.use()
        ctx.disable(moderngl.BLEND)
        ctx.screen.clear(*SLATE_BG, 1.0)    # deep slate void BEHIND the FBO layer

        # Additively composite the glowing accumulation buffer over the void.
        ctx.enable(moderngl.BLEND)
        ctx.blend_func = moderngl.ONE, moderngl.ONE
        accum_tex[write_idx].use(location=0)
        present_vao.render(moderngl.TRIANGLE_STRIP)

        # Swap roles: what we just wrote becomes next frame's "previous".
        read_idx = write_idx

        pygame.display.flip()
        pygame.display.set_caption(f"Fluid Dash - Temporal Blending | {clock.get_fps():.0f} FPS")

    pygame.quit()


if __name__ == "__main__":
    main()