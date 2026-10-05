import sys
import array
import pygame
import moderngl

# ============================================================================
# SHADER DEFINITIONS
# ============================================================================

# Vertex Shader: A simple pass-through shader.
# It takes standard 2D quad coordinates and passes them directly to the screen.
VERTEX_SHADER = '''
#version 330 core

in vec2 in_position;

void main() {
    // Map the 2D position to 3D space, occupying the full screen [-1, 1]
    gl_Position = vec4(in_position, 0.0, 1.0);
}
'''

# Fragment Shader: The core procedural generation engine.
# Utilizes Domain Warping and Fractional Brownian Motion (fBm) to create
# an "Arcane Energy Plasma" with a glassmorphic aesthetic.
FRAGMENT_SHADER = '''
#version 330 core

out vec4 fragColor;

// Uniforms passed from the Python application
uniform vec2 u_resolution;
uniform float u_time;

// ---------------------------------------------------------------------------
// PSEUDO-RANDOM HASH & NOISE FUNCTIONS
// ---------------------------------------------------------------------------

// A standard 2D hash function to generate deterministic pseudo-random values
vec2 hash(vec2 p) {
    // Dot products with arbitrary irrational numbers to scatter values
    p = vec2(dot(p, vec2(127.1, 311.7)),
             dot(p, vec2(269.5, 183.3)));
    return -1.0 + 2.0 * fract(sin(p) * 43758.5453123);
}

// Simplex-style 2D gradient noise
float noise(vec2 p) {
    const float K1 = 0.366025404; // (sqrt(3)-1)/2
    const float K2 = 0.211324865; // (3-sqrt(3))/6

    // Skew the input space to determine which simplex cell we're in
    vec2 i = floor(p + (p.x + p.y) * K1);
    vec2 a = p - i + (i.x + i.y) * K2;
    vec2 o = (a.x > a.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
    
    vec2 b = a - o + K2;
    vec2 c = a - 1.0 + 2.0 * K2;

    // Calculate radial falloffs for the corners
    vec3 h = max(0.5 - vec3(dot(a, a), dot(b, b), dot(c, c)), 0.0);
    
    // Compute gradients and sum up the noise value
    vec3 n = h * h * h * h * vec3(dot(a, hash(i + 0.0)),
                                  dot(b, hash(i + o)),
                                  dot(c, hash(i + 1.0)));
    return dot(n, vec3(70.0));
}

// ---------------------------------------------------------------------------
// FRACTIONAL BROWNIAN MOTION (fBm)
// ---------------------------------------------------------------------------

// fBm stacks multiple layers (octaves) of noise.
// Each subsequent layer has higher frequency (detail) and lower amplitude (influence).
float fbm(vec2 uv) {
    float f = 0.0;
    float amp = 0.5;
    float freq = 1.0;
    
    // A rotation matrix used to rotate the domain per octave to break up grid artifacts
    mat2 rot = mat2(1.6,  1.2, 
                   -1.2,  1.6);
                   
    for(int i = 0; i < 5; i++) {
        f += amp * noise(uv * freq);
        uv = rot * uv; // Rotate and scale the domain
        amp *= 0.5;    // Decrease amplitude (less impact)
    }
    return f;
}

// ---------------------------------------------------------------------------
// MAIN RENDERING LOGIC
// ---------------------------------------------------------------------------

void main() {
    // 1. Normalize pixel coordinates (from 0 to 1) and correct for aspect ratio
    vec2 uv = gl_FragCoord.xy / u_resolution.xy;
    uv = uv * 2.0 - 1.0;            // Remap to [-1, 1]
    uv.x *= u_resolution.x / u_resolution.y; // Aspect ratio fix
    
    // Global animation speed
    float t = u_time * 0.3;

    // 2. DOMAIN WARPING (The Secret to Liquid Dynamics)
    // We displace the UV coordinates using fBm, then feed those displaced 
    // coordinates into ANOTHER fBm. This creates flowing, folding liquid ridges.
    
    // First warp layer (q)
    vec2 q = vec2(0.0);
    q.x = fbm(uv + vec2(0.0, 0.0) + t * 0.4);
    q.y = fbm(uv + vec2(5.2, 1.3) - t * 0.3);

    // Second warp layer (r), utilizing the first warp (q)
    vec2 r = vec2(0.0);
    r.x = fbm(uv + 4.0 * q + vec2(1.7, 9.2) + t * 0.6);
    r.y = fbm(uv + 4.0 * q + vec2(8.3, 2.8) - t * 0.5);

    // Final noise field calculated from the heavily warped coordinates
    float f = fbm(uv + 4.0 * r);

    // 3. COLOR MAPPING (The Arcane Tech Palette)
    vec3 colorBase = vec3(0.05, 0.08, 0.12);  // Dark Slate background
    vec3 colorMid  = vec3(0.00, 0.80, 0.40);  // Glowing Emerald Green
    vec3 colorHigh = vec3(0.00, 0.95, 0.95);  // Arcane Cyan
    
    // Blend from the slate background into the emerald based on the raw noise structure
    vec3 col = mix(colorBase, colorMid, smoothstep(0.0, 1.0, f * 1.5));
    
    // Layer the arcane cyan over the areas with the highest domain distortion (q and r)
    col = mix(col, colorHigh, smoothstep(0.2, 1.0, length(q)));
    
    // 4. GLASSMORPHIC & GLOW EFFECTS
    // Create sharp glowing filament lines where the 'r' vector crosses certain thresholds
    float filamentGlow = exp(-6.0 * abs(r.y - r.x));
    col += colorHigh * filamentGlow * 0.8;
    
    // Add a specular "glassy" highlight across the fluid ridges
    float spec = pow(max(f, 0.0), 3.0);
    col += vec3(0.6, 1.0, 0.9) * spec * 0.4;
    
    // Soft vignette to focus the energy field in the center of the window
    float vignette = 1.0 - smoothstep(0.5, 2.0, length(uv));
    col *= vignette;
    
    // Ambient edge glow to prevent the borders from going entirely pitch black
    col += colorMid * (1.0 - vignette) * 0.15;

    // Apply slight gamma correction for crisp, vibrant contrast
    col = pow(clamp(col, 0.0, 1.0), vec3(0.85));
    
    fragColor = vec4(col, 1.0);
}
'''

