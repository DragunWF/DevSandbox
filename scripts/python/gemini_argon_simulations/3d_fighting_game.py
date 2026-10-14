import sys
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Type

import numpy as np
import pygame
import moderngl


# =============================================================================
# GLSL SHADERS (EMBEDDED #version 330 core)
# =============================================================================

ARENA_VERT_SHADER = """
#version 330 core

layout(location = 0) in vec3 in_position;
layout(location = 1) in vec3 in_normal;
layout(location = 2) in vec2 in_uv;

uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_proj;

out vec3 v_world_pos;
out vec3 v_normal;
out vec2 v_uv;

void main() {
    vec4 world_pos = u_model * vec4(in_position, 1.0);
    v_world_pos = world_pos.xyz;
    v_normal = normalize(mat3(u_model) * in_normal);
    v_uv = in_uv;
    gl_Position = u_proj * u_view * world_pos;
}
"""

ARENA_FRAG_SHADER = """
#version 330 core

in vec3 v_world_pos;
in vec3 v_normal;
in vec2 v_uv;

uniform float u_time;
uniform vec3 u_camera_pos;
uniform vec3 u_player_pos;
uniform vec3 u_ai_pos;
uniform float u_is_pillar;

out vec4 frag_color;

mat2 rot2D(float a) {
    float s = sin(a);
    float c = cos(a);
    return mat2(c, -s, s, c);
}

// 2D Signed Distance Field primitives for Arcane Architecture
float sdBox2D(vec2 p, vec2 b) {
    vec2 d = abs(p) - b;
    return length(max(d, vec2(0.0))) + min(max(d.x, d.y), 0.0);
}

float sdOctagram(vec2 p, float r) {
    vec2 p1 = p;
    vec2 p2 = rot2D(0.78539816) * p;
    float box1 = abs(sdBox2D(p1, vec2(r))) - 0.035;
    float box2 = abs(sdBox2D(p2, vec2(r))) - 0.035;
    return min(box1, box2);
}

float sdHexagon(vec2 p, float r) {
    const vec3 k = vec3(-0.866025404, 0.5, 0.577350269);
    p = abs(p);
    p -= 2.0 * min(dot(k.xy, p), 0.0) * k.xy;
    p -= vec2(clamp(p.x, -k.z * r, k.z * r), r);
    return length(p) * sign(p.y);
}

void main() {
    vec3 N = normalize(v_normal);
    vec3 V = normalize(u_camera_pos - v_world_pos);
    vec3 L = normalize(vec3(0.35, 0.85, 0.25));

    // Base dark slate monolithic stone material
    vec3 slate_dark = vec3(0.035, 0.045, 0.062);
    vec3 slate_mid = vec3(0.065, 0.082, 0.110);
    vec3 emerald = vec3(0.05, 0.96, 0.55);
    vec3 cyan = vec3(0.02, 0.88, 1.00);

    float diff = max(dot(N, L), 0.0);
    vec3 H = normalize(L + V);
    float spec = pow(max(dot(N, H), 0.0), 48.0);

    vec3 base_col = mix(slate_dark, slate_mid, diff * 0.65) + vec3(0.08, 0.12, 0.15) * spec;

    if (u_is_pillar > 0.5) {
        // Monolith Pillar SDF vertical runic engravings
        vec2 pillar_uv = vec2(atan(v_world_pos.z, v_world_pos.x) * 6.0, v_world_pos.y * 0.45);
        vec2 cell = fract(pillar_uv) - 0.5;
        float glyph_d = abs(sdBox2D(rot2D(0.785398) * cell, vec2(0.18, 0.18))) - 0.02;
        float channel_d = abs(cell.x) - 0.025;
        float rune_sdf = min(glyph_d, channel_d);

        float height_mask = smoothstep(0.2, 1.5, v_world_pos.y) * (1.0 - smoothstep(6.5, 8.5, v_world_pos.y));
        float pulse = 0.55 + 0.45 * sin(u_time * 2.2 - v_world_pos.y * 0.9);
        float rune_glow = (1.0 - smoothstep(0.0, 0.045, rune_sdf)) * height_mask * pulse;

        vec3 pillar_magic = mix(emerald, cyan, 0.5 + 0.5 * sin(v_world_pos.y * 0.4 + u_time));
        float rim = pow(1.0 - max(dot(N, V), 0.0), 3.0);
        vec3 col = base_col + pillar_magic * rune_glow * 1.4 + cyan * rim * 0.18;
        frag_color = vec4(col, 1.0);
    } else {
        // Arena Floor: High-precision 2D SDF Arcane Circle & Sacred Geometry
        vec2 p = v_world_pos.xz;
        float r = length(p);
        float angle = atan(p.y, p.x);

        // Concentric SDF rings
        float ring_outer = abs(r - 13.5) - 0.08;
        float ring_inner = abs(r - 11.8) - 0.05;
        float ring_center = abs(r - 4.2) - 0.04;
        float ring_core = abs(r - 1.4) - 0.03;

        // Rotating SDF Octagrams
        vec2 p_rot1 = rot2D(u_time * 0.12) * p;
        vec2 p_rot2 = rot2D(-u_time * 0.18) * p;
        float oct_large = sdOctagram(p_rot1, 8.3);
        float oct_small = sdOctagram(p_rot2, 2.9);

        // Radial Arcane Glyph Ticks between r = 11.8 and r = 13.5
        float num_ticks = 36.0;
        float tick_angle = fract((angle + u_time * 0.05) * num_ticks / 6.2831853) - 0.5;
        float tick_sdf = max(abs(tick_angle) - 0.08, abs(r - 12.65) - 0.55);

        // Background Hexagonal Leyline Tessellation
        vec2 hex_p = p * 0.65;
        vec2 hex_grid = fract(hex_p) - 0.5;
        float hex_sdf = abs(sdHexagon(hex_grid, 0.36)) - 0.012;

        float primary_sdf = min(min(ring_outer, ring_inner), min(oct_large, oct_small));
        primary_sdf = min(primary_sdf, min(ring_center, ring_core));
        primary_sdf = min(primary_sdf, tick_sdf);

        // Crisp SDF line rendering + exponential bloom halo
        float line_sharp = 1.0 - smoothstep(0.0, 0.055, primary_sdf);
        float line_halo = exp(-3.2 * max(primary_sdf, 0.0));
        float hex_line = (1.0 - smoothstep(0.0, 0.035, hex_sdf)) * 0.22;

        // Combatant proximity leyline excitation
        float d_player = length(p - u_player_pos.xz);
        float d_ai = length(p - u_ai_pos.xz);
        float player_aura = exp(-0.45 * d_player);
        float ai_aura = exp(-0.45 * d_ai);

        vec3 arcane_tint = mix(emerald, cyan, 0.5 + 0.5 * sin(r * 0.45 - u_time * 1.8));
        arcane_tint = mix(arcane_tint, emerald * 1.3, player_aura);
        arcane_tint = mix(arcane_tint, cyan * 1.3, ai_aura);

        float edge_fade = 1.0 - smoothstep(13.8, 15.2, r);
        vec3 rune_emission = arcane_tint * (line_sharp * 1.35 + line_halo * 0.42 + hex_line * (0.4 + player_aura + ai_aura));

        // Subtle procedural stone micro-grain
        float grain = fract(sin(dot(floor(p * 12.0), vec2(12.9898, 78.233))) * 43758.5453);
        vec3 col = (base_col * (0.92 + 0.08 * grain) + rune_emission) * edge_fade;

        frag_color = vec4(col, 1.0);
    }
}
"""

WIZARD_VERT_SHADER = """
#version 330 core

layout(location = 0) in vec3 in_position;
layout(location = 1) in vec3 in_normal;
layout(location = 2) in vec2 in_uv;

uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_proj;
uniform float u_time;

out vec3 v_world_pos;
out vec3 v_local_pos;
out vec3 v_normal;
out vec2 v_uv;

void main() {
    vec3 pos = in_position;
    // Hovering harmonic oscillation for upper crystal crown and halo
    float hover_mask = step(1.45, pos.y);
    pos.y += hover_mask * sin(u_time * 3.8 + pos.x * 2.0) * 0.06;

    vec4 world_pos = u_model * vec4(pos, 1.0);
    v_world_pos = world_pos.xyz;
    v_local_pos = pos;
    v_normal = normalize(mat3(u_model) * in_normal);
    v_uv = in_uv;
    gl_Position = u_proj * u_view * world_pos;
}
"""

WIZARD_FRAG_SHADER = """
#version 330 core

in vec3 v_world_pos;
in vec3 v_local_pos;
in vec3 v_normal;
in vec2 v_uv;

uniform float u_time;
uniform vec3 u_camera_pos;
uniform vec3 u_base_color;
uniform vec3 u_accent_color;
uniform float u_cast_intensity;

out vec4 frag_color;

void main() {
    vec3 N = normalize(v_normal);
    vec3 V = normalize(u_camera_pos - v_world_pos);
    vec3 L = normalize(vec3(0.4, 0.9, 0.3));

    float diff = max(dot(N, L), 0.0);
    vec3 H = normalize(L + V);
    float spec = pow(max(dot(N, H), 0.0), 64.0);
    float fresnel = pow(1.0 - max(dot(N, V), 0.0), 2.6);

    // SDF geometric circuit bands etched across the combatant construct
    float band1 = abs(fract(v_local_pos.y * 2.5 - u_time * 0.6) - 0.5) - 0.06;
    float band2 = abs(sin(atan(v_local_pos.z, v_local_pos.x) * 4.0 + v_local_pos.y * 3.0)) - 0.12;
    float rune_mask = 1.0 - smoothstep(0.0, 0.04, max(band1, band2));

    float crown_glow = smoothstep(1.3, 1.9, v_local_pos.y);

    vec3 chassis = u_base_color * (0.25 + 0.75 * diff) + vec3(0.5) * spec;
    vec3 arcane_glow = u_accent_color * (
        rune_mask * (1.2 + u_cast_intensity * 1.8) +
        fresnel * (0.85 + u_cast_intensity * 1.2) +
        crown_glow * 0.65
    );

    frag_color = vec4(chassis + arcane_glow, 1.0);
}
"""

