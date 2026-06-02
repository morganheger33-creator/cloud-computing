"""
╔══════════════════════════════════════════════╗
║         VOID STRIKER  —  Arcade Shooter      ║
║                                              ║
║  Controls:                                   ║
║    WASD / Arrow Keys  — Move                 ║
║    SPACE              — Shoot                ║
║    Z                  — Missile (limited)    ║
║    P                  — Pause                ║
║    R                  — Restart (game over)  ║
╚══════════════════════════════════════════════╝

Requirements:
    pip install pygame
"""

import pygame
import random
import math
import sys
from dataclasses import dataclass, field
from typing import List, Optional

pygame.init()

# ── Constants ────────────────────────────────────────────────────────────────
W, H = 900, 700
FPS  = 60

# Palette
C_BG        = (5, 5, 20)
C_STAR1     = (80, 80, 120)
C_STAR2     = (160, 160, 200)
C_PLAYER    = (0, 220, 255)
C_PLAYER2   = (0, 120, 200)
C_BULLET    = (0, 255, 180)
C_MISSILE   = (255, 140, 0)
C_ENEMY_A   = (220, 50, 80)
C_ENEMY_B   = (180, 0, 220)
C_ENEMY_C   = (255, 180, 0)
C_BOSS      = (255, 80, 0)
C_EXPLOSION = [(255,255,200),(255,200,80),(255,120,0),(200,50,0),(80,20,0)]
C_HUD       = (0, 255, 180)
C_WHITE     = (255, 255, 255)
C_RED       = (255, 60, 60)
C_SHIELD    = (80, 200, 255)
C_POWERUP   = {
    "shield":  (80, 200, 255),
    "rapid":   (255, 220, 0),
    "missile": (255, 140, 0),
    "spread":  (0, 255, 120),
    "health":  (255, 80, 120),
}

# ── Helpers ──────────────────────────────────────────────────────────────────
def lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def draw_glow(surf, color, center, radius, alpha=60):
    s = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
    pygame.draw.circle(s, (*color, alpha), (radius, radius), radius)
    surf.blit(s, (center[0]-radius, center[1]-radius))

def angle_to(src, dst):
    dx, dy = dst[0]-src[0], dst[1]-src[1]
    return math.atan2(dy, dx)

# ── Stars ────────────────────────────────────────────────────────────────────
class StarField:
    def __init__(self, n=200):
        self.stars = [self._make() for _ in range(n)]

    def _make(self, y=None):
        speed = random.uniform(0.3, 3.0)
        return {
            "x":     random.uniform(0, W),
            "y":     random.uniform(0, H) if y is None else -2,
            "speed": speed,
            "r":     max(1, int(speed * 0.8)),
            "color": C_STAR2 if speed > 1.5 else C_STAR1,
        }

    def update(self):
        for s in self.stars:
            s["y"] += s["speed"]
            if s["y"] > H + 2:
                s.update(self._make(y=-2))
                s["x"] = random.uniform(0, W)

    def draw(self, surf):
        for s in self.stars:
            pygame.draw.circle(surf, s["color"], (int(s["x"]), int(s["y"])), s["r"])

# ── Nebula background layer ───────────────────────────────────────────────────
class Nebula:
    """Slowly drifting colour clouds for visual depth."""
    def __init__(self):
        self.clouds = []
        for _ in range(6):
            self.clouds.append({
                "x": random.uniform(0, W),
                "y": random.uniform(0, H),
                "r": random.randint(120, 240),
                "color": random.choice([(30,0,60),(0,20,60),(0,40,30)]),
                "vy": random.uniform(0.1, 0.4),
                "alpha": random.randint(18, 38),
            })

    def update(self):
        for c in self.clouds:
            c["y"] += c["vy"]
            if c["y"] - c["r"] > H + 20:
                c["y"] = -c["r"]
                c["x"] = random.uniform(0, W)

    def draw(self, surf):
        for c in self.clouds:
            draw_glow(surf, c["color"], (int(c["x"]), int(c["y"])), c["r"], c["alpha"])

