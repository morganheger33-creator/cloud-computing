"""
The Wanderer's Light - An Extended Abstract Animated Story
-------------------------------------------------------------
A longer symbolic story told entirely through shapes, glow, trails,
and a starfield backdrop, paired with storybook narration.

Story arc (11 chapters):
  1. Birth       - a light flickers into being
  2. Solitude    - it drifts alone through a quiet dark
  3. The Journey - it travels far, leaving a trail of light
  4. The Storm   - turbulence and flickering danger
  5. Despair     - the light dims, almost goes out
  6. A Signal    - a faint second light appears in the distance
  7. Approach    - the two lights draw toward each other
  8. Trust       - they begin to orbit, testing closeness
  9. Union       - they merge into a single brilliant light
 10. Radiance    - a burst of color and particles - pure joy
 11. Peace       - the light settles, glowing softly among the stars

Run with:
    python wanderers_light.py

Requirements:
    pip install matplotlib numpy
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import matplotlib.patches as patches
from collections import deque

# ---------------------------------------------------------------
# Timing
# ---------------------------------------------------------------
FPS = 30
SCENES = [
    {"name": "birth",      "frames": 60,
     "text": "In the beginning, there was only dark.\nThen, a single light flickered into being."},
    {"name": "solitude",   "frames": 70,
     "text": "It drifted quietly,\nnot yet knowing what it was searching for."},
    {"name": "journey",    "frames": 90,
     "text": "So it began to travel,\nfar across the endless night."},
    {"name": "storm",      "frames": 80,
     "text": "But the way grew rough,\nand the dark pressed in from every side."},
    {"name": "despair",    "frames": 70,
     "text": "For a while, its light grew faint,\nand it wondered if it would go out."},
    {"name": "signal",     "frames": 60,
     "text": "Then, far away,\nsomething answered back."},
    {"name": "approach",   "frames": 80,
     "text": "Slowly, carefully,\nthe two lights moved toward one another."},
    {"name": "trust",      "frames": 80,
     "text": "They circled each other for a while,\nlearning that it was safe to be close."},
    {"name": "union",      "frames": 70,
     "text": "And at last,\nthey became one light, brighter than before."},
    {"name": "radiance",   "frames": 90,
     "text": "In that moment,\nall the color it had ever held burst free."},
    {"name": "peace",      "frames": 90,
     "text": "From then on, it glowed softly among the stars -\nnever alone again."},
]

scene_bounds = []
start = 0
for s in SCENES:
    scene_bounds.append((start, start + s["frames"], s))
    start += s["frames"]
TOTAL_FRAMES = start

# ---------------------------------------------------------------
# Figure & starfield background
# ---------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 8))
fig.patch.set_facecolor("black")
ax.set_facecolor("black")
ax.set_xlim(-10, 10)
ax.set_ylim(-10, 10)
ax.set_aspect("equal")
ax.axis("off")

rng = np.random.default_rng(7)
N_STARS = 220
star_x = rng.uniform(-10, 10, N_STARS)
star_y = rng.uniform(-10, 10, N_STARS)
star_base_size = rng.uniform(1, 8, N_STARS)
star_phase = rng.uniform(0, 2 * np.pi, N_STARS)
stars = ax.scatter(star_x, star_y, s=star_base_size, c="white", alpha=0.6, zorder=0)

# Caption text
caption = ax.text(
    0, -8.7, "", color="white", fontsize=13, ha="center", va="center",
    fontstyle="italic", alpha=0.0, zorder=10
)
chapter_label = ax.text(
    0, 9.0, "", color="#cfcfcf", fontsize=11, ha="center", va="center",
    alpha=0.0, zorder=10, fontweight="bold"
)

# ---------------------------------------------------------------
# Glow layers for the main light (several translucent circles
# of increasing radius / decreasing alpha simulate a soft bloom).
# ---------------------------------------------------------------
N_GLOW = 5
main_glow = [patches.Circle((0, 0), 0.5, color="#88bfff", alpha=0.0, zorder=2)
             for _ in range(N_GLOW)]
for g in main_glow:
    ax.add_patch(g)
main_core = patches.Circle((0, 0), 0.4, color="white", alpha=0.0, zorder=3)
ax.add_patch(main_core)

second_glow = [patches.Circle((5, 3), 0.5, color="#ffb08a", alpha=0.0, zorder=2)
               for _ in range(N_GLOW)]
for g in second_glow:
    ax.add_patch(g)
second_core = patches.Circle((5, 3), 0.4, color="white", alpha=0.0, zorder=3)
ax.add_patch(second_core)

# Trail history (fading past positions of the main light)
TRAIL_LEN = 28
trail_history = deque(maxlen=TRAIL_LEN)
trail_scatter = ax.scatter([], [], s=[], c=[], alpha=0.0, zorder=1)

# Radiance particle burst
N_PARTICLES = 90
particle_angles = np.linspace(0, 2 * np.pi, N_PARTICLES, endpoint=False)
particle_speed = rng.uniform(0.8, 1.3, N_PARTICLES)
particles = ax.scatter([], [], s=[], c=[], alpha=0.0, zorder=4)

# Lightning flicker overlay for the storm scene
flash_overlay = patches.Rectangle((-10, -10), 20, 20, color="white", alpha=0.0, zorder=5)
ax.add_patch(flash_overlay)


def set_glow(glow_list, core, center, base_color, radius, alpha, core_alpha=None):
    """Update a stack of glow circles + bright core to sit at `center`."""
    for i, g in enumerate(glow_list):
        g.center = center
        g.set_radius(radius * (1.3 + i * 0.55))
        g.set_alpha(max(0.0, alpha * (0.22 - i * 0.03)))
        g.set_color(base_color)
    core.center = center
    core.set_radius(radius * 0.55)
    core.set_alpha(core_alpha if core_alpha is not None else alpha)


def get_scene(frame):
    for start_f, end_f, scene in scene_bounds:
        if start_f <= frame < end_f:
            local = (frame - start_f) / (end_f - start_f)
            return scene, local
    return scene_bounds[-1][2], 1.0


def fade(local, fade_in=0.12, fade_out=0.85):
    if local < fade_in:
        return local / fade_in
    elif local > fade_out:
        return max(0.0, 1 - (local - fade_out) / (1 - fade_out))
    return 1.0


def ease(x):
    return x * x * (3 - 2 * x)


def init():
    caption.set_alpha(0)
    chapter_label.set_alpha(0)
    for g in main_glow + second_glow:
        g.set_alpha(0)
    main_core.set_alpha(0)
    second_core.set_alpha(0)
    trail_scatter.set_alpha(0)
    particles.set_alpha(0)
    flash_overlay.set_alpha(0)
    trail_history.clear()
    return (caption, chapter_label, *main_glow, main_core,
            *second_glow, second_core, trail_scatter, particles, flash_overlay)


def twinkle_stars(frame):
    t = frame / FPS
    sizes = star_base_size * (0.6 + 0.4 * np.sin(t * 1.5 + star_phase))
    stars.set_sizes(np.clip(sizes, 0.5, None))


def animate(frame):
    scene, local = get_scene(frame)
    name = scene["name"]
    e = ease(local)

    twinkle_stars(frame)

    text_alpha = fade(local)
    caption.set_text(scene["text"])
    caption.set_alpha(max(0.0, text_alpha))
    chapter_label.set_text(name.upper().replace("_", " "))
    chapter_label.set_alpha(max(0.0, text_alpha) * 0.8)

    # Reset per-frame optional elements
    set_glow(second_glow, second_core, second_core.center, "#ffb08a", 0.5, 0.0)
    particles.set_alpha(0)
    flash_overlay.set_alpha(0)

    if name == "birth":
        # Flicker into existence
        flicker = 0.3 + 0.7 * min(1.0, local * 3) * (0.7 + 0.3 * np.sin(local * 40))
        set_glow(main_glow, main_core, (0, 0), "#88bfff", 0.5, flicker, core_alpha=flicker)
        trail_history.clear()

    elif name == "solitude":
        # Gentle drifting pulse, alone
        pulse = 0.5 + 0.05 * np.sin(local * 4 * np.pi)
        pos = (2 * np.sin(local * 2 * np.pi) * 0.4, 1.5 * np.cos(local * 2 * np.pi) * 0.3)
        set_glow(main_glow, main_core, pos, "#6f9bd1", pulse, 0.9)
        trail_history.append((*pos, 0.5))

    elif name == "journey":
        # Long sweeping travel across the sky, trail builds behind it
        x = -8 + 16 * e
        y = 3 * np.sin(e * 3 * np.pi)
        set_glow(main_glow, main_core, (x, y), "#7fb2ff", 0.5, 0.95)
        trail_history.append((x, y, 0.5))

    elif name == "storm":
        # Turbulent shaking motion + occasional white flash
        jitter_x = -2 + 4 * np.sin(local * 10) + rng.normal(0, 0.15)
        jitter_y = 2 * np.cos(local * 13) + rng.normal(0, 0.15)
        flicker = 0.5 + 0.5 * np.sin(local * 50)
        set_glow(main_glow, main_core, (jitter_x, jitter_y), "#8fa8ff",
                 0.45 + 0.05 * flicker, 0.6 + 0.3 * flicker)
        trail_history.append((jitter_x, jitter_y, 0.4))
        # occasional lightning flash
        if int(local * 80) % 17 == 0:
            flash_overlay.set_alpha(0.15)

    elif name == "despair":
        # Dimming almost to nothing, motion slows
        dim = 1.0 - 0.75 * ease(min(local * 1.3, 1.0))
        pos = (0.5 * np.sin(local * np.pi), -1)
        set_glow(main_glow, main_core, pos, "#3a5578", 0.4, max(0.15, dim))
        trail_history.append((*pos, 0.3))

    elif name == "signal":
        # A second light fades in, far away
        set_glow(main_glow, main_core, (-2, -1), "#5a7ea8", 0.4, 0.5)
        appear = min(1.0, local * 1.6)
        set_glow(second_glow, second_core, (6, 4), "#ffb08a", 0.45, appear * 0.8)

    elif name == "approach":
        # Both lights drift toward one another
        x1 = -2 - 3 * (1 - e)
        x2 = 6 - 6 * e
        y1 = -1 + 1 * e
        y2 = 4 - 3 * e
        set_glow(main_glow, main_core, (x1, y1), "#88bfff", 0.5, 0.95)
        set_glow(second_glow, second_core, (x2, y2), "#ffb08a", 0.5, 0.95)
        trail_history.append((x1, y1, 0.45))

    elif name == "trust":
        # Orbit each other, testing closeness, gradually tightening
        radius = 3.0 - 1.5 * e
        angle = local * 4 * np.pi
        x1, y1 = radius * np.cos(angle), radius * np.sin(angle)
        x2, y2 = -radius * np.cos(angle), -radius * np.sin(angle)
        set_glow(main_glow, main_core, (x1, y1), "#88bfff", 0.5, 0.95)
        set_glow(second_glow, second_core, (x2, y2), "#ffb08a", 0.5, 0.95)
        trail_history.append((x1, y1, 0.4))
        trail_history.append((x2, y2, 0.4))

    elif name == "union":
        # Spiral together and blend color toward warm gold
        angle = e * 3 * np.pi
        dist = 1.4 * (1 - e)
        x1, y1 = -dist * np.cos(angle), dist * np.sin(angle)
        x2, y2 = dist * np.cos(angle), -dist * np.sin(angle)
        blend = e
        r = 0.53 + blend * (1.0 - 0.53)
        g = 0.75 + blend * (0.85 - 0.75)
        b = 1.0 - blend * (1.0 - 0.6)
        color = (r, g, b)
        set_glow(main_glow, main_core, (x1, y1), color, 0.55 + 0.15 * e, 1.0)
        set_glow(second_glow, second_core, (x2, y2), color, 0.55 + 0.15 * e, 1.0 - e)

    elif name == "radiance":
        # Big burst of colorful particles from the merged center
        set_glow(main_glow, main_core, (0, 0), "#ffd27a", 0.75 + 0.1 * np.sin(local * 8 * np.pi), 1.0)
        burst_e = ease(min(local * 1.2, 1.0))
        radius = 1 + 9 * burst_e
        xs = radius * np.cos(particle_angles * particle_speed + local * 3)
        ys = radius * np.sin(particle_angles * particle_speed + local * 3)
        colors = plt.cm.plasma((particle_angles / (2 * np.pi) + local) % 1.0)
        sizes = np.full(N_PARTICLES, np.clip(30 * (1 - burst_e) + 5, 3, None))
        particles.set_offsets(np.column_stack([xs, ys]))
        particles.set_color(colors)
        particles.set_sizes(sizes)
        particles.set_alpha(max(0.0, 1.0 - burst_e * 0.6))

    elif name == "peace":
        # Gentle breathing glow, calm among the stars
        breathe = 0.6 + 0.08 * np.sin(local * 2 * np.pi)
        set_glow(main_glow, main_core, (0, 0), "#ffe9c4", breathe, 1.0)

    # ---- Render the fading trail (older points = smaller & dimmer) ----
    if len(trail_history) > 0:
        pts = np.array([(p[0], p[1]) for p in trail_history])
        n = len(pts)
        alphas = np.linspace(0.05, 0.35, n)
        sizes = np.linspace(5, 40, n)
        trail_scatter.set_offsets(pts)
        trail_scatter.set_sizes(sizes)
        trail_scatter.set_color("#88bfff")
        trail_scatter.set_alpha(0.25)
        trail_scatter.set_array(None)

    return (caption, chapter_label, *main_glow, main_core,
            *second_glow, second_core, trail_scatter, particles, flash_overlay, stars)


anim = FuncAnimation(
    fig, animate, init_func=init,
    frames=TOTAL_FRAMES, interval=1000 / FPS, blit=False
)

plt.show()

# To export instead of showing a live window:
#   comment out plt.show() above, then uncomment one of the lines below.
#
# GIF (requires: pip install pillow) - note: long animation -> large file
# anim.save("wanderers_light.gif", writer="pillow", fps=FPS)
#
# MP4 (requires ffmpeg installed and on PATH) - recommended for this length
# anim.save("wanderers_light.mp4", writer="ffmpeg", fps=FPS, dpi=150)