# -----------------------------------------------------------------------------
# 3D VOLUMETRIC SDF RAYMARCHING SHADER FOR ARCANE PROJECTILES
# -----------------------------------------------------------------------------
PROJECTILE_VERT_SHADER = """
#version 330 core

layout(location = 0) in vec3 in_position;

uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_proj;

out vec3 v_world_pos;
out vec3 v_local_pos;

void main() {
    vec4 world_pos = u_model * vec4(in_position, 1.0);
    v_world_pos = world_pos.xyz;
    v_local_pos = in_position;
    gl_Position = u_proj * u_view * world_pos;
}
"""

PROJECTILE_FRAG_SHADER = """
#version 330 core

in vec3 v_world_pos;
in vec3 v_local_pos;

uniform float u_time;
uniform vec3 u_camera_pos;
uniform vec3 u_proj_center;
uniform float u_proj_radius;
uniform vec3 u_primary_color;
uniform vec3 u_secondary_color;

out vec4 frag_color;

mat2 rot2D(float a) {
    float s = sin(a);
    float c = cos(a);
    return mat2(c, -s, s, c);
}

// Exact 3D Octahedron Signed Distance Field (Inigo Quilez formulation)
float sdOctahedron(vec3 p, float s) {
    p = abs(p);
    float m = p.x + p.y + p.z - s;
    vec3 q;
    if (3.0 * p.x < m) {
        q = p.xyz;
    } else if (3.0 * p.y < m) {
        q = p.yzx;
    } else if (3.0 * p.z < m) {
        q = p.zxy;
    } else {
        return m * 0.57735027;
    }
    float k = clamp(0.5 * (q.z - q.y + s), 0.0, s);
    return length(vec3(q.x, q.y - s + k, q.z - k));
}

// 3D Torus Signed Distance Field for Orbiting Runic Halo Rings
float sdTorus(vec3 p, vec2 t) {
    vec2 q = vec2(length(p.xz) - t.x, p.y);
    return length(q) - t.y;
}

// Smooth Minimum for organic arcane construct fusion
float smin(float a, float b, float k) {
    float h = clamp(0.5 + 0.5 * (b - a) / k, 0.0, 1.0);
    return mix(b, a, h) - k * h * (1.0 - h);
}

// Composite 3D Arcane Construct SDF
float mapProjectileSDF(vec3 p, float time_val) {
    vec3 p1 = p;
    p1.xz = rot2D(time_val * 4.5) * p1.xz;
    p1.xy = rot2D(time_val * 3.1) * p1.xy;
    float core_oct = sdOctahedron(p1, 0.46);

    vec3 p2 = p;
    p2.yz = rot2D(time_val * 5.2) * p2.yz;
    p2.xz = rot2D(-time_val * 3.7) * p2.xz;
    float ring1 = sdTorus(p2, vec2(0.66, 0.045));

    vec3 p3 = p;
    p3.xy = rot2D(-time_val * 6.0) * p3.xy;
    float ring2 = sdTorus(p3.xzy, vec2(0.54, 0.038));

    float rings = min(ring1, ring2);
    return smin(core_oct, rings, 0.08);
}

vec3 calcSDFNormal(vec3 p, float time_val) {
    vec2 e = vec2(0.004, -0.004);
    return normalize(
        e.xyy * mapProjectileSDF(p + e.xyy, time_val) +
        e.yyx * mapProjectileSDF(p + e.yyx, time_val) +
        e.yxy * mapProjectileSDF(p + e.yxy, time_val) +
        e.xxx * mapProjectileSDF(p + e.xxx, time_val)
    );
}

void main() {
    // Raymarch in normalized local projectile space
    vec3 ro = (u_camera_pos - u_proj_center) / u_proj_radius;
    vec3 rd = normalize(v_world_pos - u_camera_pos);

    // Intersect bounding sphere of radius 1.15 in normalized space
    float b = dot(ro, rd);
    float c = dot(ro, ro) - 1.32;
    float disc = b * b - c;
    if (disc < 0.0) {
        discard;
    }

    float sqrt_disc = sqrt(max(disc, 0.0));
    float t_start = max(0.0, -b - sqrt_disc);
    float t_end = -b + sqrt_disc;

    float t = t_start;
    float accum_glow = 0.0;
    float hit_surface = 0.0;
    vec3 hit_pos = vec3(0.0);

    for (int i = 0; i < 28; ++i) {
        if (t > t_end) {
            break;
        }
        vec3 p = ro + rd * t;
        float d = mapProjectileSDF(p, u_time);

        // Volumetric Beer-Lambert / inverse-distance glow accumulation
        accum_glow += exp(-9.5 * max(d, 0.0)) * 0.065;

        if (d < 0.008) {
            hit_surface = 1.0;
            hit_pos = p;
            break;
        }
        t += max(d * 0.75, 0.022);
    }

    vec3 col = mix(u_primary_color, u_secondary_color, clamp(accum_glow * 0.8, 0.0, 1.0)) * accum_glow * 2.1;

    if (hit_surface > 0.5) {
        vec3 N = calcSDFNormal(hit_pos, u_time);
        float fres = pow(1.0 - max(dot(N, -rd), 0.0), 2.0);
        vec3 core_col = mix(vec3(0.88, 1.0, 0.96), u_secondary_color, fres);
        col += core_col * 1.45;
    }

    float alpha = clamp(accum_glow * 1.6 + hit_surface, 0.0, 1.0);
    if (alpha < 0.03) {
        discard;
    }

    frag_color = vec4(col, alpha);
}
"""

# -----------------------------------------------------------------------------
# SCREEN-SPACE REFRACTIVE & CHROMATIC DISPERSION BARRIER SHADER
# -----------------------------------------------------------------------------
BARRIER_VERT_SHADER = """
#version 330 core

layout(location = 0) in vec3 in_position;
layout(location = 1) in vec3 in_normal;

uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_proj;
uniform float u_time;
uniform float u_hit_flash;

out vec3 v_world_pos;
out vec3 v_local_pos;
out vec3 v_normal;
out vec3 v_view_normal;
out vec4 v_clip_pos;

void main() {
    // Harmonic crystalline ripple along vertex normal
    float ripple = sin(in_position.y * 8.0 + u_time * 5.0) * cos(in_position.x * 8.0 - u_time * 4.0);
    vec3 displaced = in_position + in_normal * (ripple * (0.018 + u_hit_flash * 0.06));

    vec4 world_pos = u_model * vec4(displaced, 1.0);
    v_world_pos = world_pos.xyz;
    v_local_pos = in_position;
    v_normal = normalize(mat3(u_model) * in_normal);
    v_view_normal = normalize(mat3(u_view) * v_normal);
    v_clip_pos = u_proj * u_view * world_pos;
    gl_Position = v_clip_pos;
}
"""

BARRIER_FRAG_SHADER = """
#version 330 core

in vec3 v_world_pos;
in vec3 v_local_pos;
in vec3 v_normal;
in vec3 v_view_normal;
in vec4 v_clip_pos;

uniform sampler2D u_scene_color;
uniform sampler2D u_scene_depth;
uniform vec2 u_resolution;
uniform float u_time;
uniform vec3 u_camera_pos;
uniform vec3 u_barrier_color;
uniform vec3 u_secondary_color;
uniform float u_hit_flash;

out vec4 frag_color;

float sdHexagon2D(vec2 p, float r) {
    const vec3 k = vec3(-0.866025404, 0.5, 0.577350269);
    p = abs(p);
    p -= 2.0 * min(dot(k.xy, p), 0.0) * k.xy;
    p -= vec2(clamp(p.x, -k.z * r, k.z * r), r);
    return length(p) * sign(p.y);
}

float linearizeDepth(float d, float z_near, float z_far) {
    float z_ndc = d * 2.0 - 1.0;
    return (2.0 * z_near * z_far) / (z_far + z_near - z_ndc * (z_far - z_near));
}

void main() {
    vec2 screen_uv = gl_FragCoord.xy / u_resolution;

    // Depth occlusion & ground-intersection energy ring
    float scene_d = texture(u_scene_depth, screen_uv).r;
    float frag_d = gl_FragCoord.z;

    // Discard pixels behind solid scene geometry
    if (frag_d >= scene_d) {
        discard;
    }

    float lin_scene = linearizeDepth(scene_d, 0.5, 85.0);
    float lin_frag = linearizeDepth(frag_d, 0.5, 85.0);
    float depth_diff = max(0.0, lin_scene - lin_frag);
    float intersection_glow = exp(-3.5 * depth_diff);

    vec3 N = normalize(v_normal);
    vec3 V = normalize(u_camera_pos - v_world_pos);

    // Spherical UV mapping for SDF Hexagonal Arcane Ward Lattice
    vec2 sphere_uv = vec2(atan(v_local_pos.z, v_local_pos.x) * 3.8, v_local_pos.y * 4.5);
    vec2 hex_cell = fract(sphere_uv) - 0.5;
    float hex_d = abs(sdHexagon2D(hex_cell, 0.38)) - 0.035;
    float hex_edge = 1.0 - smoothstep(0.0, 0.05, hex_d);

    // High-frequency refractive wave perturbation
    vec2 wave = vec2(
        sin(v_local_pos.y * 12.0 + u_time * 4.2) + cos(v_local_pos.x * 10.0 - u_time * 3.5),
        cos(v_local_pos.z * 12.0 - u_time * 4.0) + sin(v_local_pos.y * 9.0 + u_time * 5.0)
    ) * 0.015;

    // Physical Snell's Law View-Space Refraction + Chromatic Aberration
    vec3 view_incident = vec3(0.0, 0.0, -1.0);
    vec3 perturbed_vn = normalize(v_view_normal + vec3(wave + hex_cell * hex_edge * 0.12, 0.0));
    vec3 refr_vec = refract(view_incident, perturbed_vn, 1.0 / 1.48);

    float distort_strength = 0.065 + u_hit_flash * 0.085;
    vec2 refr_offset = refr_vec.xy * distort_strength + wave * (0.4 + u_hit_flash);

    // Chromatic Dispersion (RGB spectral split across the crystalline barrier)
    vec2 uv_r = clamp(screen_uv + refr_offset * 1.18, vec2(0.002), vec2(0.998));
    vec2 uv_g = clamp(screen_uv + refr_offset * 1.00, vec2(0.002), vec2(0.998));
    vec2 uv_b = clamp(screen_uv + refr_offset * 0.82, vec2(0.002), vec2(0.998));

    vec3 refracted_bg = vec3(
        texture(u_scene_color, uv_r).r,
        texture(u_scene_color, uv_g).g,
        texture(u_scene_color, uv_b).b
    );

    // Schlick's Fresnel Approximation for glass-like arcane reflection
    float cos_theta = abs(dot(N, V));
    float r0 = 0.08;
    float fresnel = r0 + (1.0 - r0) * pow(1.0 - cos_theta, 3.2);

    // Equatorial scanning rune band
    float scan_band = exp(-12.0 * abs(v_local_pos.y - sin(u_time * 2.4) * 0.75));

    vec3 ward_tint = mix(u_barrier_color, u_secondary_color, fresnel);
    vec3 surface_energy = ward_tint * (
        fresnel * 1.55 +
        hex_edge * (0.55 + u_hit_flash * 1.4) +
        intersection_glow * 1.75 +
        scan_band * 0.45 +
        u_hit_flash * 0.9
    );

    // Combine distorted glass refraction with glowing arcane geometric lattice
    vec3 final_col = refracted_bg * mix(vec3(0.92, 0.98, 1.0), ward_tint, 0.22) + surface_energy;
    frag_color = vec4(final_col, 1.0);
}
"""

