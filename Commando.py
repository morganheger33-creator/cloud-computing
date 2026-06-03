"""
COMMANDO STRIKE  —  Top-down action shooter (no sound)
Requires: pip install pygame
Run:      python commando_strike.py
"""

import pygame, sys, math, random
from dataclasses import dataclass, field
from typing import List, Optional

# ─────────────────────────── constants ────────────────────────────────────────
W, H        = 1024, 768
TILE        = 48
MAP_COLS    = 32
MAP_ROWS    = 28
MAP_W       = MAP_COLS * TILE
MAP_H       = MAP_ROWS * TILE
FPS         = 60

# colours
C_SKY       = (40,  45,  30)
C_GRASS     = (55,  80,  35)
C_GRASS2    = (50,  72,  30)
C_DIRT      = (90,  70,  45)
C_ROAD      = (70,  65,  55)
C_WALL      = (110, 100,  80)
C_WALL_D    = (80,  72,  55)
C_WALL_S    = (140, 130, 105)
C_WATER     = (30,  80, 140)
C_WATER2    = (35,  90, 155)
C_WHITE     = (255, 255, 255)
C_BLACK     = (0,   0,   0)
C_RED       = (220,  50,  50)
C_GREEN     = (50,  200,  80)
C_YELLOW    = (255, 210,  30)
C_ORANGE    = (255, 140,  20)
C_CYAN      = (80,  220, 220)
C_HUD       = (15,  18,  12)
C_HUDA      = (25,  32,  18)
C_AMMO      = (255, 200,  40)
C_SHADOW    = (0,   0,   0, 90)

# tile types
T_GRASS = 0
T_WALL  = 1
T_ROAD  = 2
T_WATER = 3
T_DIRT  = 4

# weapon defs  name, damage, fire_rate(frames), bullet_speed, spread, mag, color, auto
WEAPONS = [
    dict(name="RIFLE",    damage=25, rate=18, speed=14, spread=2,  mag=30,  col=(255,230, 80), auto=False),
    dict(name="SHOTGUN",  damage=18, rate=35, speed=11, spread=18, mag=8,   col=(255,160, 40), auto=False),
    dict(name="SMG",      damage=12, rate=6,  speed=13, spread=6,  mag=45,  col=(180,255,100), auto=True),
    dict(name="GRENADE",  damage=80, rate=50, speed=7,  spread=0,  mag=5,   col=(255, 80, 40), auto=False),
    dict(name="SNIPER",   damage=99, rate=60, speed=20, spread=0,  mag=5,   col=(100,220,255), auto=False),
]

# ─────────────────────────── map generation ───────────────────────────────────
def make_map():
    grid = [[T_GRASS]*MAP_COLS for _ in range(MAP_ROWS)]

    # roads
    for c in range(MAP_COLS): grid[7][c]  = T_ROAD
    for c in range(MAP_COLS): grid[20][c] = T_ROAD
    for r in range(MAP_ROWS): grid[r][8]  = T_ROAD
    for r in range(MAP_ROWS): grid[r][22] = T_ROAD

    # dirt patches
    for _ in range(40):
        r = random.randint(1, MAP_ROWS-2)
        c = random.randint(1, MAP_COLS-2)
        for dr in range(-1,2):
            for dc in range(-1,2):
                nr,nc = r+dr, c+dc
                if 0<=nr<MAP_ROWS and 0<=nc<MAP_COLS and grid[nr][nc]==T_GRASS:
                    grid[nr][nc] = T_DIRT

    # water lake
    for r in range(3,7):
        for c in range(14,20):
            grid[r][c] = T_WATER

    # wall structures (buildings)
    buildings = [
        (2, 2, 5, 6), (2, 10, 5, 14), (2, 24, 5, 28),
        (9, 2, 14, 6), (9, 10, 14, 14), (9, 24, 14, 28),
        (9, 16, 13, 20),
        (22, 2, 27, 6), (22, 10, 27, 14), (22, 16, 27, 20), (22, 24, 27, 28),
    ]
    doors = {}
    for (r1,c1,r2,c2) in buildings:
        for r in range(r1, r2):
            for c in range(c1, c2):
                grid[r][c] = T_WALL
        # hollow interior
        for r in range(r1+1, r2-1):
            for c in range(c1+1, c2-1):
                grid[r][c] = T_DIRT
        # door gap on south wall
        mid_c = (c1+c2)//2
        grid[r2-1][mid_c] = T_DIRT

    return grid

MAP = make_map()

