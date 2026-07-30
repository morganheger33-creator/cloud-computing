"""
A Shape's Story - Abstract/Symbolic Animated Short
----------------------------------------------------
Tells a short emotional story using only shapes, color, and motion,
paired with storybook-style narration text.

Story arc:
  1. Solitude   - a small, dim, still circle alone in the dark
  2. Searching  - it begins to drift, faint light trailing behind it
  3. Encounter  - a second shape appears; they orbit one another
  4. Connection - the shapes merge, colors warming
  5. Joy        - a burst of color and particles radiating outward
  6. Peace      - the scene settles into soft, glowing calm

Run with:
    python shape_story.py

Requirements:
    pip install matplotlib numpy
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import matplotlib.patches as patches

# ---------------------------------------------------------------
# Scene timing (in frames). Adjust FPS below to change real-time length.
# ---------------------------------------------------------------
FPS = 30
SCENES = [
    {"name": "solitude",   "frames": 60,  "text": "Once, there was a small light,\nalone in the quiet dark."},
    {"name": "searching",  "frames": 60,  "text": "It began to drift,\nwondering if it was the only one."},
    {"name": "encounter",  "frames": 70,  "text": "Then, out of the dark,\nanother light appeared."},
    {"name": "connection", "frames": 70,  "text": "Slowly, they moved closer,\nuntil their light became one."},
    {"name": "joy",        "frames": 80,  "text": "And in that moment,\nwarmth burst into color."},
    {"name": "peace",      "frames": 70,  "text": "From then on,\nthe dark was never quite so dark again."},
]

# Precompute cumulative frame boundaries for each scene
scene_bounds = []
start = 0
for s in SCENES:
    scene_bounds.append((start, start + s["frames"], s))
    start += s["frames"]
TOTAL_FRAMES = start

# ---------------------------------------------------------------
# Figure setup
# ---------------------------------------------------------------
fig, ax = plt.subplots(figsize=(7, 7))
fig.patch.set_facecolor("black")
ax.set_facecolor("black")
ax.set_xlim(-10, 10)
ax.set_ylim(-10, 10)
ax.set_aspect("equal")
ax.axis("off")

# Text caption (storybook narration), placed near the bottom
caption = ax.text(
    0, -8.5, "", color="white", fontsize=13, ha="center", va="center",
    fontstyle="italic", wrap=True, alpha=0.0
)

# Main character shape
circle1 = patches.Circle((0, 0), 0.5, color="#88bfff", alpha=0.9)
ax.add_patch(circle1)

# Second character shape (appears later)
circle2 = patches.Circle((6, 4), 0.5, color="#ffb08a", alpha=0.0)
ax.add_patch(circle2)

# Particle burst for the "joy" scene
N_PARTICLES = 60
particle_angles = np.linspace(0, 2 * np.pi, N_PARTICLES, endpoint=False)
particles = ax.scatter([], [], s=10, c=[], alpha=0.0)

# Soft ambient glow ring for the "peace" scene
glow = patches.Circle((0, 0), 1.5, color="#ffe9c4", alpha=0.0, zorder=0)
ax.add_patch(glow)


def get_scene(frame):
    """Return (scene_dict, local_progress 0-1) for the given global frame."""
    for start_f, end_f, scene in scene_bounds:
        if start_f <= frame < end_f:
            local = (frame - start_f) / (end_f - start_f)
            return scene, local
    return scene_bounds[-1][2], 1.0


def fade(local, fade_in=0.15, fade_out=0.85):
    """Simple opacity envelope: fade in, hold, fade out."""
    if local < fade_in:
        return local / fade_in
    elif local > fade_out:
        return 1 - (local - fade_out) / (1 - fade_out)
    return 1.0


def ease(x):
    """Smoothstep easing for gentle motion."""
    return x * x * (3 - 2 * x)


def init():
    caption.set_alpha(0)
    circle2.set_alpha(0)
    particles.set_offsets(np.empty((0, 2)))
    particles.set_alpha(0)
    glow.set_alpha(0)
    return caption, circle1, circle2, particles, glow


def animate(frame):
    scene, local = get_scene(frame)
    name = scene["name"]
    text_alpha = fade(local, fade_in=0.15, fade_out=0.8)

    caption.set_text(scene["text"])
    caption.set_alpha(max(0.0, text_alpha))

    # Default states each frame (reset, then override per-scene below)
    circle2.set_alpha(0)
    particles.set_alpha(0)
    glow.set_alpha(0)

    if name == "solitude":
        # Small dim, gently pulsing circle, alone
        pulse = 0.5 + 0.05 * np.sin(local * 4 * np.pi)
        circle1.set_radius(pulse)
        circle1.set_color("#5a7ea8")
        circle1.center = (0, 0)

    elif name == "searching":
        # Drifts slowly across the dark, faint trailing light
        e = ease(local)
        x = -6 + 6 * e
        y = 2 * np.sin(e * 2 * np.pi) * 0.5
        circle1.center = (x, y)
        circle1.set_color("#6f9bd1")
        circle1.set_radius(0.55)

    elif name == "encounter":
        # Second shape fades in and both orbit toward center
        e = ease(local)
        circle1.center = (-3 * (1 - e), 0)
        circle2.center = (3 * (1 - e), 0)
        circle2.set_alpha(min(1.0, local * 2))
        circle1.set_color("#88bfff")
        circle2.set_color("#ffb08a")
        circle1.set_radius(0.55)
        circle2.set_radius(0.55)

    elif name == "connection":
        # Shapes spiral toward each other and merge, warming in color
        e = ease(local)
        angle = e * 3 * np.pi
        dist = 1.5 * (1 - e)
        circle1.center = (-dist * np.cos(angle), dist * np.sin(angle))
        circle2.center = (dist * np.cos(angle), -dist * np.sin(angle))
        circle2.set_alpha(1.0)

        # Blend colors from blue/orange toward warm gold as they merge
        blend = e
        r = 0.53 + blend * (1.0 - 0.53)
        g = 0.75 + blend * (0.85 - 0.75)
        b = 1.0 - blend * (1.0 - 0.6)
        circle1.set_color((r, g, b))
        circle2.set_color((r, g, b))
        circle1.set_radius(0.55 + 0.1 * e)
        circle2.set_radius(0.55 + 0.1 * e)

    elif name == "joy":
        # Burst of particles radiating outward from center, colors cycling
        circle1.center = (0, 0)
        circle1.set_alpha(1.0)
        circle1.set_color("#ffd27a")
        circle1.set_radius(0.7 + 0.1 * np.sin(local * 6 * np.pi))
        circle2.set_alpha(0)  # merged into circle1

        e = ease(min(local * 1.3, 1.0))
        radius = 1 + 8 * e
        xs = radius * np.cos(particle_angles + local * 2)
        ys = radius * np.sin(particle_angles + local * 2)
        colors = plt.cm.autumn((particle_angles / (2 * np.pi) + local) % 1.0)

        particles.set_offsets(np.column_stack([xs, ys]))
        particles.set_color(colors)
        particles.set_alpha(max(0.0, 1.0 - e * 0.7))

    elif name == "peace":
        # Everything settles; soft glow breathes gently
        circle1.center = (0, 0)
        circle1.set_color("#ffe9c4")
        circle1.set_radius(0.6)
        circle1.set_alpha(1.0)

        breathe = 1.5 + 0.3 * np.sin(local * 2 * np.pi)
        glow.set_radius(breathe)
        glow.set_alpha(0.25)

    return caption, circle1, circle2, particles, glow


anim = FuncAnimation(
    fig, animate, init_func=init,
    frames=TOTAL_FRAMES, interval=1000 / FPS, blit=False
)

plt.show()

# To export as a shareable video/gif instead of a live window:
#   comment out plt.show() above, then uncomment one of the lines below.
#
# GIF (requires: pip install pillow)
# anim.save("shape_story.gif", writer="pillow", fps=FPS)
#
# MP4 (requires ffmpeg installed and on PATH)
# anim.save("shape_story.mp4", writer="ffmpeg", fps=FPS)