# -----------------------------------------------------------------------------
# SCREEN COMPOSITE & DIEGETIC SDF HUD SHADER
# -----------------------------------------------------------------------------
COMPOSITE_VERT_SHADER = """
#version 330 core

layout(location = 0) in vec2 in_pos;
layout(location = 1) in vec2 in_uv;

out vec2 v_uv;

void main() {
    v_uv = in_uv;
    gl_Position = vec4(in_pos, 0.0, 1.0);
}
"""

COMPOSITE_FRAG_SHADER = """
#version 330 core

in vec2 v_uv;

uniform sampler2D u_scene_color;
uniform vec2 u_resolution;
uniform float u_player_hp;
uniform float u_player_mana;
uniform float u_player_barrier_ready;
uniform float u_ai_hp;
uniform float u_time;

out vec4 frag_color;

float sdBox2D(vec2 p, vec2 b) {
    vec2 d = abs(p) - b;
    return length(max(d, vec2(0.0))) + min(max(d.x, d.y), 0.0);
}

// ACES Filmic Tone Mapping
vec3 acesToneMap(vec3 x) {
    const float a = 2.51;
    const float b = 0.03;
    const float c = 2.43;
    const float d = 0.59;
    const float e = 0.14;
    return clamp((x * (a * x + b)) / (x * (c * x + d) + e), 0.0, 1.0);
}

void main() {
    vec3 hdr_col = texture(u_scene_color, v_uv).rgb;

    // Subtle radial vignette
    vec2 centered = v_uv - 0.5;
    float vig = 1.0 - dot(centered, centered) * 0.55;
    vec3 col = acesToneMap(hdr_col * vig);
    col = pow(col, vec3(1.0 / 2.1));

    // Diegetic SDF Arcane HUD Bars (Bottom-Left: Player, Top-Right: Opponent)
    vec2 aspect_uv = vec2(v_uv.x * (u_resolution.x / u_resolution.y), v_uv.y);
    float ar = u_resolution.x / u_resolution.y;

    // Player HP Bar (Emerald)
    vec2 p_hp_center = vec2(0.24, 0.075);
    vec2 p_hp_half = vec2(0.18, 0.013);
    float d_p_hp_frame = abs(sdBox2D(aspect_uv - p_hp_center, p_hp_half)) - 0.002;
    float p_hp_fill_mask = step(sdBox2D(aspect_uv - p_hp_center, p_hp_half - vec2(0.004)), 0.0) *
                           step(aspect_uv.x, (p_hp_center.x - p_hp_half.x) + 2.0 * p_hp_half.x * u_player_hp);

    // Player Mana Bar (Cyan)
    vec2 p_mp_center = vec2(0.24, 0.042);
    vec2 p_mp_half = vec2(0.18, 0.009);
    float d_p_mp_frame = abs(sdBox2D(aspect_uv - p_mp_center, p_mp_half)) - 0.0018;
    float p_mp_fill_mask = step(sdBox2D(aspect_uv - p_mp_center, p_mp_half - vec2(0.003)), 0.0) *
                           step(aspect_uv.x, (p_mp_center.x - p_mp_half.x) + 2.0 * p_mp_half.x * u_player_mana);

    // Player Barrier Ward Readiness Diamond (Left of bars)
    vec2 ward_center = vec2(0.035, 0.058);
    vec2 dp = abs(aspect_uv - ward_center);
    float d_diamond = (dp.x + dp.y) - 0.018;
    float diamond_fill = (1.0 - smoothstep(-0.002, 0.002, d_diamond)) * u_player_barrier_ready;
    float diamond_outline = 1.0 - smoothstep(0.0, 0.003, abs(d_diamond) - 0.0015);

    // AI Opponent HP Bar (Top-Right, Cyan-Violet)
    vec2 ai_hp_center = vec2(ar - 0.24, 0.935);
    vec2 ai_hp_half = vec2(0.18, 0.013);
    float d_ai_frame = abs(sdBox2D(aspect_uv - ai_hp_center, ai_hp_half)) - 0.002;
    float ai_fill_mask = step(sdBox2D(aspect_uv - ai_hp_center, ai_hp_half - vec2(0.004)), 0.0) *
                         step((ai_hp_center.x + ai_hp_half.x) - 2.0 * ai_hp_half.x * u_ai_hp, aspect_uv.x);

    float frame_lines = (1.0 - smoothstep(0.0, 0.0025, min(min(d_p_hp_frame, d_p_mp_frame), d_ai_frame))) + diamond_outline;

    vec3 emerald = vec3(0.05, 0.96, 0.55);
    vec3 cyan = vec3(0.05, 0.88, 1.00);
    vec3 archon_teal = vec3(0.15, 0.72, 0.98);

    col = mix(col, emerald * (0.85 + 0.15 * sin(u_time * 4.0)), p_hp_fill_mask * 0.9);
    col = mix(col, cyan * 0.9, p_mp_fill_mask * 0.9);
    col = mix(col, cyan * 1.2, diamond_fill * 0.95);
    col = mix(col, archon_teal, ai_fill_mask * 0.9);
    col += vec3(0.45, 0.85, 0.75) * clamp(frame_lines, 0.0, 1.0) * 0.7;

    frag_color = vec4(col, 1.0);
}
"""


# =============================================================================
# NUMPY 3D MATRIX & RAYCASTING MATHEMATICS
# =============================================================================

class Math3D:
    @staticmethod
    def normalize(v: np.ndarray) -> np.ndarray:
        norm = max(1e-7, float(np.linalg.norm(v)))
        return v / norm

    @staticmethod
    def perspective(fov_deg: float, aspect: float, z_near: float, z_far: float) -> np.ndarray:
        f = 1.0 / math.tan(math.radians(fov_deg) * 0.5)
        mat = np.zeros((4, 4), dtype=np.float32)
        mat[0, 0] = f / max(0.001, aspect)
        mat[1, 1] = f
        mat[2, 2] = (z_far + z_near) / (z_near - z_far)
        mat[2, 3] = (2.0 * z_far * z_near) / (z_near - z_far)
        mat[3, 2] = -1.0
        return mat

    @staticmethod
    def look_at(eye: np.ndarray, target: np.ndarray, up: np.ndarray) -> np.ndarray:
        f = Math3D.normalize(target - eye)
        s = Math3D.normalize(np.cross(f, up))
        u = np.cross(s, f)

        mat = np.identity(4, dtype=np.float32)
        mat[0, 0:3] = s
        mat[1, 0:3] = u
        mat[2, 0:3] = -f
        mat[0, 3] = -float(np.dot(s, eye))
        mat[1, 3] = -float(np.dot(u, eye))
        mat[2, 3] = float(np.dot(f, eye))
        return mat

    @staticmethod
    def compose_model_matrix(position: np.ndarray, rot_y: float, scale: np.ndarray) -> np.ndarray:
        c = math.cos(rot_y)
        s = math.sin(rot_y)
        sx, sy, sz = float(scale[0]), float(scale[1]), float(scale[2])

        mat = np.identity(4, dtype=np.float32)
        mat[0, 0] = c * sx
        mat[0, 2] = s * sz
        mat[1, 1] = sy
        mat[2, 0] = -s * sx
        mat[2, 2] = c * sz
        mat[0, 3] = float(position[0])
        mat[1, 3] = float(position[1])
        mat[2, 3] = float(position[2])
        return mat

    @staticmethod
    def gl_bytes(mat: np.ndarray) -> bytes:
        # Transpose mathematical row-major matrix to OpenGL column-major memory layout
        return np.ascontiguousarray(mat.T, dtype=np.float32).tobytes()

    @staticmethod
    def raycast_ground_plane(
        mouse_x: float,
        mouse_y: float,
        screen_w: float,
        screen_h: float,
        view_mat: np.ndarray,
        proj_mat: np.ndarray
    ) -> np.ndarray:
        ndc_x = (2.0 * mouse_x) / max(1.0, screen_w) - 1.0
        ndc_y = 1.0 - (2.0 * mouse_y) / max(1.0, screen_h)

        vp = proj_mat @ view_mat
        inv_vp = np.linalg.inv(vp)

        near_clip = np.array([ndc_x, ndc_y, -1.0, 1.0], dtype=np.float32)
        far_clip = np.array([ndc_x, ndc_y, 1.0, 1.0], dtype=np.float32)

        near_world = inv_vp @ near_clip
        far_world = inv_vp @ far_clip
        near_world = near_world[:3] / max(1e-6, abs(float(near_world[3]))) * np.sign(float(near_world[3]))
        far_world = far_world[:3] / max(1e-6, abs(float(far_world[3]))) * np.sign(float(far_world[3]))

        ray_dir = Math3D.normalize(far_world - near_world)
        denom = float(ray_dir[1])
        if abs(denom) < 1e-5:
            return np.array([0.0, 0.0, 0.0], dtype=np.float32)

        t = -float(near_world[1]) / denom
        t = max(0.0, min(t, 120.0))
        return near_world + ray_dir * t