# ── Particles ─────────────────────────────────────────────────────────────────
class Particle:
    __slots__ = ("x","y","vx","vy","life","max_life","color","r")

    def __init__(self, x, y, vx, vy, life, color, r=2):
        self.x, self.y   = x, y
        self.vx, self.vy = vx, vy
        self.life = self.max_life = life
        self.color = color
        self.r = r

    def update(self):
        self.x  += self.vx
        self.y  += self.vy
        self.vy += 0.06
        self.vx *= 0.97
        self.life -= 1

    def draw(self, surf):
        t   = self.life / self.max_life
        col = lerp_color((20,10,5), self.color, t)
        r   = max(1, int(self.r * t))
        s   = pygame.Surface((r*2+1, r*2+1), pygame.SRCALPHA)
        pygame.draw.circle(s, (*col, int(t*255)), (r, r), r)
        surf.blit(s, (int(self.x)-r, int(self.y)-r))


class ParticleSystem:
    def __init__(self):
        self.particles: List[Particle] = []

    def explode(self, x, y, color, n=30, speed=4):
        for _ in range(n):
            angle = random.uniform(0, 2*math.pi)
            sp    = random.uniform(0.5, speed)
            c     = lerp_color(C_EXPLOSION[random.randint(0,4)], color, random.random())
            self.particles.append(
                Particle(x, y, math.cos(angle)*sp, math.sin(angle)*sp,
                         random.randint(20, 55), c, random.randint(2,5))
            )

    def trail(self, x, y, color, n=3):
        for _ in range(n):
            self.particles.append(Particle(
                x + random.uniform(-3,3), y + random.uniform(-3,3),
                random.uniform(-0.5,0.5), random.uniform(0.5,2),
                random.randint(6,14), color, 2
            ))

    def spark(self, x, y, color, n=6):
        """Small sparks for hits that don't kill."""
        for _ in range(n):
            angle = random.uniform(0, 2*math.pi)
            sp    = random.uniform(1, 3)
            self.particles.append(
                Particle(x, y, math.cos(angle)*sp, math.sin(angle)*sp,
                         random.randint(6, 14), color, 1)
            )

    def update(self):
        self.particles = [p for p in self.particles if p.life > 0]
        for p in self.particles:
            p.update()

    def draw(self, surf):
        for p in self.particles:
            p.draw(surf)

# ── Screen-shake ──────────────────────────────────────────────────────────────
class ScreenShake:
    def __init__(self):
        self.amount = 0

    def shake(self, intensity=6):
        self.amount = max(self.amount, intensity)

    def update(self):
        if self.amount > 0:
            self.amount = max(0, self.amount - 0.8)

    def offset(self):
        if self.amount < 0.5:
            return (0, 0)
        a = int(self.amount)
        return (random.randint(-a, a), random.randint(-a, a))

# ── Bullets ───────────────────────────────────────────────────────────────────
class Bullet:
    def __init__(self, x, y, vx, vy, damage=10, color=C_BULLET, r=4, owner="player"):
        self.x, self.y   = x, y
        self.vx, self.vy = vx, vy
        self.damage = damage
        self.color  = color
        self.r      = r
        self.owner  = owner
        self.alive  = True

    def update(self):
        self.x += self.vx
        self.y += self.vy
        if not (-20 < self.x < W+20 and -20 < self.y < H+20):
            self.alive = False

    def draw(self, surf, ps: ParticleSystem):
        ps.trail(self.x, self.y, self.color, n=2)
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), self.r)
        draw_glow(surf, self.color, (int(self.x), int(self.y)), self.r+4, 50)


class Missile(Bullet):
    def __init__(self, x, y, target_getter):
        super().__init__(x, y, 0, -6, damage=70, color=C_MISSILE, r=5, owner="player")
        self.target_getter = target_getter
        self.speed         = 7
        self.turn_rate     = 0.12

    def update(self):
        target = self.target_getter()
        if target:
            desired = angle_to((self.x, self.y), (target.x, target.y))
            current = math.atan2(self.vy, self.vx)
            diff    = (desired - current + math.pi) % (2*math.pi) - math.pi
            current += diff * self.turn_rate
            self.vx  = math.cos(current) * self.speed
            self.vy  = math.sin(current) * self.speed
        super().update()

    def draw(self, surf, ps):
        ps.trail(self.x, self.y, C_MISSILE, n=5)
        pygame.draw.circle(surf, C_MISSILE, (int(self.x), int(self.y)), 5)
        draw_glow(surf, C_MISSILE, (int(self.x), int(self.y)), 12, 70)