# ============================================================================
# APPLICATION LOGIC
# ============================================================================

def main():
    # 1. INITIALIZE PYGAME & OPENGL SETTINGS
    pygame.init()
    
    # Request an OpenGL 3.3 Core Profile context (Required for ModernGL)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
    
    # Enable hardware acceleration and double buffering
    window_size = (800, 600)
    screen = pygame.display.set_mode(window_size, pygame.OPENGL | pygame.DOUBLEBUF)
    pygame.display.set_caption("Arcane Energy Plasma - ModernGL")

    # 2. INITIALIZE MODERNGL CONTEXT
    ctx = moderngl.create_context()
    
    # Compile the shader program
    try:
        prog = ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=FRAGMENT_SHADER)
    except Exception as e:
        print(f"Shader Compilation Error:\n{e}")
        pygame.quit()
        sys.exit(1)

    # 3. SET UP GEOMETRY (Full-screen Quad)
    # 2D Coordinates for two triangles forming a rectangle covering [-1, 1] space
    quad_vertices = array.array('f', [
        -1.0, -1.0,  # Bottom-Left
         1.0, -1.0,  # Bottom-Right
        -1.0,  1.0,  # Top-Left
         1.0,  1.0   # Top-Right
    ])
    
    # Load geometry into a Vertex Buffer Object (VBO)
    vbo = ctx.buffer(quad_vertices.tobytes())
    
    # Link VBO to the Vertex Array Object (VAO) to map variables to the vertex shader
    vao = ctx.vertex_array(prog, [(vbo, '2f', 'in_position')])

    # 4. MAP UNIFORMS
    # Gracefully fetch uniforms. ModernGL omits unused uniforms during compilation.
    u_time = prog.get('u_time', None)
    u_resolution = prog.get('u_resolution', None)

    if u_resolution:
        u_resolution.value = window_size

    clock = pygame.time.Clock()

    # 5. MAIN RENDER LOOP
    running = True
    while running:
        # Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        # Update Time Uniform
        if u_time:
            # Convert milliseconds to seconds
            u_time.value = pygame.time.get_ticks() / 1000.0

        # Render Phase
        # We render a Triangle Strip to form the full-screen quad from the 4 vertices
        vao.render(moderngl.TRIANGLE_STRIP)

        # Swap buffers to display the rendered frame
        pygame.display.flip()
        
        # Cap framerate to 60 FPS
        clock.tick(60)

    # Cleanup
    vbo.release()
    vao.release()
    prog.release()
    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()