# =============================================================================
# PROCEDURAL 3D MESH FACTORY (VECTORIZED NUMPY)
# =============================================================================

class MeshFactory:
    @staticmethod
    def _build_frustum_section(
        r_bottom: float,
        r_top: float,
        y_bottom: float,
        y_top: float,
        sides: int,
        twist: float = 0.0
    ) -> np.ndarray:
        angles = np.linspace(0.0, 2.0 * np.pi, sides + 1, dtype=np.float32)
        verts: List[List[float]] = []

        slope_y = r_bottom - r_top
        height = max(1e-4, y_top - y_bottom)

        for i in range(sides):
            a0, a1 = float(angles[i]), float(angles[i + 1])
            b0, b1 = a0 + twist, a1 + twist

            p00 = [r_bottom * math.cos(a0), y_bottom, r_bottom * math.sin(a0)]
            p10 = [r_bottom * math.cos(a1), y_bottom, r_bottom * math.sin(a1)]
            p11 = [r_top * math.cos(b1), y_top, r_top * math.sin(b1)]
            p01 = [r_top * math.cos(b0), y_top, r_top * math.sin(b0)]

            mid_a = 0.5 * (a0 + a1)
            nx = math.cos(mid_a) * height
            nz = math.sin(mid_a) * height
            ny = slope_y
            n_len = max(1e-6, math.sqrt(nx * nx + ny * ny + nz * nz))
            n = [nx / n_len, ny / n_len, nz / n_len]

            u0, u1 = float(i) / sides, float(i + 1) / sides
            verts.extend([
                p00 + n + [u0, 0.0],
                p11 + n + [u1, 1.0],
                p10 + n + [u1, 0.0],
                p00 + n + [u0, 0.0],
                p01 + n + [u0, 1.0],
                p11 + n + [u1, 1.0],
            ])

            # Top & bottom caps if closed
            if r_top > 0.001:
                up_n = [0.0, 1.0, 0.0]
                verts.extend([
                    [0.0, y_top, 0.0] + up_n + [0.5, 0.5],
                    p01 + up_n + [0.5, 1.0],
                    p11 + up_n + [1.0, 1.0],
                ])
            if r_bottom > 0.001:
                dn_n = [0.0, -1.0, 0.0]
                verts.extend([
                    [0.0, y_bottom, 0.0] + dn_n + [0.5, 0.5],
                    p10 + dn_n + [1.0, 0.0],
                    p00 + dn_n + [0.5, 0.0],
                ])

        return np.array(verts, dtype=np.float32)

    @staticmethod
    def create_arena_floor(radius: float = 15.2, segments: int = 64) -> np.ndarray:
        angles = np.linspace(0.0, 2.0 * np.pi, segments + 1, dtype=np.float32)
        verts: List[List[float]] = []
        up_n = [0.0, 1.0, 0.0]

        for i in range(segments):
            a0, a1 = float(angles[i]), float(angles[i + 1])
            x0, z0 = radius * math.cos(a0), radius * math.sin(a0)
            x1, z1 = radius * math.cos(a1), radius * math.sin(a1)

            verts.extend([
                [0.0, 0.0, 0.0] + up_n + [0.0, 0.0],
                [x1, 0.0, z1] + up_n + [x1 / radius, z1 / radius],
                [x0, 0.0, z0] + up_n + [x0 / radius, z0 / radius],
            ])

        return np.array(verts, dtype=np.float32)

    @staticmethod
    def create_monolith_pillars(num_pillars: int = 8, ring_radius: float = 15.8) -> np.ndarray:
        parts: List[np.ndarray] = []
        base_pillar = np.vstack([
            MeshFactory._build_frustum_section(1.15, 0.82, -1.0, 6.8, sides=6),
            MeshFactory._build_frustum_section(0.82, 0.0, 6.8, 8.4, sides=6),
        ])

        for i in range(num_pillars):
            angle = (2.0 * math.pi * i) / num_pillars + 0.392699
            px = ring_radius * math.cos(angle)
            pz = ring_radius * math.sin(angle)

            instance = base_pillar.copy()
            c, s = math.cos(-angle), math.sin(-angle)
            x = instance[:, 0].copy()
            z = instance[:, 2].copy()
            instance[:, 0] = c * x - s * z + px
            instance[:, 2] = s * x + c * z + pz

            nx = instance[:, 3].copy()
            nz = instance[:, 5].copy()
            instance[:, 3] = c * nx - s * nz
            instance[:, 5] = s * nx + c * nz
            parts.append(instance)

        return np.vstack(parts).astype(np.float32)

    @staticmethod
    def create_wizard_construct() -> np.ndarray:
        # Composite high-fantasy crystalline archon silhouette
        lower_robe = MeshFactory._build_frustum_section(0.62, 0.28, 0.0, 1.15, sides=8, twist=0.2)
        upper_torso = MeshFactory._build_frustum_section(0.26, 0.44, 1.10, 1.52, sides=6)
        crown_lower = MeshFactory._build_frustum_section(0.0, 0.26, 1.58, 1.82, sides=4, twist=0.4)
        crown_upper = MeshFactory._build_frustum_section(0.26, 0.0, 1.82, 2.12, sides=4, twist=0.4)

        # Floating shoulder shards
        shard_l = MeshFactory._build_frustum_section(0.16, 0.0, 1.25, 1.72, sides=4)
        shard_l[:, 0] += 0.52
        shard_r = MeshFactory._build_frustum_section(0.16, 0.0, 1.25, 1.72, sides=4)
        shard_r[:, 0] -= 0.52

        return np.vstack([
            lower_robe,
            upper_torso,
            crown_lower,
            crown_upper,
            shard_l,
            shard_r,
        ]).astype(np.float32)

    @staticmethod
    def create_unit_cube(half_size: float = 1.0) -> np.ndarray:
        s = half_size
        faces = [
            # +Z
            ([-s, -s, s], [s, -s, s], [s, s, s], [-s, s, s], [0.0, 0.0, 1.0]),
            # -Z
            ([s, -s, -s], [-s, -s, -s], [-s, s, -s], [s, s, -s], [0.0, 0.0, -1.0]),
            # +X
            ([s, -s, s], [s, -s, -s], [s, s, -s], [s, s, s], [1.0, 0.0, 0.0]),
            # -X
            ([-s, -s, -s], [-s, -s, s], [-s, s, s], [-s, s, -s], [-1.0, 0.0, 0.0]),
            # +Y
            ([-s, s, s], [s, s, s], [s, s, -s], [-s, s, -s], [0.0, 1.0, 0.0]),
            # -Y
            ([-s, -s, -s], [s, -s, -s], [s, -s, s], [-s, -s, s], [0.0, -1.0, 0.0]),
        ]
        verts: List[List[float]] = []
        for p0, p1, p2, p3, n in faces:
            verts.extend([
                p0 + n + [0.0, 0.0],
                p1 + n + [1.0, 0.0],
                p2 + n + [1.0, 1.0],
                p0 + n + [0.0, 0.0],
                p2 + n + [1.0, 1.0],
                p3 + n + [0.0, 1.0],
            ])
        return np.array(verts, dtype=np.float32)

    @staticmethod
    def create_uv_sphere(rings: int = 28, sectors: int = 40) -> np.ndarray:
        verts: List[List[float]] = []
        for r in range(rings):
            phi0 = math.pi * (float(r) / rings - 0.5)
            phi1 = math.pi * (float(r + 1) / rings - 0.5)
            y0, r0 = math.sin(phi0), math.cos(phi0)
            y1, r1 = math.sin(phi1), math.cos(phi1)

            for s in range(sectors):
                th0 = 2.0 * math.pi * (float(s) / sectors)
                th1 = 2.0 * math.pi * (float(s + 1) / sectors)

                p00 = [r0 * math.cos(th0), y0, r0 * math.sin(th0)]
                p10 = [r0 * math.cos(th1), y0, r0 * math.sin(th1)]
                p11 = [r1 * math.cos(th1), y1, r1 * math.sin(th1)]
                p01 = [r1 * math.cos(th0), y1, r1 * math.sin(th0)]

                u0, u1 = float(s) / sectors, float(s + 1) / sectors
                v0, v1 = float(r) / rings, float(r + 1) / rings

                verts.extend([
                    p00 + p00 + [u0, v0],
                    p11 + p11 + [u1, v1],
                    p10 + p10 + [u1, v0],
                    p00 + p00 + [u0, v0],
                    p01 + p01 + [u0, v1],
                    p11 + p11 + [u1, v1],
                ])
        return np.array(verts, dtype=np.float32)