# ── Power-ups ─────────────────────────────────────────────────────────────────
class PowerUp:
    TYPES = ["shield", "rapid", "missile", "spread", "health"]

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.vy    = 1.5
        self.kind  = random.choice(self.TYPES)
        self.color = C_POWERUP[self.kind]
        self.alive = True
        self.t     = 0

    def update(self):
        self.y += self.vy
        self.t += 1
        if self.y > H + 20:
            self.alive = False

    def draw(self, surf):
        bob = math.sin(self.t * 0.1) * 4
        cx, cy = int(self.x), int(self.y + bob)
        draw_glow(surf, self.color, (cx, cy), 20, 55)
        pygame.draw.circle(surf, self.color, (cx, cy), 12)
        pygame.draw.circle(surf, C_WHITE,    (cx, cy), 12, 2)
        font  = pygame.font.SysFont("consolas", 11, bold=True)
        label = {"shield":"SH","rapid":"RF","missile":"MS","spread":"SP","health":"HP"}[self.kind]
        txt   = font.render(label, True, C_BG)
        surf.blit(txt, txt.get_rect(center=(cx, cy)))

    @property
    def rect(self):
        return pygame.Rect(self.x-12, self.y-12, 24, 24)

# ── Enemies ───────────────────────────────────────────────────────────────────
class Enemy:
    def __init__(self, x, y, hp, speed, score, color, size):
        self.x, self.y  = float(x), float(y)
        self.hp = self.max_hp = hp
        self.speed  = speed
        self.score  = score
        self.color  = color
        self.size   = size
        self.alive  = True
        self.shoot_timer = random.randint(30, 120)
        self.t = 0

    def update(self, bullets, player):
        self.t += 1
        self._move(player)
        self.shoot_timer -= 1
        if self.shoot_timer <= 0:
            self._shoot(bullets, player)
            self.shoot_timer = self._shoot_interval()
        if self.y > H + self.size + 10:
            self.alive = False

    def _move(self, player):
        self.y += self.speed

    def _shoot(self, bullets, player):
        ang = angle_to((self.x, self.y), (player.x, player.y))
        spd = 3.5
        bullets.append(Bullet(self.x, self.y,
                               math.cos(ang)*spd, math.sin(ang)*spd,
                               damage=10, color=self.color, r=3, owner="enemy"))

    def _shoot_interval(self):
        return random.randint(80, 160)

    def hit(self, dmg):
        self.hp -= dmg
        if self.hp <= 0:
            self.alive = False
            return True
        return False

    def draw(self, surf):
        self._draw_shape(surf)
        if self.hp < self.max_hp:
            bw = self.size * 2
            bx = int(self.x) - self.size
            by = int(self.y) - self.size - 8
            pygame.draw.rect(surf, (80,0,0), (bx, by, bw, 4))
            pygame.draw.rect(surf, C_RED,    (bx, by, int(bw * self.hp / self.max_hp), 4))

    def _draw_shape(self, surf):
        pts = self._get_points()
        pygame.draw.polygon(surf, self.color, pts)
        pygame.draw.polygon(surf, C_WHITE, pts, 1)
        draw_glow(surf, self.color, (int(self.x), int(self.y)), self.size, 40)

    def _get_points(self):
        s  = self.size
        cx, cy = int(self.x), int(self.y)
        return [(cx, cy+s), (cx-s, cy-s), (cx+s, cy-s)]

    @property
    def rect(self):
        s = self.size
        return pygame.Rect(self.x-s, self.y-s, s*2, s*2)


