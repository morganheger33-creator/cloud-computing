import pygame
import random
import math
import sys

# ── Init ──────────────────────────────────────────────────────────────────────
pygame.init()

WIDTH, HEIGHT = 900, 650
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tank Battle")
clock = pygame.time.Clock()
FPS = 60

# ── Colours ───────────────────────────────────────────────────────────────────
C_BG          = (34,  139,  34)   # grass green
C_GROUND      = (101,  67,  33)   # dirt brown strip
C_PLAYER      = (50,  100, 200)   # blue tank body
C_PLAYER_D    = (30,   60, 140)   # blue tank dark
C_ENEMY       = (200,  50,  50)   # red tank body
C_ENEMY_D     = (140,  30,  30)   # red tank dark
C_BULLET_P    = (255, 230,   0)   # player bullet
C_BULLET_E    = (255, 100,   0)   # enemy bullet
C_TREE        = (20,   80,  20)   # tree trunk/leaves
C_WHITE       = (255, 255, 255)
C_BLACK       = (0,     0,   0)
C_HUD_BG      = (20,   20,  20)
C_HP_GREEN    = (0,   200,  50)
C_HP_RED      = (220,  50,  50)
C_EXPLOSION   = [(255,200,0),(255,140,0),(255,80,0),(200,50,0)]
C_ROAD        = (80,   70,  60)

GROUND_Y      = HEIGHT - 100      # top of the ground strip

# ── Fonts ─────────────────────────────────────────────────────────────────────
font_big   = pygame.font.SysFont("consolas", 52, bold=True)
font_med   = pygame.font.SysFont("consolas", 28, bold=True)
font_small = pygame.font.SysFont("consolas", 20)

# ── Helpers ───────────────────────────────────────────────────────────────────
def draw_text(surf, text, font, color, cx, cy):
    s = font.render(text, True, color)
    surf.blit(s, s.get_rect(center=(cx, cy)))

def clamp(val, lo, hi):
    return max(lo, min(hi, val))