# =============================================================================
# STRICT ENTITY COMPONENT SYSTEM (ECS)
# =============================================================================

@dataclass
class TransformComponent:
    position: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float32))
    rotation_y: float = 0.0
    scale: np.ndarray = field(default_factory=lambda: np.ones(3, dtype=np.float32))
    model_matrix: np.ndarray = field(default_factory=lambda: np.identity(4, dtype=np.float32))


@dataclass
class VelocityComponent:
    linear: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float32))
    damping: float = 9.0
    max_speed: float = 7.5
    constrain_to_arena: bool = True


@dataclass
class CombatStateComponent:
    team: int = 0
    hp: float = 100.0
    max_hp: float = 100.0
    mana: float = 100.0
    max_mana: float = 100.0
    mana_regen: float = 18.0
    state: str = "IDLE"
    cast_anim_timer: float = 0.0
    proj_cooldown: float = 0.0
    barrier_cooldown: float = 0.0
    active_barrier_entity: Optional[int] = None


@dataclass
class SpellCasterComponent:
    wants_cast_projectile: bool = False
    wants_cast_barrier: bool = False
    aim_direction: np.ndarray = field(default_factory=lambda: np.array([0.0, 0.0, 1.0], dtype=np.float32))
    projectile_speed: float = 16.5
    projectile_damage: float = 18.0
    projectile_mana_cost: float = 16.0
    projectile_cd_duration: float = 0.42
    barrier_duration: float = 3.2
    barrier_radius: float = 1.65
    barrier_mana_cost: float = 32.0
    barrier_cd_duration: float = 5.0


@dataclass
class ProjectileComponent:
    owner_id: int = -1
    team: int = 0
    damage: float = 18.0
    lifetime: float = 3.2
    age: float = 0.0
    radius: float = 0.58


@dataclass
class BarrierComponent:
    owner_id: int = -1
    team: int = 0
    lifetime: float = 3.2
    age: float = 0.0
    radius: float = 1.65
    hit_flash: float = 0.0


@dataclass
class AIComponent:
    target_entity: int = -1
    strafe_dir: float = 1.0
    decision_timer: float = 0.0
    preferred_range: float = 9.2


@dataclass
class RenderableComponent:
    mesh_key: str = "wizard"
    shader_pass: str = "WIZARD"
    primary_color: np.ndarray = field(default_factory=lambda: np.array([0.05, 0.96, 0.55], dtype=np.float32))
    secondary_color: np.ndarray = field(default_factory=lambda: np.array([0.02, 0.88, 1.00], dtype=np.float32))


class ECSWorld:
    def __init__(self):
        self._next_entity_id: int = 1
        self._entities: Set[int] = set()
        self._components: Dict[Type, Dict[int, object]] = {}
        self._destroy_queue: Set[int] = set()
        self.time: float = 0.0
        self.camera_yaw: float = 0.0
        self.camera_distance: float = 21.5
        self.camera_height: float = 14.5
        self.camera_pos: np.ndarray = np.array([0.0, 14.5, 21.5], dtype=np.float32)
        self.view_matrix: np.ndarray = np.identity(4, dtype=np.float32)
        self.proj_matrix: np.ndarray = np.identity(4, dtype=np.float32)
        self.player_entity: int = -1
        self.ai_entity: int = -1

    def create_entity(self) -> int:
        eid = self._next_entity_id
        self._next_entity_id += 1
        self._entities.add(eid)
        return eid

    def destroy_entity(self, eid: int):
        self._destroy_queue.add(eid)

    def flush_destroyed(self):
        for eid in self._destroy_queue:
            self._entities.discard(eid)
            for comp_table in self._components.values():
                comp_table.pop(eid, None)
        self._destroy_queue.clear()

    def add_component(self, eid: int, component: object):
        comp_type = type(component)
        if comp_type not in self._components:
            self._components[comp_type] = {}
        self._components[comp_type][eid] = component

    def get_component(self, eid: int, comp_type: Type):
        table = self._components.get(comp_type)
        if table is None:
            return None
        return table.get(eid)

    def query(self, *comp_types: Type) -> List[Tuple]:
        if not comp_types:
            return []
        tables = [self._components.get(ct, {}) for ct in comp_types]
        common_ids = set(tables[0].keys())
        for t in tables[1:]:
            common_ids &= set(t.keys())
        common_ids -= self._destroy_queue
        return [(eid, *(t[eid] for t in tables)) for eid in common_ids]


# =============================================================================
# ECS SYSTEMS (INPUT, AI, PHYSICS, COMBAT, RENDERING)
# =============================================================================

class InputSystem:
    def __init__(self):
        self.last_mouse_pos: Tuple[int, int] = (0, 0)

    def update(self, world: ECSWorld, dt: float, window_size: Tuple[int, int]):
        keys = pygame.key.get_pressed()
        mouse_buttons = pygame.mouse.get_pressed(num_buttons=3)
        mx, my = pygame.mouse.get_pos()

        # Camera orbit controls
        if keys[pygame.K_q]:
            world.camera_yaw -= 1.4 * dt
        if keys[pygame.K_e]:
            world.camera_yaw += 1.4 * dt

        player_id = world.player_entity
        transform = world.get_component(player_id, TransformComponent)
        velocity = world.get_component(player_id, VelocityComponent)
        caster = world.get_component(player_id, SpellCasterComponent)
        combat = world.get_component(player_id, CombatStateComponent)

        if not (transform and velocity and caster and combat):
            return
        if combat.hp <= 0.0:
            return

        # Camera-relative movement basis on XZ plane
        cam_fwd = np.array([-math.sin(world.camera_yaw), 0.0, -math.cos(world.camera_yaw)], dtype=np.float32)
        cam_right = np.array([math.cos(world.camera_yaw), 0.0, -math.sin(world.camera_yaw)], dtype=np.float32)

        move_dir = np.zeros(3, dtype=np.float32)
        if keys[pygame.K_w]:
            move_dir += cam_fwd
        if keys[pygame.K_s]:
            move_dir -= cam_fwd
        if keys[pygame.K_d]:
            move_dir += cam_right
        if keys[pygame.K_a]:
            move_dir -= cam_right

        move_len = float(np.linalg.norm(move_dir))
        if move_len > 1e-4:
            move_dir /= move_len
            velocity.linear += move_dir * 48.0 * dt

        # Aiming via 3D Mouse Raycast onto y = 0 Arena Plane + Arrow Key fallback
        if (mx, my) != self.last_mouse_pos:
            self.last_mouse_pos = (mx, my)
            hit_pt = Math3D.raycast_ground_plane(
                float(mx), float(my),
                float(window_size[0]), float(window_size[1]),
                world.view_matrix, world.proj_matrix
            )
            aim_vec = hit_pt - transform.position
            aim_vec[1] = 0.0
            if float(np.linalg.norm(aim_vec)) > 0.05:
                caster.aim_direction = Math3D.normalize(aim_vec)
                transform.rotation_y = math.atan2(float(caster.aim_direction[0]), float(caster.aim_direction[2]))

        if keys[pygame.K_LEFT]:
            transform.rotation_y += 3.2 * dt
            caster.aim_direction = np.array(
                [math.sin(transform.rotation_y), 0.0, math.cos(transform.rotation_y)],
                dtype=np.float32
            )
        if keys[pygame.K_RIGHT]:
            transform.rotation_y -= 3.2 * dt
            caster.aim_direction = np.array(
                [math.sin(transform.rotation_y), 0.0, math.cos(transform.rotation_y)],
                dtype=np.float32
            )

        caster.wants_cast_projectile = bool(mouse_buttons[0] or keys[pygame.K_SPACE])
        caster.wants_cast_barrier = bool(mouse_buttons[2] or keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])


class AISystem:
    def update(self, world: ECSWorld, dt: float):
        for eid, ai, transform, velocity, combat, caster in world.query(
            AIComponent, TransformComponent, VelocityComponent, CombatStateComponent, SpellCasterComponent
        ):
            if combat.hp <= 0.0:
                caster.wants_cast_projectile = False
                caster.wants_cast_barrier = False
                continue

            target_transform = world.get_component(ai.target_entity, TransformComponent)
            target_velocity = world.get_component(ai.target_entity, VelocityComponent)
            target_combat = world.get_component(ai.target_entity, CombatStateComponent)

            if not (target_transform and target_combat) or target_combat.hp <= 0.0:
                caster.wants_cast_projectile = False
                caster.wants_cast_barrier = False
                continue

            to_target = target_transform.position - transform.position
            to_target[1] = 0.0
            dist = max(1e-4, float(np.linalg.norm(to_target)))
            dir_to_target = to_target / dist

            # Predictive leading aim calculation
            lead_pos = target_transform.position.copy()
            if target_velocity is not None:
                travel_time = dist / max(1.0, caster.projectile_speed)
                lead_pos = lead_pos + target_velocity.linear * travel_time * 0.65

            aim_vec = lead_pos - transform.position
            aim_vec[1] = 0.0
            caster.aim_direction = Math3D.normalize(aim_vec)
            transform.rotation_y = math.atan2(float(caster.aim_direction[0]), float(caster.aim_direction[2]))

            # Periodic tactical strafe reversals
            ai.decision_timer = max(0.0, ai.decision_timer - dt)
            if ai.decision_timer <= 0.0:
                ai.decision_timer = 1.1 + 0.9 * abs(math.sin(world.time * 3.7))
                if math.sin(world.time * 7.3) > 0.1:
                    ai.strafe_dir *= -1.0

            # Maintain optimal arcane duel distance while orbiting
            tangent = np.array([-dir_to_target[2] * ai.strafe_dir, 0.0, dir_to_target[0] * ai.strafe_dir], dtype=np.float32)
            radial_err = dist - ai.preferred_range
            radial_push = np.clip(radial_err * 0.45, -1.0, 1.0)
            move_intent = Math3D.normalize(tangent + dir_to_target * radial_push)
            velocity.linear += move_intent * 40.0 * dt

            # Threat Detection: Check incoming hostile projectiles
            threat_detected = False
            for p_eid, proj, p_trans, p_vel in world.query(ProjectileComponent, TransformComponent, VelocityComponent):
                if proj.team != combat.team:
                    rel_pos = transform.position - p_trans.position
                    rel_pos[1] = 0.0
                    p_dist = float(np.linalg.norm(rel_pos))
                    closing = float(np.dot(Math3D.normalize(p_vel.linear), Math3D.normalize(rel_pos)))
                    if p_dist < 5.2 and closing > 0.72:
                        threat_detected = True
                        break

            caster.wants_cast_barrier = threat_detected
            caster.wants_cast_projectile = (
                dist < 16.5 and
                combat.proj_cooldown <= 0.0 and
                combat.mana >= caster.projectile_mana_cost + 8.0
            )