def tile_at(wx, wy):
    c = int(wx // TILE)
    r = int(wy // TILE)
    if 0 <= r < MAP_ROWS and 0 <= c < MAP_COLS:
        return MAP[r][c]
    return T_WALL

def is_solid(wx, wy):
    t = tile_at(wx, wy)
    return t == T_WALL or t == T_WATER

def is_solid_rect(rect):
    corners = [
        (rect.left+4,  rect.top+4),
        (rect.right-4, rect.top+4),
        (rect.left+4,  rect.bottom-4),
        (rect.right-4, rect.bottom-4),
    ]
    return any(is_solid(x, y) for x, y in corners)

# ─────────────────────────── camera ───────────────────────────────────────────
class Camera:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0

    def update(self, target_x, target_y):
        self.x += (target_x - W//2 - self.x) * 0.12
        self.y += (target_y - H//2 - self.y) * 0.12
        self.x = max(0, min(MAP_W - W, self.x))
        self.y = max(0, min(MAP_H - H, self.y))

    def apply(self, wx, wy):
        return wx - self.x, wy - self.y

    def world(self, sx, sy):
        return sx + self.x, sy + self.y

# ─────────────────────────── particles ────────────────────────────────────────
class Particle:
    __slots__ = ('x','y','vx','vy','life','max_life','col','r')
    def __init__(self, x, y, col, speed=4, life=30, r=4):
        self.x, self.y = x, y
        a = random.uniform(0, math.tau)
        s = random.uniform(speed*0.4, speed)
        self.vx, self.vy = math.cos(a)*s, math.sin(a)*s
        self.life = self.max_life = life + random.randint(-8,8)
        self.col = col
        self.r = r

    def update(self):
        self.x += self.vx; self.y += self.vy
        self.vx *= 0.88;   self.vy *= 0.88
        self.life -= 1

    def draw(self, surf, cam):
        sx, sy = cam.apply(self.x, self.y)
        if -20 < sx < W+20 and -20 < sy < H+20:
            alpha_r = max(1, int(self.r * self.life / self.max_life))
            pygame.draw.circle(surf, self.col, (int(sx), int(sy)), alpha_r)

def explode(particles, x, y, col, n=28, speed=5, life=35, r=6):
    for _ in range(n):
        particles.append(Particle(x, y, col, speed, life, r))

# ─────────────────────────── bullet ───────────────────────────────────────────
class Bullet:
    __slots__ = ('x','y','vx','vy','dmg','owner','alive','col','is_grenade','timer')
    def __init__(self, x, y, angle, speed, dmg, owner, col, is_grenade=False):
        self.x, self.y = x, y
        self.vx = math.cos(angle)*speed
        self.vy = math.sin(angle)*speed
        self.dmg = dmg; self.owner = owner
        self.alive = True; self.col = col
        self.is_grenade = is_grenade
        self.timer = 55 if is_grenade else 999

    def update(self):
        self.x += self.vx; self.y += self.vy
        self.timer -= 1
        if self.timer <= 0:
            self.alive = False
        if is_solid(self.x, self.y):
            self.alive = False

    def rect(self):
        return pygame.Rect(self.x-5, self.y-5, 10, 10)

    def draw(self, surf, cam):
        sx, sy = cam.apply(self.x, self.y)
        if self.is_grenade:
            pygame.draw.circle(surf, C_ORANGE, (int(sx),int(sy)), 6)
            pygame.draw.circle(surf, C_YELLOW, (int(sx),int(sy)), 3)
        else:
            ex = sx - self.vx*3; ey = sy - self.vy*3
            pygame.draw.line(surf, self.col, (int(ex),int(ey)), (int(sx),int(sy)), 3)
            pygame.draw.circle(surf, C_WHITE, (int(sx),int(sy)), 2)

# ─────────────────────────── drop items ───────────────────────────────────────
class Drop:
    def __init__(self, x, y, kind):
        self.x, self.y = x, y
        self.kind = kind   # 'health' | weapon index
        self.alive = True
        self.bob = random.uniform(0, math.tau)

    def update(self):
        self.bob += 0.07

    def draw(self, surf, cam):
        sx, sy = cam.apply(self.x, self.y + math.sin(self.bob)*3)
        if self.kind == 'health':
            pygame.draw.rect(surf, C_RED,   (sx-10, sy-10, 20, 20), border_radius=4)
            pygame.draw.rect(surf, C_WHITE, (sx-2,  sy-8,   4, 16))
            pygame.draw.rect(surf, C_WHITE, (sx-8,  sy-2,  16,  4))
        else:
            w = WEAPONS[self.kind]
            pygame.draw.rect(surf, (60,60,40), (sx-12, sy-8, 24, 16), border_radius=3)
            pygame.draw.rect(surf, w['col'],   (sx-10, sy-6, 20, 12), border_radius=2)
            lbl = pygame.font.SysFont('consolas',9,True).render(w['name'][:3],True,C_BLACK)
            surf.blit(lbl, (sx-lbl.get_width()//2, sy-lbl.get_height()//2))

    def rect(self):
        return pygame.Rect(self.x-14, self.y-14, 28, 28)

# ─────────────────────────── enemy ────────────────────────────────────────────
ENEMY_TYPES = [
    dict(name='GRUNT',   hp=40,  speed=1.4, dmg=10, rate=80,  col=(160, 60, 60), size=14, score=50),
    dict(name='HEAVY',   hp=100, speed=0.8, dmg=20, rate=100, col=(100, 40,140), size=18, score=120),
    dict(name='SNIPER',  hp=30,  speed=0.6, dmg=40, rate=120, col=(40, 140, 80), size=13, score=100),
    dict(name='RUSHER',  hp=25,  speed=2.4, dmg=8,  rate=50,  col=(200,120, 30), size=12, score=75),
]

class Enemy:
    def __init__(self, x, y, etype=0):
        self.x, self.y = float(x), float(y)
        t = ENEMY_TYPES[etype]
        self.hp = self.max_hp = t['hp']
        self.speed = t['speed']
        self.dmg   = t['dmg']
        self.rate  = t['rate']
        self.col   = t['col']
        self.size  = t['size']
        self.score = t['score']
        self.name  = t['name']
        self.cool  = random.randint(0, self.rate)
        self.alive = True
        self.angle = 0.0
        self.state = 'patrol'
        self.patrol_target = (x + random.randint(-200,200), y + random.randint(-200,200))
        self.alert_timer = 0
        self.hit_flash   = 0

    def update(self, player, bullets, particles, drops):
        if not self.alive: return
        if self.hit_flash > 0: self.hit_flash -= 1

        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)
        sight = 280 if self.name=='SNIPER' else 220

        if dist < sight:
            self.state = 'chase'
            self.alert_timer = 180
        elif self.alert_timer > 0:
            self.alert_timer -= 1
        else:
            self.state = 'patrol'

        if self.state == 'chase':
            if dist > 80:
                nx, ny = dx/dist, dy/dist
                newx = self.x + nx*self.speed
                newy = self.y + ny*self.speed
                tr = pygame.Rect(newx-self.size, newy-self.size, self.size*2, self.size*2)
                if not is_solid_rect(tr):
                    self.x, self.y = newx, newy
            self.angle = math.atan2(dy, dx)
            self.cool -= 1
            if self.cool <= 0 and dist < sight:
                spread = random.uniform(-0.12, 0.12)
                b = Bullet(self.x, self.y, self.angle+spread, 10, self.dmg, 'enemy',
                           (255,80,80))
                bullets.append(b)
                self.cool = self.rate
        else:
            px, py = self.patrol_target
            pdx = px-self.x; pdy = py-self.y
            pd = math.hypot(pdx, pdy)
            if pd < 10:
                self.patrol_target = (
                    self.x + random.randint(-250,250),
                    self.y + random.randint(-250,250)
                )
            else:
                nx,ny = pdx/pd, pdy/pd
                newx = self.x + nx*self.speed*0.5
                newy = self.y + ny*self.speed*0.5
                tr = pygame.Rect(newx-self.size, newy-self.size, self.size*2, self.size*2)
                if not is_solid_rect(tr):
                    self.x, self.y = newx, newy
                self.angle = math.atan2(pdy, pdx)

    def take_hit(self, dmg, particles, drops):
        self.hp -= dmg
        self.hit_flash = 8
        explode(particles, self.x, self.y, (255,180,60), n=10, speed=3, life=20, r=4)
        if self.hp <= 0:
            self.alive = False
            explode(particles, self.x, self.y, self.col, n=30, speed=5, life=40, r=6)
            explode(particles, self.x, self.y, (255,200,80), n=15, speed=3, life=30, r=4)
            # random drop
            roll = random.random()
            if roll < 0.18:
                drops.append(Drop(self.x, self.y, 'health'))
            elif roll < 0.30:
                drops.append(Drop(self.x, self.y, random.randint(0, len(WEAPONS)-1)))

    def draw(self, surf, cam):
        if not self.alive: return
        sx, sy = cam.apply(self.x, self.y)
        if not (-40 < sx < W+40 and -40 < sy < H+40): return

        col = C_WHITE if self.hit_flash % 2 == 1 else self.col
        # shadow
        pygame.draw.ellipse(surf, (0,0,0), (sx-self.size, sy-self.size//2+self.size, self.size*2, self.size))

        # body circle
        pygame.draw.circle(surf, col, (int(sx), int(sy)), self.size)
        pygame.draw.circle(surf, (0,0,0), (int(sx), int(sy)), self.size, 2)

        # head
        hx = sx + math.cos(self.angle)*self.size*0.45
        hy = sy + math.sin(self.angle)*self.size*0.45
        pygame.draw.circle(surf, (200,160,110), (int(hx),int(hy)), self.size//2)

        # gun
        gx = sx + math.cos(self.angle)*(self.size+8)
        gy = sy + math.sin(self.angle)*(self.size+8)
        pygame.draw.line(surf, (60,60,60), (int(sx),int(sy)), (int(gx),int(gy)), 4)

        # health bar
        bw = self.size*2+4
        ratio = self.hp / self.max_hp
        pygame.draw.rect(surf, C_RED,   (sx-bw//2, sy-self.size-10, bw, 5))
        pygame.draw.rect(surf, C_GREEN, (sx-bw//2, sy-self.size-10, int(bw*ratio), 5))

        # alert indicator
        if self.alert_timer > 120:
            pygame.draw.circle(surf, C_YELLOW, (int(sx), int(sy-self.size-18)), 5)

    def rect(self):
        return pygame.Rect(self.x-self.size, self.y-self.size, self.size*2, self.size*2)

# ─────────────────────────── player ───────────────────────────────────────────
class Player:
    SPEED    = 3.8
    HP_MAX   = 100
    ROLL_CD  = 90
    ROLL_DUR = 18

    def __init__(self):
        self.x, self.y = 10*TILE + 24.0, 15*TILE + 24.0
        self.hp        = self.HP_MAX
        self.angle     = 0.0
        self.alive     = True
        self.score     = 0

        # weapons inventory: index → ammo
        self.weapons   = {0: 30, 2: 45}    # start with rifle + SMG
        self.w_index   = 0                  # current weapon key
        self.w_slots   = [0, 2]            # ordered slot list
        self.cool      = 0
        self.reload_t  = 0

        self.roll_cd   = 0
        self.roll_dur  = 0
        self.roll_vx   = 0.0
        self.roll_vy   = 0.0

        self.hit_flash = 0
        self.kills     = 0

    @property
    def weapon(self):
        return WEAPONS[self.w_index]

    def current_ammo(self):
        return self.weapons.get(self.w_index, 0)

    def pick_weapon(self, w_idx):
        if w_idx not in self.weapons:
            self.weapons[w_idx] = WEAPONS[w_idx]['mag']
            if w_idx not in self.w_slots:
                self.w_slots.append(w_idx)
        else:
            self.weapons[w_idx] = min(
                self.weapons[w_idx] + WEAPONS[w_idx]['mag'],
                WEAPONS[w_idx]['mag'] * 3
            )

    def switch_weapon(self, direction):
        if len(self.w_slots) < 2: return
        idx = self.w_slots.index(self.w_index)
        idx = (idx + direction) % len(self.w_slots)
        self.w_index = self.w_slots[idx]
        self.cool = 0

    def update(self, keys, mouse_buttons, mouse_pos, cam, bullets):
        if not self.alive: return
        if self.hit_flash > 0: self.hit_flash -= 1
        if self.cool > 0:      self.cool -= 1

        # aim
        wx, wy = cam.world(*mouse_pos)
        self.angle = math.atan2(wy - self.y, wx - self.x)

        # roll
        if self.roll_dur > 0:
            self.roll_dur -= 1
            newx = self.x + self.roll_vx
            newy = self.y + self.roll_vy
            pr = pygame.Rect(newx-14, newy-14, 28, 28)
            if not is_solid_rect(pr):
                self.x, self.y = newx, newy
            return   # no other movement during roll

        if self.roll_cd > 0: self.roll_cd -= 1

        # movement
        mv_x = mv_y = 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:    mv_y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:  mv_y += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  mv_x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: mv_x += 1
        if mv_x and mv_y:
            mv_x *= 0.707; mv_y *= 0.707

        newx = self.x + mv_x * self.SPEED
        newy = self.y + mv_y * self.SPEED
        pr = pygame.Rect(newx-14, newy-14, 28, 28)
        if not is_solid_rect(pr):
            self.x, self.y = newx, newy

        # shoot
        w = self.weapon
        fired = mouse_buttons[0] if w['auto'] else False
        # handled in event loop for non-auto

        if self.cool == 0 and self.weapons.get(self.w_index, 0) > 0 and mouse_buttons[0]:
            self._fire(bullets)

    def _fire(self, bullets):
        w = self.weapon
        is_gren = (self.w_index == 3)
        shots = 6 if self.w_index == 1 else 1   # shotgun pellets
        for _ in range(shots):
            sp = math.radians(random.uniform(-w['spread']/2, w['spread']/2))
            b = Bullet(self.x, self.y, self.angle+sp,
                       w['speed'], w['damage'], 'player', w['col'], is_gren)
            bullets.append(b)
        self.weapons[self.w_index] -= 1
        self.cool = w['rate']
        if self.weapons[self.w_index] <= 0:
            self.weapons.pop(self.w_index)
            if self.w_index in self.w_slots:
                self.w_slots.remove(self.w_index)
            if self.w_slots:
                self.w_index = self.w_slots[0]

    def do_roll(self, keys):
        if self.roll_cd > 0 or self.roll_dur > 0: return
        mv_x = mv_y = 0
        if keys[pygame.K_w]: mv_y = -1
        if keys[pygame.K_s]: mv_y =  1
        if keys[pygame.K_a]: mv_x = -1
        if keys[pygame.K_d]: mv_x =  1
        if mv_x == 0 and mv_y == 0: mv_x = math.cos(self.angle); mv_y = math.sin(self.angle)
        ln = math.hypot(mv_x, mv_y) or 1
        self.roll_vx = (mv_x/ln) * 6.5
        self.roll_vy = (mv_y/ln) * 6.5
        self.roll_dur = self.ROLL_DUR
        self.roll_cd  = self.ROLL_CD

    def take_hit(self, dmg, particles):
        if self.roll_dur > 0: return   # invincible during roll
        self.hp -= dmg
        self.hit_flash = 10
        explode(particles, self.x, self.y, (255,80,80), n=8, speed=3, life=15, r=4)
        if self.hp <= 0:
            self.hp = 0; self.alive = False

    def draw(self, surf, cam):
        sx, sy = cam.apply(self.x, self.y)
        rolling = self.roll_dur > 0

        # shadow
        pygame.draw.ellipse(surf, (0,0,0), (sx-16, sy+8, 32, 12))

        body_col = (200,200,200) if self.hit_flash%2==1 else (60,130,200)
        if rolling: body_col = (100,200,255)

        # body
        pygame.draw.circle(surf, body_col, (int(sx),int(sy)), 16)
        pygame.draw.circle(surf, (30,70,140), (int(sx),int(sy)), 16, 2)

        # legs (two circles offset)
        lx1 = sx + math.cos(self.angle+2.2)*10
        ly1 = sy + math.sin(self.angle+2.2)*10
        lx2 = sx + math.cos(self.angle-2.2)*10
        ly2 = sy + math.sin(self.angle-2.2)*10
        pygame.draw.circle(surf, (40,90,160), (int(lx1),int(ly1)), 7)
        pygame.draw.circle(surf, (40,90,160), (int(lx2),int(ly2)), 7)

        # head
        hx = sx + math.cos(self.angle)*8
        hy = sy + math.sin(self.angle)*8
        pygame.draw.circle(surf, (210,170,110), (int(hx),int(hy)), 9)
        # helmet
        pygame.draw.arc(surf, (50,80,50),
                        (int(hx)-9, int(hy)-9, 18, 18), 0, math.pi, 4)

        # gun barrel
        w = self.weapon
        g_start = (sx + math.cos(self.angle)*10, sy + math.sin(self.angle)*10)
        g_end   = (sx + math.cos(self.angle)*26, sy + math.sin(self.angle)*26)
        pygame.draw.line(surf, (30,30,30), (int(g_start[0]),int(g_start[1])),
                         (int(g_end[0]),int(g_end[1])), 4)
        pygame.draw.circle(surf, w['col'], (int(g_end[0]),int(g_end[1])), 3)

        # roll trail
        if rolling:
            for i in range(3):
                tx = sx - math.cos(self.angle)*i*8
                ty = sy - math.sin(self.angle)*i*8
                pygame.draw.circle(surf, (80,180,255,80), (int(tx),int(ty)), 8-i*2)

    def rect(self):
        return pygame.Rect(self.x-14, self.y-14, 28, 28)

# ─────────────────────────── world drawing ────────────────────────────────────
_tree_cache = {}

def draw_tree(surf, sx, sy):
    pygame.draw.rect(surf, (80,50,20), (sx-5, sy-10, 10, 20))
    pygame.draw.circle(surf, (25,90,25), (sx, sy-18), 20)
    pygame.draw.circle(surf, (35,110,35), (sx-8, sy-22), 14)
    pygame.draw.circle(surf, (20,75,20), (sx+6, sy-24), 12)

def draw_world(surf, cam):
    # only draw visible tiles
    start_c = max(0, int(cam.x // TILE))
    start_r = max(0, int(cam.y // TILE))
    end_c   = min(MAP_COLS, start_c + W//TILE + 2)
    end_r   = min(MAP_ROWS, start_r + H//TILE + 2)

    tree_positions = []

    for r in range(start_r, end_r):
        for c in range(start_c, end_c):
            t = MAP[r][c]
            wx = c * TILE; wy = r * TILE
            sx, sy = cam.apply(wx, wy)

            if t == T_GRASS:
                col = C_GRASS if (r+c)%2==0 else C_GRASS2
                pygame.draw.rect(surf, col, (sx, sy, TILE, TILE))
                # random tufts
                random.seed(r*1000+c)
                for _ in range(3):
                    tx = sx + random.randint(4, TILE-4)
                    ty = sy + random.randint(4, TILE-4)
                    pygame.draw.line(surf, (40,65,25), (tx,ty),(tx,ty-5),1)
            elif t == T_ROAD:
                pygame.draw.rect(surf, C_ROAD, (sx, sy, TILE, TILE))
                # centre line
                if c % 3 == 0:
                    pygame.draw.rect(surf, (110,100,80), (sx+TILE//2-2, sy, 4, TILE))
            elif t == T_WALL:
                pygame.draw.rect(surf, C_WALL, (sx, sy, TILE, TILE))
                pygame.draw.rect(surf, C_WALL_S, (sx, sy, TILE, 4))
                pygame.draw.rect(surf, C_WALL_D, (sx, sy+TILE-4, TILE, 4))
                # brick pattern
                brick_y = (r % 2) * (TILE//2)
                for bx in range(0, TILE, TILE//2):
                    bx2 = (bx + brick_y) % TILE
                    pygame.draw.line(surf, C_WALL_D, (sx+bx2, sy), (sx+bx2, sy+TILE), 1)
                pygame.draw.line(surf, C_WALL_D, (sx, sy+TILE//2), (sx+TILE, sy+TILE//2), 1)
            elif t == T_WATER:
                col = C_WATER if (r+c+pygame.time.get_ticks()//500)%2==0 else C_WATER2
                pygame.draw.rect(surf, col, (sx, sy, TILE, TILE))
                # ripple
                pygame.draw.arc(surf, (60,130,200),
                                (sx+8, sy+8, TILE-16, TILE//2), 0, math.pi, 2)
            elif t == T_DIRT:
                pygame.draw.rect(surf, C_DIRT, (sx, sy, TILE, TILE))
                random.seed(r*999+c*3)
                for _ in range(2):
                    dx2 = sx+random.randint(4,TILE-4); dy2 = sy+random.randint(4,TILE-4)
                    pygame.draw.circle(surf, (70,50,30), (dx2,dy2), 3)

            # trees on grass edge tiles
            if t == T_GRASS:
                random.seed(r*777+c*13)
                if random.random() < 0.08:
                    tree_positions.append((sx+TILE//2, sy+TILE//2))

    random.seed(42)  # restore
    return tree_positions

# ─────────────────────────── HUD ──────────────────────────────────────────────
_font_hud  = None
_font_hudb = None
_font_huds = None

def get_fonts():
    global _font_hud, _font_hudb, _font_huds
    if _font_hud is None:
        _font_hud  = pygame.font.SysFont('consolas', 18, bold=True)
        _font_hudb = pygame.font.SysFont('consolas', 28, bold=True)
        _font_huds = pygame.font.SysFont('consolas', 13)
    return _font_hud, _font_hudb, _font_huds

def draw_hud(surf, player, wave, enemies_left):
    fh, fb, fs = get_fonts()

    # dark bottom bar
    bar_h = 70
    pygame.draw.rect(surf, C_HUD, (0, H-bar_h, W, bar_h))
    pygame.draw.line(surf, (60,80,40), (0, H-bar_h), (W, H-bar_h), 2)

    # HP bar
    pygame.draw.rect(surf, (60,20,20), (20, H-54, 180, 18), border_radius=4)
    hp_w = int(180 * max(0, player.hp) / player.HP_MAX)
    hp_col = C_GREEN if player.hp > 50 else C_YELLOW if player.hp > 25 else C_RED
    pygame.draw.rect(surf, hp_col, (20, H-54, hp_w, 18), border_radius=4)
    pygame.draw.rect(surf, (100,140,70), (20, H-54, 180, 18), 1, border_radius=4)
    t = fh.render(f"HP  {player.hp}", True, C_WHITE)
    surf.blit(t, (22, H-53))

    # weapon slots
    slot_x = 215
    for i, wi in enumerate(player.w_slots):
        w  = WEAPONS[wi]
        am = player.weapons.get(wi, 0)
        active = (wi == player.w_index)
        bx = slot_x + i*110
        bg = C_HUDA if active else C_HUD
        pygame.draw.rect(surf, bg, (bx, H-62, 105, 52), border_radius=5)
        border_col = w['col'] if active else (60,70,50)
        pygame.draw.rect(surf, border_col, (bx, H-62, 105, 52), 2 if active else 1, border_radius=5)
        nt = fh.render(w['name'], True, w['col'] if active else (140,150,120))
        at = fh.render(f"{am}", True, C_AMMO if active else (100,110,90))
        surf.blit(nt, (bx+6, H-58))
        surf.blit(at, (bx+6, H-36))
        kt = fs.render(f"[{i+1}]", True, (80,90,70))
        surf.blit(kt, (bx+80, H-58))

    # score / wave / kills
    sc_t = fb.render(f"{player.score:06d}", True, C_YELLOW)
    surf.blit(sc_t, (W-200, H-58))
    wt = fh.render(f"WAVE {wave}", True, (150,200,120))
    surf.blit(wt, (W-200, H-30))
    kt2 = fh.render(f"KILLS {player.kills}", True, (180,140,200))
    surf.blit(kt2, (W-100, H-30))

    # roll cooldown arc
    if player.roll_cd > 0:
        ratio = 1 - player.roll_cd / player.ROLL_CD
        angle_end = -math.pi/2 + math.tau * ratio
        pygame.draw.arc(surf, C_CYAN, (W-50, H-bar_h-55, 40, 40),
                        -math.pi/2, angle_end, 4)
    else:
        pygame.draw.circle(surf, C_CYAN, (W-30, H-bar_h-35), 10)

    rt = fs.render("ROLL[SPACE]", True, (80,120,100))
    surf.blit(rt, (W-58, H-bar_h-15))

    # enemies remaining mini-radar dots
    radar_x, radar_y, radar_r = W-80, H-bar_h-95, 28
    pygame.draw.circle(surf, (20,28,16), (radar_x, radar_y), radar_r)
    pygame.draw.circle(surf, (40,60,30), (radar_x, radar_y), radar_r, 1)
    pygame.draw.line(surf, (40,60,30),(radar_x-radar_r, radar_y),(radar_x+radar_r, radar_y),1)
    pygame.draw.line(surf, (40,60,30),(radar_x, radar_y-radar_r),(radar_x, radar_y+radar_r),1)

    # crosshair
    mx, my = pygame.mouse.get_pos()
    r = 12
    pygame.draw.line(surf, C_GREEN, (mx-r,my),(mx-4,my),2)
    pygame.draw.line(surf, C_GREEN, (mx+4,my),(mx+r,my),2)
    pygame.draw.line(surf, C_GREEN, (mx,my-r),(mx,my-4),2)
    pygame.draw.line(surf, C_GREEN, (mx,my+4),(mx,my+r),2)
    pygame.draw.circle(surf, C_GREEN, (mx,my), 4, 1)

# ─────────────────────────── screens ──────────────────────────────────────────
def title_screen(surf):
    fb = pygame.font.SysFont('consolas', 60, bold=True)
    fm = pygame.font.SysFont('consolas', 24, bold=True)
    fs = pygame.font.SysFont('consolas', 17)
    while True:
        surf.fill((15,20,10))
        # scanlines effect
        for y in range(0, H, 4):
            pygame.draw.line(surf, (0,0,0), (0,y),(W,y),1)

        t1 = fb.render("COMMANDO STRIKE", True, (80,200,80))
        surf.blit(t1, t1.get_rect(center=(W//2, 160)))
        t2 = fb.render("COMMANDO STRIKE", True, (40,255,40))
        surf.blit(t2, t2.get_rect(center=(W//2-2, 158)))

        lines = [
            ("WASD / ARROW KEYS",   "Move"),
            ("MOUSE AIM + LMB",     "Shoot"),
            ("SPACE",               "Dodge Roll  (invincible!)"),
            ("1-5",                 "Switch weapon"),
            ("SCROLL WHEEL",        "Cycle weapons"),
            ("Pick up glowing items","Weapons & Health"),
        ]
        for i,(k,v) in enumerate(lines):
            kt = fm.render(k, True, C_YELLOW)
            vt = fm.render(v, True, (180,220,140))
            surf.blit(kt, (W//2-280, 290+i*38))
            surf.blit(vt, (W//2+20,  290+i*38))

        blink = (pygame.time.get_ticks()//600)%2==0
        if blink:
            bt = fm.render("PRESS  ENTER  TO  BEGIN", True, C_GREEN)
            surf.blit(bt, bt.get_rect(center=(W//2, H-80)))

        pygame.display.flip()
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN: return

def game_over_screen(surf, score, kills, won):
    fb = pygame.font.SysFont('consolas', 54, bold=True)
    fm = pygame.font.SysFont('consolas', 26, bold=True)
    while True:
        surf.fill((10,10,15))
        msg = "MISSION COMPLETE!" if won else "YOU WERE ELIMINATED"
        col = (80,255,100) if won else (255,60,60)
        t = fb.render(msg, True, col)
        surf.blit(t, t.get_rect(center=(W//2, 200)))
        for i,(label,val) in enumerate([("SCORE", f"{score:06d}"),("KILLS", str(kills))]):
            lt = fm.render(label, True, (150,160,140))
            vt = fm.render(val, True, C_YELLOW)
            surf.blit(lt, (W//2-160, 310+i*50))
            surf.blit(vt, (W//2+40,  310+i*50))
        rt = fm.render("ENTER — play again      ESC — quit", True, (120,140,100))
        surf.blit(rt, rt.get_rect(center=(W//2, H-80)))
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN: return True
                if e.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()

# ─────────────────────────── wave spawner ─────────────────────────────────────
def spawn_wave(wave):
    enemies = []
    count = 4 + wave * 2
    spawn_zones = [
        (2*TILE, 2*TILE, 6*TILE, 6*TILE),
        (24*TILE, 2*TILE, 30*TILE, 6*TILE),
        (2*TILE, 22*TILE, 6*TILE, 26*TILE),
        (24*TILE, 22*TILE, 30*TILE, 26*TILE),
        (14*TILE, 9*TILE, 20*TILE, 13*TILE),
    ]
    for i in range(count):
        zone = random.choice(spawn_zones)
        x = random.randint(zone[0], zone[2])
        y = random.randint(zone[1], zone[3])
        if is_solid(x, y): x += TILE; y += TILE
        etype = min(len(ENEMY_TYPES)-1,
                    random.choices([0,1,2,3],
                                   weights=[40, 20+(wave*3), 15+(wave*2), 15+(wave*2)])[0])
        enemies.append(Enemy(x, y, etype))
    return enemies

# ─────────────────────────── main ─────────────────────────────────────────────
def main():
    pygame.init()
    pygame.mouse.set_visible(False)
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Commando Strike")
    clock  = pygame.time.Clock()

    title_screen(screen)

    while True:
        # ── setup ─────────────────────────────────────────────────────────────
        cam       = Camera()
        player    = Player()
        bullets: List[Bullet]   = []
        particles: List[Particle] = []
        drops: List[Drop]       = []
        wave      = 1
        enemies   = spawn_wave(wave)
        wave_msg_t = 120   # frames to show wave message
        running   = True

        while running:
            dt = clock.tick(FPS)
            keys  = pygame.key.get_pressed()
            mpos  = pygame.mouse.get_pos()
            mbuttons = pygame.mouse.get_pressed()

            # ── events ────────────────────────────────────────────────────────
            for e in pygame.event.get():
                if e.type == pygame.QUIT: pygame.quit(); sys.exit()
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()
                    if e.key == pygame.K_SPACE:  player.do_roll(keys)
                    # weapon slots 1-5
                    for ki, kval in enumerate([pygame.K_1,pygame.K_2,pygame.K_3,
                                               pygame.K_4,pygame.K_5]):
                        if e.key == kval and ki < len(player.w_slots):
                            player.w_index = player.w_slots[ki]
                    # non-auto shoot
                    if e.key == pygame.K_f:
                        b = None
                        if player.cool == 0 and player.weapons.get(player.w_index,0)>0:
                            player._fire(bullets)
                if e.type == pygame.MOUSEBUTTONDOWN:
                    if e.button == 1 and not WEAPONS[player.w_index]['auto']:
                        if player.cool==0 and player.weapons.get(player.w_index,0)>0:
                            player._fire(bullets)
                    if e.button == 4: player.switch_weapon(-1)
                    if e.button == 5: player.switch_weapon(1)

            # ── update ────────────────────────────────────────────────────────
            player.update(keys, mbuttons, mpos, cam, bullets)
            cam.update(player.x, player.y)

            for en in enemies:
                en.update(player, bullets, particles, drops)

            for b in bullets:
                b.update()

            # bullet ↔ enemy
            for b in [x for x in bullets if x.alive and x.owner=='player']:
                for en in [e for e in enemies if e.alive]:
                    if b.rect().colliderect(en.rect()):
                        b.alive = False
                        dmg = b.dmg
                        if b.is_grenade:
                            # area damage
                            for en2 in enemies:
                                if math.hypot(en2.x-b.x, en2.y-b.y) < 90:
                                    en2.take_hit(dmg, particles, drops)
                            explode(particles, b.x, b.y, C_ORANGE, 40, 7, 50, 10)
                            explode(particles, b.x, b.y, C_YELLOW, 20, 4, 30, 6)
                        else:
                            en.take_hit(dmg, particles, drops)
                        if not en.alive:
                            player.score += en.score
                            player.kills += 1
                        break

            # grenade area trigger on wall
            for b in [x for x in bullets if x.is_grenade and not x.alive]:
                explode(particles, b.x, b.y, C_ORANGE, 40, 7, 50, 10)

            # bullet ↔ player
            for b in [x for x in bullets if x.alive and x.owner=='enemy']:
                if b.rect().colliderect(player.rect()):
                    b.alive = False
                    player.take_hit(b.dmg, particles)

            # drops
            for d in drops:
                d.update()
                if d.rect().colliderect(player.rect()):
                    if d.kind == 'health':
                        player.hp = min(player.HP_MAX, player.hp + 35)
                    else:
                        player.pick_weapon(d.kind)
                    d.alive = False

            for p in particles: p.update()

            # cleanup
            bullets   = [b for b in bullets   if b.alive]
            particles = [p for p in particles if p.life > 0]
            drops     = [d for d in drops     if d.alive]
            enemies   = [e for e in enemies   if e.alive]

            # next wave
            if not enemies:
                wave += 1
                wave_msg_t = 150
                enemies = spawn_wave(wave)
                player.hp = min(player.HP_MAX, player.hp + 25)  # small heal

            if wave_msg_t > 0: wave_msg_t -= 1

            # ── draw ──────────────────────────────────────────────────────────
            tree_pos = draw_world(screen, cam)

            for d in drops:  d.draw(screen, cam)
            for p in particles: p.draw(screen, cam)
            for b in bullets: b.draw(screen, cam)
            for en in enemies: en.draw(screen, cam)

            # trees on top (above entities for depth)
            for tx, ty in tree_pos:
                draw_tree(screen, tx, ty)

            player.draw(screen, cam)
            draw_hud(screen, player, wave, len(enemies))

            # wave announcement
            if wave_msg_t > 0:
                fm2 = pygame.font.SysFont('consolas', 36, bold=True)
                alpha = min(255, wave_msg_t * 4)
                wt2 = fm2.render(f"— WAVE  {wave} —", True, C_YELLOW)
                screen.blit(wt2, wt2.get_rect(center=(W//2, H//2-40)))

            pygame.display.flip()

            if not player.alive:
                running = False

        again = game_over_screen(screen, player.score, player.kills, False)
        if not again: break

if __name__ == "__main__":
    main()