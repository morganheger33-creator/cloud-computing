"""
Beating Heart Animation
------------------------
Draws a heart shape using a parametric equation and pulses it
like a heartbeat using a scale factor that follows a "lub-dub" rhythm.

Run with:
    python heartbeat_animation.py

Requirements:
    pip install matplotlib numpy
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# ---- Heart shape (parametric equation) ----
def heart_shape(t, scale=1.0):
    x = 16 * np.sin(t) ** 3
    y = (13 * np.cos(t)
         - 5 * np.cos(2 * t)
         - 2 * np.cos(3 * t)
         - np.cos(4 * t))
    return x * scale, y * scale


# ---- Heartbeat pulse pattern (lub-dub) ----
def beat_scale(frame, total_frames_per_beat=40):
    # Position within the current beat cycle (0 to 1)
    phase = (frame % total_frames_per_beat) / total_frames_per_beat

    # Two quick pulses ("lub" then "dub"), then a rest period
    if phase < 0.12:
        # lub - quick expand
        return 1.0 + 0.25 * np.sin(phase / 0.12 * np.pi)
    elif phase < 0.24:
        # relax slightly
        p = (phase - 0.12) / 0.12
        return 1.0 + 0.10 * np.sin(p * np.pi)
    elif phase < 0.34:
        # dub - second smaller pulse
        p = (phase - 0.24) / 0.10
        return 1.0 + 0.15 * np.sin(p * np.pi)
    else:
        # rest period between beats
        return 1.0


# ---- Set up the figure ----
fig, ax = plt.subplots(figsize=(6, 6))
fig.patch.set_facecolor("black")
ax.set_facecolor("black")
ax.set_xlim(-22, 22)
ax.set_ylim(-20, 18)
ax.axis("off")
ax.set_aspect("equal")

t = np.linspace(0, 2 * np.pi, 500)

line, = ax.plot([], [], color="red", linewidth=2)
fill = ax.fill([], [], color="crimson", alpha=0.8)[0]

title = ax.text(0, 15, "", color="white", fontsize=16,
                 ha="center", va="center", fontweight="bold")

BEAT_LENGTH = 40  # frames per heartbeat cycle


def init():
    line.set_data([], [])
    fill.set_xy(np.empty((0, 2)))
    return line, fill, title


def animate(frame):
    scale = beat_scale(frame, BEAT_LENGTH)
    x, y = heart_shape(t, scale=scale)

    line.set_data(x, y)
    fill.set_xy(np.column_stack([x, y]))

    # Glow/color shifts slightly with the beat intensity
    intensity = min(1.0, (scale - 1.0) * 4 + 0.6)
    fill.set_color((1.0, 0.0, intensity * 0.3))

    return line, fill, title


anim = FuncAnimation(
    fig, animate, init_func=init,
    frames=400, interval=20, blit=True
)

plt.show()

# To save as a gif instead of showing a live window, comment out plt.show()
# above and uncomment the line below (requires pillow: pip install pillow)
# anim.save("heartbeat.gif", writer="pillow", fps=30)