class MovementAndTransformSystem:
    def update(self, world: ECSWorld, dt: float):
        arena_limit = 13.0

        for eid, transform, velocity in world.query(TransformComponent, VelocityComponent):
            speed = float(np.linalg.norm(velocity.linear))
            if speed > velocity.max_speed:
                velocity.linear = (velocity.linear / speed) * velocity.max_speed

            transform.position = transform.position + velocity.linear * dt

            if velocity.constrain_to_arena:
                xz = transform.position[[0, 2]]
                r = float(np.linalg.norm(xz))
                if r > arena_limit:
                    xz_clamped = (xz / r) * arena_limit
                    transform.position[0] = xz_clamped[0]
                    transform.position[2] = xz_clamped[1]

            damp_factor = math.exp(-velocity.damping * dt)
            velocity.linear *= damp_factor

        # Lock active Barriers to their caster's spatial coordinates
        for b_eid, barrier, b_trans in world.query(BarrierComponent, TransformComponent):
            owner_trans = world.get_component(barrier.owner_id, TransformComponent)
            if owner_trans is not None:
                b_trans.position[0] = owner_trans.position[0]
                b_trans.position[1] = 1.05
                b_trans.position[2] = owner_trans.position[2]
                b_trans.rotation_y = world.time * 0.6

        # Batch update 4x4 Model Matrices
        for eid, transform in world.query(TransformComponent):
            transform.model_matrix = Math3D.compose_model_matrix(
                transform.position, transform.rotation_y, transform.scale
            )


class SpellAndCombatSystem:
    def update(self, world: ECSWorld, dt: float):
        # 1. Update combatant cooldowns, mana regeneration, and spell casting requests
        for eid, transform, combat, caster, renderable in world.query(
            TransformComponent, CombatStateComponent, SpellCasterComponent, RenderableComponent
        ):
            if combat.hp <= 0.0:
                combat.state = "DEFEATED"
                transform.scale = np.array([1.0, 0.18, 1.0], dtype=np.float32)
                continue

            combat.mana = min(combat.max_mana, combat.mana + combat.mana_regen * dt)
            combat.proj_cooldown = max(0.0, combat.proj_cooldown - dt)
            combat.barrier_cooldown = max(0.0, combat.barrier_cooldown - dt)
            combat.cast_anim_timer = max(0.0, combat.cast_anim_timer - dt)

            # Conjure Refractive Barrier Ward
            if (
                caster.wants_cast_barrier and
                combat.barrier_cooldown <= 0.0 and
                combat.active_barrier_entity is None and
                combat.mana >= caster.barrier_mana_cost
            ):
                combat.mana -= caster.barrier_mana_cost
                combat.barrier_cooldown = caster.barrier_cd_duration
                combat.cast_anim_timer = 0.65
                combat.state = "CHANNELING_BARRIER"

                b_eid = world.create_entity()
                r_scale = caster.barrier_radius
                world.add_component(
                    b_eid,
                    TransformComponent(
                        position=np.array([transform.position[0], 1.05, transform.position[2]], dtype=np.float32),
                        rotation_y=0.0,
                        scale=np.array([r_scale, r_scale, r_scale], dtype=np.float32),
                    )
                )
                world.add_component(
                    b_eid,
                    BarrierComponent(
                        owner_id=eid,
                        team=combat.team,
                        lifetime=caster.barrier_duration,
                        age=0.0,
                        radius=caster.barrier_radius,
                        hit_flash=0.75,
                    )
                )
                world.add_component(
                    b_eid,
                    RenderableComponent(
                        mesh_key="barrier_sphere",
                        shader_pass="BARRIER",
                        primary_color=renderable.primary_color.copy(),
                        secondary_color=renderable.secondary_color.copy(),
                    )
                )
                combat.active_barrier_entity = b_eid

            # Cast Volumetric SDF Arcane Projectile
            if (
                caster.wants_cast_projectile and
                combat.proj_cooldown <= 0.0 and
                combat.mana >= caster.projectile_mana_cost
            ):
                combat.mana -= caster.projectile_mana_cost
                combat.proj_cooldown = caster.projectile_cd_duration
                combat.cast_anim_timer = 0.40
                combat.state = "CASTING_PROJECTILE"

                spawn_pos = transform.position + caster.aim_direction * 1.15
                spawn_pos[1] = 1.12
                proj_vel = caster.aim_direction * caster.projectile_speed

                p_eid = world.create_entity()
                p_rad = 0.62
                world.add_component(
                    p_eid,
                    TransformComponent(
                        position=spawn_pos,
                        rotation_y=transform.rotation_y,
                        scale=np.array([p_rad, p_rad, p_rad], dtype=np.float32),
                    )
                )
                world.add_component(
                    p_eid,
                    VelocityComponent(
                        linear=proj_vel,
                        damping=0.0,
                        max_speed=35.0,
                        constrain_to_arena=False,
                    )
                )
                world.add_component(
                    p_eid,
                    ProjectileComponent(
                        owner_id=eid,
                        team=combat.team,
                        damage=caster.projectile_damage,
                        lifetime=3.0,
                        age=0.0,
                        radius=p_rad,
                    )
                )
                world.add_component(
                    p_eid,
                    RenderableComponent(
                        mesh_key="projectile_cube",
                        shader_pass="SDF_PROJECTILE",
                        primary_color=renderable.primary_color.copy(),
                        secondary_color=renderable.secondary_color.copy(),
                    )
                )

        # 2. Update Barrier lifetimes and hit-flash decay
        for b_eid, barrier in world.query(BarrierComponent):
            barrier.age += dt
            barrier.hit_flash = max(0.0, barrier.hit_flash - 2.6 * dt)
            if barrier.age >= barrier.lifetime:
                owner_combat = world.get_component(barrier.owner_id, CombatStateComponent)
                if owner_combat is not None and owner_combat.active_barrier_entity == b_eid:
                    owner_combat.active_barrier_entity = None
                world.destroy_entity(b_eid)

        # 3. Update Projectiles & Resolve Collisions (Barrier Deflection + Combatant Impact)
        barriers = world.query(BarrierComponent, TransformComponent, RenderableComponent)
        combatants = world.query(CombatStateComponent, TransformComponent, VelocityComponent)

        for p_eid, proj, p_trans, p_vel, p_rend in world.query(
            ProjectileComponent, TransformComponent, VelocityComponent, RenderableComponent
        ):
            proj.age += dt
            if proj.age >= proj.lifetime or float(np.linalg.norm(p_trans.position[[0, 2]])) > 20.0:
                world.destroy_entity(p_eid)
                continue

            # Check Projectile vs Refractive Barrier Collision (Deflection!)
            deflected = False
            for b_eid, barrier, b_trans, b_rend in barriers:
                if barrier.team != proj.team:
                    delta = p_trans.position - b_trans.position
                    dist = max(1e-5, float(np.linalg.norm(delta)))
                    if dist < (proj.radius + barrier.radius):
                        normal = delta / dist
                        normal[1] = 0.0
                        normal = Math3D.normalize(normal)

                        # Reflect velocity vector off the refractive barrier normal
                        v_dot_n = float(np.dot(p_vel.linear, normal))
                        p_vel.linear = (p_vel.linear - 2.0 * v_dot_n * normal) * 1.15
                        p_trans.position = b_trans.position + normal * (barrier.radius + proj.radius + 0.08)

                        # Convert projectile allegiance & chromatic tint to the barrier's caster
                        proj.team = barrier.team
                        proj.owner_id = barrier.owner_id
                        proj.age = 0.0
                        p_rend.primary_color = b_rend.primary_color.copy()
                        p_rend.secondary_color = b_rend.secondary_color.copy()
                        barrier.hit_flash = 1.0
                        deflected = True
                        break

            if deflected:
                continue

            # Check Projectile vs Combatant Collision
            for c_eid, combat, c_trans, c_vel in combatants:
                if combat.team != proj.team and combat.hp > 0.0:
                    # Skip if protected by an active barrier
                    if combat.active_barrier_entity is not None:
                        continue

                    delta_xz = p_trans.position[[0, 2]] - c_trans.position[[0, 2]]
                    dist_xz = float(np.linalg.norm(delta_xz))
                    if dist_xz < (proj.radius + 0.58):
                        combat.hp = max(0.0, combat.hp - proj.damage)
                        combat.cast_anim_timer = 0.35
                        combat.state = "STAGGERED"

                        knock_dir = Math3D.normalize(
                            np.array([p_vel.linear[0], 0.0, p_vel.linear[2]], dtype=np.float32)
                        )
                        c_vel.linear += knock_dir * 12.5
                        world.destroy_entity(p_eid)
                        break