class EnemyA(Enemy):   # Drifter — simple downward
    def __init__(self, x, y):
        super().__init__(x, y, hp=30, speed=2.0, score=100, color=C_ENEMY_A, size=16)
        self.drift = random.uniform(-0.4, 0.4)

    def _move(self, player):
        self.x += self.drift + math.sin(self.t * 0.05) * 0.5
        self.y += self.speed

    def _get_points(self):
        cx, cy = int(self.x), int(self.y)
        s = self.size
        return [(cx, cy+s), (cx-s, cy-s//2), (cx, cy-s), (cx+s, cy-s//2)]


class EnemyB(Enemy):   # Hunter — tracks player X
    def __init__(self, x, y):
        super().__init__(x, y, hp=55, speed=1.6, score=200, color=C_ENEMY_B, size=18)

    def _move(self, player):
        dx = player.x - self.x
        self.x += max(-2.2, min(2.2, dx * 0.05))
        self.y += self.speed

    def _shoot_interval(self):
        return random.randint(50, 100)

    def _get_points(self):
        cx, cy = int(self.x), int(self.y)
        s = self.size
        return [(cx, cy-s), (cx+s, cy), (cx+s//2, cy+s), (cx-s//2, cy+s), (cx-s, cy)]


class EnemyC(Enemy):   # Gunship — spread shots
    def __init__(self, x, y):
        super().__init__(x, y, hp=80, speed=1.0, score=350, color=C_ENEMY_C, size=22)

    def _shoot(self, bullets, player):
        for offset in (-20, 0, 20):
            ang = angle_to((self.x, self.y), (player.x + offset, player.y))
            spd = 3.0
            bullets.append(Bullet(self.x, self.y,
                                   math.cos(ang)*spd, math.sin(ang)*spd,
                                   damage=8, color=C_ENEMY_C, r=3, owner="enemy"))

    def _shoot_interval(self):
        return random.randint(100, 180)

    def _get_points(self):
        cx, cy = int(self.x), int(self.y)
        s = self.size
        return [(cx, cy-s), (cx+s, cy+s//2), (cx+s//2, cy+s),
                (cx-s//2, cy+s), (cx-s, cy+s//2)]


class EnemyD(Enemy):   # Swooper — dives at player then retreats
    def __init__(self, x, y):
        super().__init__(x, y, hp=45, speed=0.8, score=250, color=(100,255,100), size=16)
        self.diving  = False
        self.dive_vy = 0.0
        self.dive_vx = 0.0
        self.retreat = False

    def _move(self, player):
        if not self.diving and not self.retreat and self.y > 0 and self.t % 120 == 80:
            self.diving  = True
            ang          = angle_to((self.x, self.y), (player.x, player.y))
            self.dive_vx = math.cos(ang) * 5
            self.dive_vy = math.sin(ang) * 5
        if self.diving:
            self.x += self.dive_vx
            self.y += self.dive_vy
            if self.y > H * 0.75 or self.t % 120 == 110:
                self.diving  = False
                self.retreat = True
                self.dive_vy = -4
                self.dive_vx = 0
        elif self.retreat:
            self.y += self.dive_vy
            if self.y < -self.size:
                self.alive = False
        else:
            self.x += math.sin(self.t * 0.04) * 1.5
            self.y += self.speed

    def _get_points(self):
        cx, cy = int(self.x), int(self.y)
        s = self.size
        return [(cx, cy-s), (cx+s, cy+s), (cx, cy+s//2), (cx-s, cy+s)]


class Boss(Enemy):
    PHASES = 3

    def __init__(self, wave):
        super().__init__(W//2, -80,
                         hp=700 + wave*120, speed=0.6,
                         score=2500, color=C_BOSS, size=52)
        self.phase         = 1
        self.entry         = True
        self.target_y      = 110
        self.shoot_patterns = 0
        self.angle_offset  = 0

    def _move(self, player):
        if self.entry:
            self.y += 1.8
            if self.y >= self.target_y:
                self.entry = False
        else:
            self.x += math.sin(self.t * 0.015) * 2.5
            self.x  = max(80, min(W-80, self.x))

        if self.hp < self.max_hp * 0.33 and self.phase < 3:
            self.phase = 3; self.speed = 1.3
        elif self.hp < self.max_hp * 0.66 and self.phase < 2:
            self.phase = 2; self.speed = 1.0

    def _shoot(self, bullets, player):
        self.shoot_patterns += 1
        if self.phase == 1:
            for i in range(8):
                ang = 2*math.pi*i/8 + self.angle_offset
                bullets.append(Bullet(self.x, self.y, math.cos(ang)*3, math.sin(ang)*3,
                                       damage=12, color=C_BOSS, r=5, owner="enemy"))
        elif self.phase == 2:
            ang_p = angle_to((self.x, self.y), (player.x, player.y))
            for offset in range(-2, 3):
                ang = ang_p + offset * 0.2
                bullets.append(Bullet(self.x, self.y, math.cos(ang)*4, math.sin(ang)*4,
                                       damage=15, color=C_BOSS, r=5, owner="enemy"))
            for i in range(12):
                ang = 2*math.pi*i/12 + self.angle_offset
                bullets.append(Bullet(self.x, self.y, math.cos(ang)*2, math.sin(ang)*2,
                                       damage=10, color=C_ENEMY_A, r=4, owner="enemy"))
        elif self.phase == 3:
            for i in range(16):
                ang = 2*math.pi*i/16 + self.angle_offset*3
                spd = 2.5 + (i % 3) * 0.5
                bullets.append(Bullet(self.x, self.y, math.cos(ang)*spd, math.sin(ang)*spd,
                                       damage=18, color=(255,50,200), r=5, owner="enemy"))
        self.angle_offset += 0.3

    def _shoot_interval(self):
        return {1:80, 2:55, 3:35}[self.phase]

    def _draw_shape(self, surf):
        cx, cy = int(self.x), int(self.y)
        s = self.size
        phase_color = [C_BOSS, (255,150,0), (255,50,200)][self.phase-1]
        draw_glow(surf, phase_color, (cx, cy), s+22, 55)
        pts = [
            (cx, cy-s), (cx+s*0.6, cy-s*0.4), (cx+s, cy+s*0.3),
            (cx+s*0.4, cy+s), (cx-s*0.4, cy+s), (cx-s, cy+s*0.3),
            (cx-s*0.6, cy-s*0.4)
        ]
        pts = [(int(p[0]), int(p[1])) for p in pts]
        pygame.draw.polygon(surf, phase_color, pts)
        pygame.draw.polygon(surf, C_WHITE, pts, 2)
        pulse = int(abs(math.sin(self.t * 0.05)) * 14)
        pygame.draw.circle(surf, C_WHITE, (cx, cy), 16 + pulse, 3)
        for i in range(self.phase):
            pygame.draw.circle(surf, C_WHITE, (cx - 20 + i*20, cy), 5)

    @property
    def rect(self):
        s = self.size
        return pygame.Rect(self.x-s, self.y-s, s*2, s*2)

# ── Player ────────────────────────────────────────────────────────────────────
class Player:
    INVULN_FRAMES = 90

    def __init__(self):
        self.x, self.y  = W//2, H - 90
        self.speed      = 5
        self.hp         = 100
        self.max_hp     = 100
        self.shield     = 0
        self.missiles   = 3
        self.rapid      = 0
        self.spread     = 0
        self.shoot_cd   = 0
        self.invuln     = 0
        self.score      = 0
        self.alive      = True
        self.t          = 0

    @property
    def rect(self):
        return pygame.Rect(self.x-14, self.y-16, 28, 32)

    def handle_input(self, keys, bullets, enemies):
        dx = dy = 0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += 1
        if keys[pygame.K_UP]    or keys[pygame.K_w]: dy -= 1
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: dy += 1
        if dx and dy:
            dx *= 0.707; dy *= 0.707
        self.x = max(18, min(W-18, self.x + dx * self.speed))
        self.y = max(18, min(H-18, self.y + dy * self.speed))

        if keys[pygame.K_SPACE] and self.shoot_cd <= 0:
            self._fire(bullets)
            self.shoot_cd = 7 if self.rapid > 0 else 14

    def fire_missile(self, bullets, enemies):
        if self.missiles <= 0:
            return
        self.missiles -= 1
        def get_target():
            alive = [e for e in enemies if e.alive]
            if not alive: return None
            return min(alive, key=lambda e: math.hypot(e.x-self.x, e.y-self.y))
        bullets.append(Missile(self.x, self.y - 10, get_target))

    def _fire(self, bullets):
        spd = 14
        if self.spread > 0:
            for angle_deg in (-20, -10, 0, 10, 20):
                ang = math.radians(angle_deg - 90)
                bullets.append(Bullet(self.x, self.y-10,
                                       math.cos(ang)*spd, math.sin(ang)*spd,
                                       damage=12, color=C_BULLET, r=4, owner="player"))
        else:
            bullets.append(Bullet(self.x-6, self.y-10, 0, -spd, damage=20, color=C_BULLET, r=4, owner="player"))
            bullets.append(Bullet(self.x+6, self.y-10, 0, -spd, damage=20, color=C_BULLET, r=4, owner="player"))

    def update(self):
        self.t += 1
        if self.shoot_cd > 0: self.shoot_cd -= 1
        if self.invuln > 0:   self.invuln   -= 1
        if self.rapid  > 0:   self.rapid    -= 1
        if self.spread > 0:   self.spread   -= 1

    def take_damage(self, dmg):
        if self.invuln > 0:
            return
        if self.shield > 0:
            self.shield -= dmg
            if self.shield < 0:
                self.hp    += self.shield
                self.shield = 0
        else:
            self.hp -= dmg
        self.invuln = self.INVULN_FRAMES
        if self.hp <= 0:
            self.alive = False

    def apply_powerup(self, kind):
        if kind == "shield":
            self.shield = min(self.shield + 60, 100)
        elif kind == "rapid":
            self.rapid  = 300
        elif kind == "missile":
            self.missiles = min(self.missiles + 3, 9)
        elif kind == "spread":
            self.spread = 300
        elif kind == "health":
            self.hp = min(self.hp + 30, self.max_hp)

    def draw(self, surf, ps):
        ps.trail(self.x, self.y + 16, C_PLAYER2, n=4)
        if self.invuln > 0 and self.t % 6 < 3:
            return
        cx, cy = int(self.x), int(self.y)
        draw_glow(surf, C_PLAYER, (cx, cy), 26, 40)
        pts = [(cx, cy-18), (cx-14, cy+14), (cx, cy+7), (cx+14, cy+14)]
        pygame.draw.polygon(surf, C_PLAYER2, pts)
        pygame.draw.polygon(surf, C_PLAYER,  pts, 2)
        pygame.draw.circle(surf, C_WHITE,  (cx, cy-8), 5)
        pygame.draw.circle(surf, C_PLAYER, (cx, cy-8), 5, 1)
        if self.shield > 0:
            alpha = int(180 * self.shield / 100)
            draw_glow(surf, C_SHIELD, (cx, cy), 22, alpha)
            pygame.draw.circle(surf, C_SHIELD, (cx, cy), 22, 2)
        if self.rapid  > 0: draw_glow(surf, (255,220,0), (cx, cy), 28, 30)
        if self.spread > 0: draw_glow(surf, (0,255,120), (cx, cy), 28, 30)

# ── HUD ───────────────────────────────────────────────────────────────────────
class HUD:
    def __init__(self):
        self.font_big   = pygame.font.SysFont("consolas", 28, bold=True)
        self.font_mid   = pygame.font.SysFont("consolas", 18, bold=True)
        self.font_small = pygame.font.SysFont("consolas", 14)
        self.wave_msg   = ""
        self.wave_msg_t = 0

    def show_wave(self, text, duration=160):
        self.wave_msg   = text
        self.wave_msg_t = duration

    def draw(self, surf, player, wave, boss_frac):
        # Score
        score_txt = self.font_big.render(f"{player.score:08d}", True, C_HUD)
        surf.blit(score_txt, score_txt.get_rect(center=(W//2, 16)))

        # HP bar
        self._bar(surf, 14, H-30, 200, 16, player.hp/player.max_hp, C_RED, "HP")
        if player.shield > 0:
            self._bar(surf, 14, H-50, 200, 10, player.shield/100, C_SHIELD, "SH")

        # Missiles
        m_txt = self.font_mid.render(f"MSL {player.missiles}", True, C_MISSILE)
        surf.blit(m_txt, (W-140, H-32))

        # Wave
        w_txt = self.font_mid.render(f"WAVE {wave}", True, C_HUD)
        surf.blit(w_txt, (W-120, 10))

        # Powerup timers
        y_off = H - 80
        if player.rapid > 0:
            self._bar(surf, 14, y_off, 140, 8, player.rapid/300, (255,220,0), "RAPID")
            y_off -= 20
        if player.spread > 0:
            self._bar(surf, 14, y_off, 140, 8, player.spread/300, (0,255,120), "SPREAD")

        # Wave announcement
        if self.wave_msg_t > 0:
            alpha = min(255, self.wave_msg_t * 4)
            txt   = self.font_big.render(self.wave_msg, True, C_WHITE)
            s     = pygame.Surface(txt.get_size(), pygame.SRCALPHA)
            s.fill((0,0,0,0))
            s.blit(txt, (0,0))
            s.set_alpha(alpha)
            surf.blit(s, (W//2 - txt.get_width()//2, H//2 - 60))
            self.wave_msg_t -= 1

        # Boss HP bar
        if boss_frac is not None:
            bw = W - 100
            bx, by = 50, 50
            pygame.draw.rect(surf, (60,0,0),   (bx, by, bw, 18), border_radius=4)
            pygame.draw.rect(surf, C_BOSS,     (bx, by, int(bw * boss_frac), 18), border_radius=4)
            pygame.draw.rect(surf, C_WHITE,    (bx, by, bw, 18), 2, border_radius=4)
            surf.blit(self.font_small.render("BOSS", True, C_WHITE), (bx+4, by+1))

    def _bar(self, surf, x, y, w, h, pct, color, label=""):
        pygame.draw.rect(surf, (30,30,50), (x, y, w, h), border_radius=3)
        fw = max(0, int(w * pct))
        if fw:
            pygame.draw.rect(surf, color, (x, y, fw, h), border_radius=3)
        pygame.draw.rect(surf, (100,100,120), (x, y, w, h), 1, border_radius=3)
        if label:
            surf.blit(self.font_small.render(label, True, C_WHITE), (x+w+6, y-1))

# ── Wave Manager ──────────────────────────────────────────────────────────────
class WaveManager:
    def __init__(self):
        self.wave           = 0
        self.enemies_queue: List[Enemy] = []
        self.spawn_timer    = 0
        self.spawn_rate     = 40
        self.boss: Optional[Boss] = None
        self.between_waves  = True
        self.between_timer  = 180

    def start_next_wave(self, hud: HUD):
        self.wave += 1
        self.between_waves = False
        is_boss_wave = self.wave % 5 == 0
        if is_boss_wave:
            self.boss           = Boss(self.wave)
            self.enemies_queue  = []
            hud.show_wave(f"⚠ WAVE {self.wave} — BOSS ⚠", 200)
        else:
            self.boss           = None
            self.enemies_queue  = self._build_wave()
            hud.show_wave(f"WAVE {self.wave}", 120)
        self.spawn_timer = 0
        self.spawn_rate  = max(12, 40 - self.wave * 3)

    def _build_wave(self) -> List[Enemy]:
        enemies = []
        n = 6 + self.wave * 2
        for _ in range(n):
            x = random.uniform(40, W-40)
            y = random.uniform(-300, -40)
            r = random.random()
            if self.wave < 2:
                enemies.append(EnemyA(x, y))
            elif self.wave < 4:
                enemies.append(EnemyA(x, y) if r < 0.6 else EnemyB(x, y))
            else:
                if r < 0.35:
                    enemies.append(EnemyA(x, y))
                elif r < 0.60:
                    enemies.append(EnemyB(x, y))
                elif r < 0.80:
                    enemies.append(EnemyC(x, y))
                else:
                    enemies.append(EnemyD(x, y))
        return enemies

    def update(self, enemies: List[Enemy], hud: HUD):
        if self.between_waves:
            self.between_timer -= 1
            if self.between_timer <= 0:
                self.start_next_wave(hud)
                self.between_timer = 180
            return

        if self.boss:
            if self.boss not in enemies:
                enemies.append(self.boss)
            if not self.boss.alive:
                self.boss = None
                self._wave_done()
            return

        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_rate and self.enemies_queue:
            enemies.append(self.enemies_queue.pop(0))
            self.spawn_timer = 0

        if not self.enemies_queue and not [e for e in enemies if e.alive]:
            self._wave_done()

    def _wave_done(self):
        self.between_waves = True
        self.between_timer = 160

    def boss_hp_fraction(self):
        if self.boss and self.boss.alive:
            return self.boss.hp / self.boss.max_hp
        return None

# ── Game ──────────────────────────────────────────────────────────────────────
class Game:
    def __init__(self):
        self.screen     = pygame.display.set_mode((W, H))
        pygame.display.set_caption("VOID STRIKER")
        self.clock      = pygame.time.Clock()
        self.font_title = pygame.font.SysFont("consolas", 48, bold=True)
        self.font_mid   = pygame.font.SysFont("consolas", 22, bold=True)
        self.shake      = ScreenShake()
        self.reset()

    def reset(self):
        self.player   = Player()
        self.bullets: List[Bullet]  = []
        self.enemies: List[Enemy]   = []
        self.powerups: List[PowerUp] = []
        self.ps       = ParticleSystem()
        self.stars    = StarField()
        self.nebula   = Nebula()
        self.hud      = HUD()
        self.waves    = WaveManager()
        self.shake    = ScreenShake()
        self.paused   = False
        self.game_over = False
        self.running  = True

    def run(self):
        while self.running:
            self.handle_events()
            if not self.paused and not self.game_over:
                self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p and not self.game_over:
                    self.paused = not self.paused
                elif event.key == pygame.K_z and not self.paused and not self.game_over:
                    self.player.fire_missile(self.bullets, self.enemies)
                elif event.key == pygame.K_r and self.game_over:
                    self.reset()
                elif event.key == pygame.K_ESCAPE:
                    self.running = False

    def update(self):
        keys = pygame.key.get_pressed()
        self.stars.update()
        self.nebula.update()
        self.shake.update()
        self.player.handle_input(keys, self.bullets, self.enemies)
        self.player.update()
        self.waves.update(self.enemies, self.hud)
        self.hud.wave_msg_t = max(0, self.hud.wave_msg_t)

        for b in self.bullets:
            b.update()
        self.bullets = [b for b in self.bullets if b.alive]

        for e in self.enemies:
            if e.alive:
                e.update(self.bullets, self.player)
        self.enemies = [e for e in self.enemies if e.alive]

        for p in self.powerups:
            p.update()
        self.powerups = [p for p in self.powerups if p.alive]

        self.ps.update()

        # Player bullets vs enemies
        for b in self.bullets:
            if b.owner != "player": continue
            for e in self.enemies:
                if not e.alive: continue
                if e.rect.collidepoint(b.x, b.y):
                    killed = e.hit(b.damage)
                    b.alive = False
                    if killed:
                        self.shake.shake(7)
                        self.ps.explode(e.x, e.y, e.color, n=45, speed=5)
                        self.player.score += e.score
                        if random.random() < 0.22:
                            self.powerups.append(PowerUp(e.x, e.y))
                    else:
                        self.ps.spark(e.x, e.y, e.color, n=6)
                    break

        # Enemy bullets vs player
        for b in self.bullets:
            if b.owner != "enemy": continue
            if self.player.rect.collidepoint(b.x, b.y):
                self.player.take_damage(b.damage)
                b.alive = False
                self.shake.shake(4)
                self.ps.explode(self.player.x, self.player.y, C_RED, n=20, speed=3)

        # Enemy body collision
        for e in self.enemies:
            if e.rect.colliderect(self.player.rect):
                self.player.take_damage(20)
                self.shake.shake(6)
                self.ps.explode(e.x, e.y, e.color, n=30, speed=4)
                e.alive = False

        # Powerup pickup
        for p in self.powerups:
            if p.rect.colliderect(self.player.rect):
                self.player.apply_powerup(p.kind)
                p.alive = False
                self.ps.explode(p.x, p.y, p.color, n=15, speed=2)

        if not self.player.alive:
            self.game_over = True

    def draw(self):
        ox, oy = self.shake.offset()
        # Draw everything to a surface then blit with shake offset
        canvas = pygame.Surface((W, H))
        canvas.fill(C_BG)
        self.nebula.draw(canvas)
        self.stars.draw(canvas)
        self.ps.draw(canvas)
        for p in self.powerups:
            p.draw(canvas)
        for e in self.enemies:
            e.draw(canvas)
        for b in self.bullets:
            b.draw(canvas, self.ps)
        self.player.draw(canvas, self.ps)

        boss_frac = self.waves.boss_hp_fraction()
        self.hud.draw(canvas, self.player, self.waves.wave, boss_frac)

        if self.paused:
            self._overlay(canvas, "PAUSED", "P to resume")
        if self.game_over:
            self._overlay(canvas, "GAME OVER", f"Score: {self.player.score:08d}    R to restart")

        self.screen.fill(C_BG)
        self.screen.blit(canvas, (ox, oy))
        pygame.display.flip()

    def _overlay(self, surf, title, sub):
        s = pygame.Surface((W, H), pygame.SRCALPHA)
        s.fill((0, 0, 0, 160))
        surf.blit(s, (0, 0))
        t  = self.font_title.render(title, True, C_HUD)
        st = self.font_mid.render(sub,   True, C_WHITE)
        surf.blit(t,  t.get_rect(center=(W//2, H//2 - 30)))
        surf.blit(st, st.get_rect(center=(W//2, H//2 + 20)))


# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    Game().run()