# ── Tank drawing ──────────────────────────────────────────────────────────────
def draw_tank(surf, x, y, angle_deg, body_col, dark_col, barrel_col=(200,200,200)):
    """Draw a top-down-ish side-view tank centred at (x, y)."""
    W, H = 52, 30
    # body
    body = pygame.Rect(x - W//2, y - H//2, W, H)
    pygame.draw.rect(surf, body_col, body, border_radius=6)
    pygame.draw.rect(surf, dark_col, body, 2, border_radius=6)
    # turret dome
    pygame.draw.circle(surf, dark_col, (x, y), 12)
    pygame.draw.circle(surf, body_col, (x, y), 10)
    # barrel
    rad = math.radians(angle_deg)
    bx = x + math.cos(rad) * 22
    by = y + math.sin(rad) * 22
    pygame.draw.line(surf, barrel_col, (x, y), (int(bx), int(by)), 5)
    # tracks (simple lines)
    pygame.draw.rect(surf, dark_col, (x - W//2, y - H//2 - 5, W, 5), border_radius=2)
    pygame.draw.rect(surf, dark_col, (x - W//2, y + H//2,     W, 5), border_radius=2)

# ── Particle / Explosion ──────────────────────────────────────────────────────
class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 7)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = random.randint(20, 45)
        self.max_life = self.life
        self.r = random.randint(4, 10)
        self.col = random.choice(C_EXPLOSION)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.2
        self.life -= 1

    def draw(self, surf):
        alpha = int(255 * self.life / self.max_life)
        r = max(1, int(self.r * self.life / self.max_life))
        pygame.draw.circle(surf, self.col, (int(self.x), int(self.y)), r)

# ── Bullet ────────────────────────────────────────────────────────────────────
class Bullet:
    SPEED = 10
    def __init__(self, x, y, angle_deg, owner):
        self.x = float(x)
        self.y = float(y)
        rad = math.radians(angle_deg)
        self.vx = math.cos(rad) * self.SPEED
        self.vy = math.sin(rad) * self.SPEED
        self.owner = owner   # 'player' or 'enemy'
        self.alive = True
        self.col = C_BULLET_P if owner == 'player' else C_BULLET_E

    def update(self):
        self.x += self.vx
        self.y += self.vy
        if not (0 < self.x < WIDTH and 0 < self.y < HEIGHT):
            self.alive = False

    def draw(self, surf):
        pygame.draw.circle(surf, self.col, (int(self.x), int(self.y)), 5)

    def rect(self):
        return pygame.Rect(self.x - 5, self.y - 5, 10, 10)

# ── Player Tank ───────────────────────────────────────────────────────────────
class Player:
    SPEED   = 4
    HP_MAX  = 5
    COOLDOWN = 25   # frames between shots

    def __init__(self):
        self.x = 120
        self.y = GROUND_Y - 20
        self.angle = 0          # barrel angle
        self.hp = self.HP_MAX
        self.cool = 0
        self.score = 0

    def handle_input(self, keys):
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: self.x -= self.SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.x += self.SPEED
        # constrain to ground
        self.x = clamp(self.x, 30, WIDTH - 30)
        self.y = GROUND_Y - 20

        # rotate barrel
        if keys[pygame.K_UP]   or keys[pygame.K_w]: self.angle -= 3
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: self.angle += 3
        self.angle = clamp(self.angle, -85, 85)

        if self.cool > 0:
            self.cool -= 1

    def shoot(self):
        if self.cool == 0:
            rad = math.radians(self.angle)
            bx = self.x + math.cos(rad) * 28
            by = self.y + math.sin(rad) * 28
            self.cool = self.COOLDOWN
            return Bullet(bx, by, self.angle, 'player')
        return None

    def draw(self, surf):
        draw_tank(surf, self.x, self.y, self.angle, C_PLAYER, C_PLAYER_D)

    def rect(self):
        return pygame.Rect(self.x - 26, self.y - 15, 52, 30)

# ── Enemy Tank ────────────────────────────────────────────────────────────────
class Enemy:
    HP_MAX  = 3
    COOLDOWN_MIN = 90
    COOLDOWN_MAX = 180

    def __init__(self, level):
        self.x = float(random.randint(500, WIDTH - 60))
        self.y = float(GROUND_Y - 20)
        self.hp = self.HP_MAX + level // 2
        self.speed = 1.2 + level * 0.15
        self.dir = -1                         # move left toward player
        self.angle = 180                      # barrel points left by default
        self.cool = random.randint(self.COOLDOWN_MIN, self.COOLDOWN_MAX)
        self.alive = True

    def update(self, player):
        # drift toward player horizontally
        if self.x > player.x + 250:
            self.x += self.dir * self.speed
        # aim roughly at player
        dx = player.x - self.x
        dy = player.y - self.y
        target_angle = math.degrees(math.atan2(dy, dx))
        # smooth rotation
        diff = (target_angle - self.angle + 180) % 360 - 180
        self.angle += clamp(diff, -2, 2)

        self.cool -= 1

    def shoot(self):
        if self.cool <= 0:
            rad = math.radians(self.angle)
            bx = self.x + math.cos(rad) * 28
            by = self.y + math.sin(rad) * 28
            self.cool = random.randint(self.COOLDOWN_MIN, self.COOLDOWN_MAX)
            return Bullet(bx, by, self.angle, 'enemy')
        return None

    def draw(self, surf):
        draw_tank(surf, int(self.x), int(self.y), self.angle, C_ENEMY, C_ENEMY_D)
        # health bar
        bar_w = 50
        ratio = self.hp / (self.HP_MAX + 0)  # approximation
        pygame.draw.rect(surf, C_HP_RED,   (self.x - 25, self.y - 30, bar_w, 6))
        pygame.draw.rect(surf, C_HP_GREEN, (self.x - 25, self.y - 30, int(bar_w * (self.hp / (self.HP_MAX))), 6))

    def rect(self):
        return pygame.Rect(self.x - 26, self.y - 15, 52, 30)

# ── Scenery ───────────────────────────────────────────────────────────────────
def draw_scenery(surf, trees):
    # sky gradient effect (flat strips)
    surf.fill((100, 160, 240))                          # sky
    pygame.draw.rect(surf, (80, 190, 100),
                     (0, GROUND_Y - 8, WIDTH, 8))       # grass edge
    pygame.draw.rect(surf, C_ROAD,
                     (0, GROUND_Y - 5, WIDTH, HEIGHT - GROUND_Y + 5))  # ground

    # road markings
    for rx in range(0, WIDTH, 80):
        pygame.draw.rect(surf, (200, 190, 160), (rx, GROUND_Y + 20, 40, 6))

    # clouds (static)
    for cx, cy in [(150,60),(350,40),(600,70),(800,50)]:
        pygame.draw.ellipse(surf, C_WHITE, (cx, cy, 90, 30))
        pygame.draw.ellipse(surf, C_WHITE, (cx+20, cy-15, 60, 30))

    # trees
    for tx, ty in trees:
        pygame.draw.rect(surf, (100, 60, 20), (tx - 5, ty - 30, 10, 30))
        pygame.draw.circle(surf, (30, 110, 30), (tx, ty - 35), 22)
        pygame.draw.circle(surf, (20,  90, 20), (tx, ty - 45), 14)

# ── HUD ───────────────────────────────────────────────────────────────────────
def draw_hud(surf, player, level, enemies_left):
    # top bar background
    pygame.draw.rect(surf, C_HUD_BG, (0, 0, WIDTH, 42))

    # HP hearts / pips
    for i in range(player.HP_MAX):
        col = C_HP_GREEN if i < player.hp else (60, 60, 60)
        pygame.draw.rect(surf, col, (10 + i * 28, 8, 22, 26), border_radius=4)

    draw_text(surf, f"SCORE  {player.score:05d}", font_small, C_WHITE, WIDTH//2, 21)
    draw_text(surf, f"LVL {level}   ENEMIES {enemies_left}", font_small, C_WHITE, WIDTH - 170, 21)

    # barrel angle indicator
    draw_text(surf, f"AIM {player.angle:+.0f}°", font_small, (180,220,255), 300, 21)

    # reload bar
    if player.cool > 0:
        ratio = 1 - player.cool / player.COOLDOWN
        pygame.draw.rect(surf, (60,60,60), (10, 36, 120, 5))
        pygame.draw.rect(surf, C_BULLET_P, (10, 36, int(120*ratio), 5))

# ── Screens ───────────────────────────────────────────────────────────────────
def title_screen():
    while True:
        screen.fill((20, 20, 40))
        draw_text(screen, "TANK BATTLE", font_big,  (255,200,0),  WIDTH//2, 180)
        draw_text(screen, "ARROW KEYS / WASD  — Move & Aim",  font_small, C_WHITE, WIDTH//2, 290)
        draw_text(screen, "SPACE — Fire",                      font_small, C_WHITE, WIDTH//2, 320)
        draw_text(screen, "Destroy all enemy tanks to advance!", font_small, (180,255,180), WIDTH//2, 360)
        draw_text(screen, "Press  ENTER  to start",            font_med,   (255,220,100), WIDTH//2, 430)
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN:
                return

def game_over_screen(score, won):
    msg   = "MISSION COMPLETE!" if won else "TANK DESTROYED!"
    color = (100, 255, 100)    if won else (255, 80, 80)
    while True:
        screen.fill((10, 10, 20))
        draw_text(screen, msg,                     font_big,   color,   WIDTH//2, 200)
        draw_text(screen, f"Final Score: {score}", font_med,   C_WHITE, WIDTH//2, 290)
        draw_text(screen, "Press ENTER to play again",
                  font_small, (200,200,200), WIDTH//2, 370)
        draw_text(screen, "Press ESC to quit",
                  font_small, (200,200,200), WIDTH//2, 400)
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN: return True
                if e.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()

# ── Main Game Loop ────────────────────────────────────────────────────────────
def run_game():
    # static scenery trees
    trees = [(random.randint(0, WIDTH), GROUND_Y - 5) for _ in range(12)]

    player    = Player()
    level     = 1
    enemies   = [Enemy(level) for _ in range(3)]
    bullets   = []
    particles = []

    ENEMIES_PER_LEVEL = 3

    running = True
    while running:
        clock.tick(FPS)

        # ── Events ────────────────────────────────────────────────────────────
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                if e.key == pygame.K_SPACE:
                    b = player.shoot()
                    if b:
                        bullets.append(b)

        # ── Player input ──────────────────────────────────────────────────────
        keys = pygame.key.get_pressed()
        player.handle_input(keys)

        # ── Enemy update & shoot ──────────────────────────────────────────────
        for en in enemies:
            en.update(player)
            b = en.shoot()
            if b:
                bullets.append(b)

        # ── Bullets ───────────────────────────────────────────────────────────
        for b in bullets:
            b.update()

        # collision: player bullets → enemies
        for b in bullets:
            if b.owner == 'player' and b.alive:
                for en in enemies:
                    if en.alive and b.rect().colliderect(en.rect()):
                        en.hp -= 1
                        b.alive = False
                        for _ in range(18):
                            particles.append(Particle(en.x, en.y))
                        if en.hp <= 0:
                            en.alive = False
                            player.score += 100

        # collision: enemy bullets → player
        for b in bullets:
            if b.owner == 'enemy' and b.alive:
                if b.rect().colliderect(player.rect()):
                    player.hp -= 1
                    b.alive = False
                    for _ in range(14):
                        particles.append(Particle(player.x, player.y))

        # clean up
        bullets   = [b for b in bullets   if b.alive]
        enemies   = [e for e in enemies   if e.alive]
        particles = [p for p in particles if p.life > 0]
        for p in particles:
            p.update()

        # ── Level advance ──────────────────────────────────────────────────────
        if not enemies:
            level += 1
            count = ENEMIES_PER_LEVEL + level - 1
            enemies = [Enemy(level) for _ in range(count)]
            player.score += 250 * (level - 1)

        # ── Player dead ───────────────────────────────────────────────────────
        if player.hp <= 0:
            return player.score, False     # game over

        # ── Draw ─────────────────────────────────────────────────────────────
        draw_scenery(screen, trees)

        for p in particles:
            p.draw(screen)

        for b in bullets:
            b.draw(screen)

        for en in enemies:
            en.draw(screen)

        player.draw(screen)

        draw_hud(screen, player, level, len(enemies))

        pygame.display.flip()

    return player.score, True

# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    title_screen()
    while True:
        score, won = run_game()
        again = game_over_screen(score, won)
        if not again:
            break

if __name__ == "__main__":
    main()