class RenderSystem:
    def __init__(self, ctx: moderngl.Context, width: int, height: int):
        self.ctx = ctx
        self.width = width
        self.height = height

        # Compile GLSL Shader Programs
        self.arena_prog = self.ctx.program(vertex_shader=ARENA_VERT_SHADER, fragment_shader=ARENA_FRAG_SHADER)
        self.wizard_prog = self.ctx.program(vertex_shader=WIZARD_VERT_SHADER, fragment_shader=WIZARD_FRAG_SHADER)
        self.proj_prog = self.ctx.program(vertex_shader=PROJECTILE_VERT_SHADER, fragment_shader=PROJECTILE_FRAG_SHADER)
        self.barrier_prog = self.ctx.program(vertex_shader=BARRIER_VERT_SHADER, fragment_shader=BARRIER_FRAG_SHADER)
        self.comp_prog = self.ctx.program(vertex_shader=COMPOSITE_VERT_SHADER, fragment_shader=COMPOSITE_FRAG_SHADER)

        self.programs: Dict[str, moderngl.Program] = {
            "ARENA": self.arena_prog,
            "WIZARD": self.wizard_prog,
            "SDF_PROJECTILE": self.proj_prog,
            "BARRIER": self.barrier_prog,
        }

        # Build Procedural Geometry Buffers & VAOs
        self.vaos: Dict[str, Dict[str, moderngl.VertexArray]] = {}
        self._register_mesh("arena_floor", MeshFactory.create_arena_floor())
        self._register_mesh("monolith_pillars", MeshFactory.create_monolith_pillars())
        self._register_mesh("wizard", MeshFactory.create_wizard_construct())
        self._register_mesh("projectile_cube", MeshFactory.create_unit_cube(1.15))
        self._register_mesh("barrier_sphere", MeshFactory.create_uv_sphere(28, 40))

        # Fullscreen Quad for FBO Composite & HUD
        quad_data = np.array([
            -1.0, -1.0, 0.0, 0.0,
             1.0, -1.0, 1.0, 0.0,
             1.0,  1.0, 1.0, 1.0,
            -1.0, -1.0, 0.0, 0.0,
             1.0,  1.0, 1.0, 1.0,
            -1.0,  1.0, 0.0, 1.0,
        ], dtype=np.float32)
        quad_vbo = self.ctx.buffer(quad_data.tobytes())
        self.quad_vao = self.ctx.vertex_array(self.comp_prog, [(quad_vbo, "2f 2f", "in_pos", "in_uv")])

        # Offscreen Scene Framebuffer for Screen-Space Refraction
        self.scene_color_tex: Optional[moderngl.Texture] = None
        self.scene_depth_tex: Optional[moderngl.Texture] = None
        self.scene_fbo: Optional[moderngl.Framebuffer] = None
        fb_w, fb_h = self.ctx.screen.size
        self.resize(max(width, fb_w), max(height, fb_h))

    def _build_vao_for_prog(self, prog: moderngl.Program, vbo: moderngl.Buffer) -> moderngl.VertexArray:
        """
        Builds a VertexArray for a 32-byte interleaved VBO (3f pos, 3f normal, 2f uv)
        while automatically substituting byte-padding ('12x' or '8x') for any vertex
        attribute eliminated by the GLSL compiler during linking.
        """
        fmt_parts: List[str] = []
        attrib_names: List[str] = []

        if "in_position" in prog:
            fmt_parts.append("3f")
            attrib_names.append("in_position")
        else:
            fmt_parts.append("12x")

        if "in_normal" in prog:
            fmt_parts.append("3f")
            attrib_names.append("in_normal")
        else:
            fmt_parts.append("12x")

        if "in_uv" in prog:
            fmt_parts.append("2f")
            attrib_names.append("in_uv")
        else:
            fmt_parts.append("8x")

        fmt_str = " ".join(fmt_parts)
        return self.ctx.vertex_array(prog, [(vbo, fmt_str, *attrib_names)])

    def _register_mesh(self, key: str, vertex_data: np.ndarray):
        vbo = self.ctx.buffer(vertex_data.tobytes())
        self.vaos[key] = {
            pass_name: self._build_vao_for_prog(prog, vbo)
            for pass_name, prog in self.programs.items()
        }

    def resize(self, width: int, height: int):
        self.width = max(1, width)
        self.height = max(1, height)
        if self.scene_fbo is not None:
            self.scene_fbo.release()
        if self.scene_color_tex is not None:
            self.scene_color_tex.release()
        if self.scene_depth_tex is not None:
            self.scene_depth_tex.release()

        self.scene_color_tex = self.ctx.texture((self.width, self.height), 4, dtype="f2")
        self.scene_color_tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.scene_depth_tex = self.ctx.depth_texture((self.width, self.height))
        self.scene_fbo = self.ctx.framebuffer(
            color_attachments=[self.scene_color_tex],
            depth_attachment=self.scene_depth_tex,
        )

    @staticmethod
    def _set_uniform(prog: moderngl.Program, name: str, val):
        if name in prog:
            prog[name].value = val

    @staticmethod
    def _write_uniform(prog: moderngl.Program, name: str, raw_bytes: bytes):
        if name in prog:
            prog[name].write(raw_bytes)

    def render(self, world: ECSWorld):
        # Ensure offscreen FBO matches actual default framebuffer pixel dimensions (e.g. macOS Retina)
        fb_w, fb_h = self.ctx.screen.size
        if fb_w > 0 and fb_h > 0 and (fb_w != self.width or fb_h != self.height):
            self.resize(fb_w, fb_h)

        # Update orbital camera matrices
        aspect = float(self.width) / float(self.height)
        world.proj_matrix = Math3D.perspective(46.0, aspect, 0.5, 85.0)

        p_trans = world.get_component(world.player_entity, TransformComponent)
        ai_trans = world.get_component(world.ai_entity, TransformComponent)
        p_pos = p_trans.position if p_trans is not None else np.zeros(3, dtype=np.float32)
        ai_pos = ai_trans.position if ai_trans is not None else np.zeros(3, dtype=np.float32)

        # Dynamic camera focus midpoint biased gently toward the player
        focus = p_pos * 0.4 + ai_pos * 0.25
        focus[1] = 0.8

        cam_x = focus[0] + world.camera_distance * math.sin(world.camera_yaw)
        cam_z = focus[2] + world.camera_distance * math.cos(world.camera_yaw)
        world.camera_pos = np.array([cam_x, world.camera_height, cam_z], dtype=np.float32)
        world.view_matrix = Math3D.look_at(
            world.camera_pos, focus, np.array([0.0, 1.0, 0.0], dtype=np.float32)
        )

        view_bytes = Math3D.gl_bytes(world.view_matrix)
        proj_bytes = Math3D.gl_bytes(world.proj_matrix)
        identity_bytes = Math3D.gl_bytes(np.identity(4, dtype=np.float32))
        cam_tuple = (float(world.camera_pos[0]), float(world.camera_pos[1]), float(world.camera_pos[2]))

        # =====================================================================
        # PASS 1: OFFSCREEN SCENE FBO (ARENA, MONOLITHS, WIZARDS, SDF SPELLS)
        # =====================================================================
        self.scene_fbo.use()
        self.ctx.viewport = (0, 0, self.width, self.height)
        self.ctx.clear(0.02, 0.026, 0.038, 1.0, depth=1.0)
        self.ctx.enable(moderngl.DEPTH_TEST | moderngl.CULL_FACE)
        self.ctx.disable(moderngl.BLEND)

        # 1A. Render Arena Floor & Peripheral Monolith Pillars
        self._write_uniform(self.arena_prog, "u_model", identity_bytes)
        self._write_uniform(self.arena_prog, "u_view", view_bytes)
        self._write_uniform(self.arena_prog, "u_proj", proj_bytes)
        self._set_uniform(self.arena_prog, "u_time", float(world.time))
        self._set_uniform(self.arena_prog, "u_camera_pos", cam_tuple)
        self._set_uniform(self.arena_prog, "u_player_pos", (float(p_pos[0]), float(p_pos[1]), float(p_pos[2])))
        self._set_uniform(self.arena_prog, "u_ai_pos", (float(ai_pos[0]), float(ai_pos[1]), float(ai_pos[2])))

        self._set_uniform(self.arena_prog, "u_is_pillar", 0.0)
        self.vaos["arena_floor"]["ARENA"].render(moderngl.TRIANGLES)

        self._set_uniform(self.arena_prog, "u_is_pillar", 1.0)
        self.vaos["monolith_pillars"]["ARENA"].render(moderngl.TRIANGLES)

        # 1B. Render Arcane Combatant Constructs
        self._write_uniform(self.wizard_prog, "u_view", view_bytes)
        self._write_uniform(self.wizard_prog, "u_proj", proj_bytes)
        self._set_uniform(self.wizard_prog, "u_time", float(world.time))
        self._set_uniform(self.wizard_prog, "u_camera_pos", cam_tuple)

        for eid, transform, renderable in world.query(TransformComponent, RenderableComponent):
            if renderable.shader_pass == "WIZARD":
                combat = world.get_component(eid, CombatStateComponent)
                cast_glow = combat.cast_anim_timer * 2.0 if combat is not None else 0.0

                self._write_uniform(self.wizard_prog, "u_model", Math3D.gl_bytes(transform.model_matrix))
                self._set_uniform(self.wizard_prog, "u_base_color", tuple(float(x) for x in renderable.primary_color))
                self._set_uniform(self.wizard_prog, "u_accent_color", tuple(float(x) for x in renderable.secondary_color))
                self._set_uniform(self.wizard_prog, "u_cast_intensity", float(cast_glow))
                self.vaos[renderable.mesh_key]["WIZARD"].render(moderngl.TRIANGLES)

        # 1C. Render 3D Volumetric Raymarched SDF Projectiles (Additive Blending)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE)
        self.ctx.depth_mask = False
        self.ctx.disable(moderngl.CULL_FACE)

        self._write_uniform(self.proj_prog, "u_view", view_bytes)
        self._write_uniform(self.proj_prog, "u_proj", proj_bytes)
        self._set_uniform(self.proj_prog, "u_time", float(world.time))
        self._set_uniform(self.proj_prog, "u_camera_pos", cam_tuple)

        for eid, proj, transform, renderable in world.query(
            ProjectileComponent, TransformComponent, RenderableComponent
        ):
            self._write_uniform(self.proj_prog, "u_model", Math3D.gl_bytes(transform.model_matrix))
            self._set_uniform(
                self.proj_prog,
                "u_proj_center",
                (float(transform.position[0]), float(transform.position[1]), float(transform.position[2]))
            )
            self._set_uniform(self.proj_prog, "u_proj_radius", float(proj.radius))
            self._set_uniform(self.proj_prog, "u_primary_color", tuple(float(x) for x in renderable.primary_color))
            self._set_uniform(self.proj_prog, "u_secondary_color", tuple(float(x) for x in renderable.secondary_color))
            self.vaos[renderable.mesh_key]["SDF_PROJECTILE"].render(moderngl.TRIANGLES)

        self.ctx.depth_mask = True

        # =====================================================================
        # PASS 2: SCREEN COMPOSITE, REFRACTIVE BARRIERS & DIEGETIC HUD
        # =====================================================================
        self.ctx.screen.use()
        self.ctx.viewport = (0, 0, self.width, self.height)
        self.ctx.clear(0.0, 0.0, 0.0, 1.0)
        self.ctx.disable(moderngl.DEPTH_TEST | moderngl.BLEND | moderngl.CULL_FACE)

        # 2A. Draw Tone-Mapped Scene + SDF HUD Overlay
        p_combat = world.get_component(world.player_entity, CombatStateComponent)
        ai_combat = world.get_component(world.ai_entity, CombatStateComponent)

        p_hp_ratio = (p_combat.hp / p_combat.max_hp) if p_combat is not None else 0.0
        p_mp_ratio = (p_combat.mana / p_combat.max_mana) if p_combat is not None else 0.0
        p_ward_ready = 1.0 if (p_combat is not None and p_combat.barrier_cooldown <= 0.0) else 0.15
        ai_hp_ratio = (ai_combat.hp / ai_combat.max_hp) if ai_combat is not None else 0.0

        self.scene_color_tex.use(location=0)
        self._set_uniform(self.comp_prog, "u_scene_color", 0)
        self._set_uniform(self.comp_prog, "u_resolution", (float(self.width), float(self.height)))
        self._set_uniform(self.comp_prog, "u_player_hp", float(p_hp_ratio))
        self._set_uniform(self.comp_prog, "u_player_mana", float(p_mp_ratio))
        self._set_uniform(self.comp_prog, "u_player_barrier_ready", float(p_ward_ready))
        self._set_uniform(self.comp_prog, "u_ai_hp", float(ai_hp_ratio))
        self._set_uniform(self.comp_prog, "u_time", float(world.time))
        self.quad_vao.render(moderngl.TRIANGLES)

        # 2B. Render Glass-Like Refractive Magical Barriers (Sampling Scene Color & Depth)
        self.ctx.enable(moderngl.CULL_FACE)
        self.scene_color_tex.use(location=0)
        self.scene_depth_tex.use(location=1)

        self._write_uniform(self.barrier_prog, "u_view", view_bytes)
        self._write_uniform(self.barrier_prog, "u_proj", proj_bytes)
        self._set_uniform(self.barrier_prog, "u_scene_color", 0)
        self._set_uniform(self.barrier_prog, "u_scene_depth", 1)
        self._set_uniform(self.barrier_prog, "u_resolution", (float(self.width), float(self.height)))
        self._set_uniform(self.barrier_prog, "u_time", float(world.time))
        self._set_uniform(self.barrier_prog, "u_camera_pos", cam_tuple)

        for b_eid, barrier, transform, renderable in world.query(
            BarrierComponent, TransformComponent, RenderableComponent
        ):
            self._write_uniform(self.barrier_prog, "u_model", Math3D.gl_bytes(transform.model_matrix))
            self._set_uniform(self.barrier_prog, "u_barrier_color", tuple(float(x) for x in renderable.secondary_color))
            self._set_uniform(self.barrier_prog, "u_secondary_color", tuple(float(x) for x in renderable.primary_color))
            self._set_uniform(self.barrier_prog, "u_hit_flash", float(barrier.hit_flash))
            self.vaos[renderable.mesh_key]["BARRIER"].render(moderngl.TRIANGLES)

    def release(self):
        if self.scene_fbo is not None:
            self.scene_fbo.release()
        if self.scene_color_tex is not None:
            self.scene_color_tex.release()
        if self.scene_depth_tex is not None:
            self.scene_depth_tex.release()


# =============================================================================
# GAME ENGINE BOOTSTRAP & ARENA SPAWNER
# =============================================================================

def populate_arena(world: ECSWorld):
    for eid in list(world._entities):
        world.destroy_entity(eid)
    world.flush_destroyed()

    # 1. Spawn Player Combatant (Emerald / Cyan Geometric Archon)
    player_id = world.create_entity()
    world.player_entity = player_id
    world.add_component(
        player_id,
        TransformComponent(
            position=np.array([0.0, 0.0, 6.5], dtype=np.float32),
            rotation_y=math.pi,
            scale=np.ones(3, dtype=np.float32),
        )
    )
    world.add_component(player_id, VelocityComponent())
    world.add_component(player_id, CombatStateComponent(team=1))
    world.add_component(
        player_id,
        SpellCasterComponent(
            aim_direction=np.array([0.0, 0.0, -1.0], dtype=np.float32)
        )
    )
    world.add_component(
        player_id,
        RenderableComponent(
            mesh_key="wizard",
            shader_pass="WIZARD",
            primary_color=np.array([0.07, 0.14, 0.12], dtype=np.float32),
            secondary_color=np.array([0.04, 0.98, 0.56], dtype=np.float32),
        )
    )

    # 2. Spawn AI Opponent Combatant (Obsidian / Cyan-Azure Archon)
    ai_id = world.create_entity()
    world.ai_entity = ai_id
    world.add_component(
        ai_id,
        TransformComponent(
            position=np.array([0.0, 0.0, -6.5], dtype=np.float32),
            rotation_y=0.0,
            scale=np.ones(3, dtype=np.float32),
        )
    )
    world.add_component(ai_id, VelocityComponent(max_speed=6.8))
    world.add_component(ai_id, CombatStateComponent(team=2))
    world.add_component(
        ai_id,
        SpellCasterComponent(
            aim_direction=np.array([0.0, 0.0, 1.0], dtype=np.float32),
            projectile_cd_duration=0.65,
        )
    )
    world.add_component(ai_id, AIComponent(target_entity=player_id))
    world.add_component(
        ai_id,
        RenderableComponent(
            mesh_key="wizard",
            shader_pass="WIZARD",
            primary_color=np.array([0.06, 0.09, 0.16], dtype=np.float32),
            secondary_color=np.array([0.02, 0.86, 1.00], dtype=np.float32),
        )
    )


def main():
    pygame.init()

    # Configure OpenGL 3.3 Core Profile (macOS & Cross-Platform compatible)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True)

    win_w, win_h = 1280, 760
    pygame.display.set_mode((win_w, win_h), pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE)
    pygame.display.set_caption("ARCANE MONOLITH // 3D SDF & Refractive Arena Prototype")

    ctx = moderngl.create_context()
    clock = pygame.time.Clock()

    world = ECSWorld()
    populate_arena(world)

    input_sys = InputSystem()
    ai_sys = AISystem()
    move_sys = MovementAndTransformSystem()
    combat_sys = SpellAndCombatSystem()
    render_sys = RenderSystem(ctx, win_w, win_h)

    running = True
    try:
        while running:
            dt = min(0.05, clock.tick(60) / 1000.0)
            world.time += dt

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r:
                        populate_arena(world)
                elif event.type == pygame.MOUSEWHEEL:
                    world.camera_distance = float(np.clip(world.camera_distance - event.y * 1.2, 12.0, 32.0))
                elif event.type == pygame.VIDEORESIZE:
                    win_w, win_h = max(320, event.w), max(240, event.h)
                    fb_w, fb_h = ctx.screen.size
                    render_sys.resize(max(win_w, fb_w), max(win_h, fb_h))

            # Execute ECS Pipeline
            cur_win_size = pygame.display.get_window_size()
            input_sys.update(world, dt, cur_win_size)
            ai_sys.update(world, dt)
            combat_sys.update(world, dt)
            world.flush_destroyed()
            move_sys.update(world, dt)
            render_sys.render(world)

            # Update Window Telemetry
            p_combat = world.get_component(world.player_entity, CombatStateComponent)
            ai_combat = world.get_component(world.ai_entity, CombatStateComponent)
            if p_combat and ai_combat:
                status = (
                    f"ARCANE MONOLITH | Player HP: {p_combat.hp:.0f} MP: {p_combat.mana:.0f} "
                    f"| Opponent HP: {ai_combat.hp:.0f} | [WASD] Move [LMB/Space] SDF Spell "
                    f"[RMB/Shift] Refractive Ward [R] Reset"
                )
                pygame.display.set_caption(status)

            pygame.display.flip()

    finally:
        render_sys.release()
        ctx.release()
        pygame.quit()
        sys.exit(0)


if __name__ == "__main__":
    main()