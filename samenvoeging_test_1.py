import pygame
import random
import sys
import math

pygame.init()

info = pygame.display.Info()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
W, H = screen.get_size()

SCALE = H / 768.0

BLACK = (0, 0, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

BLOCK_COUNT = 4
PLAYER_RADIUS = int(20 * SCALE)

PLAYER_MAX_SPEED = 11 * SCALE
PLAYER_ACCEL = 1.8 * SCALE
PLAYER_FRICTION = 0.82 

START_SPEED = 3.5 * SCALE
SPEED_INCREASE = 0.0007 * SCALE
MAX_FALL_SPEED = 14 * SCALE

SPLITTER_CHANCE = 0.22
SPLIT_TRIGGER_MARGIN = 40 * SCALE
SPLIT_CHILD_SPREAD = 3.8 * SCALE
SPLIT_MAX_EXTRA = 8

FONT_GAME_OVER = pygame.font.SysFont("Arial", int(72 * SCALE), bold=True)
FONT_RETRY = pygame.font.SysFont("Arial", int(30 * SCALE))
FONT_SCORE = pygame.font.SysFont("Arial", int(30 * SCALE), bold=True)

def make_block(level_mode="down"):
    base_min = int(20 * SCALE)
    base_max = int(65 * SCALE)
    size = random.randint(base_min, base_max)

    if level_mode == "side":
        x = random.randint(W, W + int(500 * SCALE))
        y = random.randint(0, H - size)
    elif level_mode == "up":
        x = random.randint(0, W - size)
        y = random.randint(H, H + int(500 * SCALE))
    else:
        x = random.randint(0, W - size)
        y = random.randint(int(-500 * SCALE), 0)

    is_splitter = (random.random() < SPLITTER_CHANCE)
    drift_strength = 1.2 * SCALE
    
    return {
        "x": float(x),
        "y": float(y),
        "size": size,
        "splitter": is_splitter,
        "split_done": False,
        "vx": random.uniform(-drift_strength, drift_strength),
        "vy": random.uniform(-0.5 * SCALE, 0.5 * SCALE),
    }

def create_blocks(level_mode="down"):
    return [make_block(level_mode) for _ in range(BLOCK_COUNT)]

def respawn_block(block, level_mode):
    block.update(make_block(level_mode))

def maybe_split(blocks, block, level_mode, fall_speed, max_allowed_blocks):
    if not block["splitter"] or block["split_done"]:
        return
    if len(blocks) >= max_allowed_blocks:
        return

    if level_mode == "side":
        mid_x = W / 2
        if abs(block["x"] - mid_x) > SPLIT_TRIGGER_MARGIN: return
    else:
        mid_y = H / 2
        if abs(block["y"] - mid_y) > SPLIT_TRIGGER_MARGIN: return

    block["split_done"] = True
    parent_size = block["size"]
    child_size = max(int(18 * SCALE), parent_size // 2)
    cx, cy = block["x"] + parent_size / 4, block["y"] + parent_size / 4

    if level_mode == "side":
        c1 = {"x": cx, "y": cy, "size": child_size, "splitter": False, "split_done": True, "vx": block["vx"], "vy": -SPLIT_CHILD_SPREAD}
        c2 = {"x": cx, "y": cy, "size": child_size, "splitter": False, "split_done": True, "vx": block["vx"], "vy": +SPLIT_CHILD_SPREAD}
    else:
        c1 = {"x": cx, "y": cy, "size": child_size, "splitter": False, "split_done": True, "vx": -SPLIT_CHILD_SPREAD, "vy": block["vy"]}
        c2 = {"x": cx, "y": cy, "size": child_size, "splitter": False, "split_done": True, "vx": +SPLIT_CHILD_SPREAD, "vy": block["vy"]}

    blocks.extend([c1, c2])

def update_blocks(blocks, fall_speed, current_score, level_mode):
    extra_planeten = (current_score // 800) 
    max_allowed = BLOCK_COUNT + extra_planeten + SPLIT_MAX_EXTRA

    for block in blocks:
        s = block["size"]
        if level_mode == "side":
            block["x"] += fall_speed
            block["y"] += block["vy"]
            block["x"] += block["vx"]
            maybe_split(blocks, block, level_mode, fall_speed, max_allowed)
            if block["x"] < -s: respawn_block(block, level_mode)
        else:
            block["y"] += fall_speed
            block["x"] += block["vx"]
            block["y"] += block["vy"]
            maybe_split(blocks, block, level_mode, fall_speed, max_allowed)
            if fall_speed > 0 and block["y"] > H: respawn_block(block, "down")
            elif fall_speed < 0 and block["y"] < -s: respawn_block(block, "up")

    if len(blocks) < BLOCK_COUNT + extra_planeten:
        blocks.append(make_block(level_mode))

def show_game_over(surface, final_score):
    waiting = True
    while waiting:
        surface.fill(BLACK)
        t1 = FONT_GAME_OVER.render("GAME OVER", True, RED)
        t2 = FONT_RETRY.render(f"Score: {final_score // 10}", True, WHITE)
        t3 = FONT_RETRY.render("Druk SPATIE om te herstarten", True, GREEN)
        t4 = FONT_RETRY.render("Druk ESC om te stoppen", True, YELLOW)
        
        cx, cy = W // 2, H // 2
        surface.blit(t1, t1.get_rect(center=(cx, cy - int(80 * SCALE))))
        surface.blit(t2, t2.get_rect(center=(cx, cy)))
        surface.blit(t3, t3.get_rect(center=(cx, cy + int(80 * SCALE))))
        surface.blit(t4, t4.get_rect(center=(cx, cy + int(140 * SCALE))))

        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE: waiting = False
                if event.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()

def render_frame(surface, blocks, px, py, score, lives, immunity, bg_img, imgs, p_img, portal_rect, portal_img):
    surface.fill(BLACK)
    surface.blit(bg_img, (0, 0))

    if portal_rect and portal_img:
        surface.blit(portal_img, portal_rect)

    for b in blocks:
        if b["size"] < 40 * SCALE: img = imgs[0]
        elif b["size"] < 50 * SCALE: img = imgs[1]
        else: img = imgs[2]
        surface.blit(pygame.transform.scale(img, (b["size"], b["size"])), (b["x"], b["y"]))
        
        if b["splitter"] and not b["split_done"]:
             pygame.draw.circle(surface, YELLOW, (int(b["x"])+b["size"]//2, int(b["y"])+b["size"]//2), b["size"]//2 + int(8 * SCALE), 3)

    if immunity == 0 or (immunity // 5) % 2 == 0:
        surface.blit(p_img, p_img.get_rect(center=(int(px), int(py))))

    score_offset = int(180 * SCALE)
    score_y = int(20 * SCALE)
    surface.blit(FONT_SCORE.render(f"Score: {score // 10}", True, WHITE), (W - score_offset, score_y))

def main():
    pygame.display.set_caption("Space Dodger Fullscreen")
    clock = pygame.time.Clock()

    p_img = pygame.image.load("images/spaceshipp.png").convert_alpha()
    p_img = pygame.transform.scale(p_img, (PLAYER_RADIUS * 2, PLAYER_RADIUS * 2))
    
    bg_img = pygame.image.load("images/galaxy.png").convert()
    bg_img = pygame.transform.scale(bg_img, (W, H))
    
    met_s = pygame.image.load("images/neptunus.png").convert_alpha()
    met_m = pygame.image.load("images/mars.png").convert_alpha()
    met_l = pygame.image.load("images/jupiter.png").convert_alpha()
    
    heart_size = int(30 * SCALE)
    heart_img = pygame.image.load("images/lives.png").convert_alpha()
    heart_img = pygame.transform.scale(heart_img, (heart_size, heart_size))
    
    portal_w, portal_h = int(200 * SCALE), int(40 * SCALE)
    portal_img = pygame.image.load("images/portal.png").convert_alpha()
    portal_img = pygame.transform.scale(portal_img, (portal_w, portal_h))

    imgs = [met_s, met_m, met_l]

    x, y = W // 2, H - int(100 * SCALE)
    player_vx = 0
    player_vy = 0

    blocks = create_blocks("down")
    fall_speed = START_SPEED
    score, lives, immunity_timer = 0, 3, 0
    level_flipped, level_side = False, False

    running = True
    while running:
        clock.tick(60)
        
        portal1 = ((score // 10) >= 250 and not level_flipped)
        portal2 = ((score // 10) >= 500 and level_flipped and not level_side)
        portal_active = portal1 or portal2
        if immunity_timer > 0: immunity_timer -= 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: running = False
        
        keys = pygame.key.get_pressed()
        input_x = 0
        input_y = 0
        
        if not portal_active:
            if keys[pygame.K_LEFT]:  input_x -= 1
            if keys[pygame.K_RIGHT]: input_x += 1
            if keys[pygame.K_UP]:    input_y -= 1
            if keys[pygame.K_DOWN]:  input_y += 1

        if input_x != 0:
            player_vx += input_x * PLAYER_ACCEL
        else:
            player_vx *= PLAYER_FRICTION

        if input_y != 0:
            player_vy += input_y * PLAYER_ACCEL
        else:
            player_vy *= PLAYER_FRICTION

        speed = math.sqrt(player_vx**2 + player_vy**2)
        if speed > PLAYER_MAX_SPEED:
            scale_v = PLAYER_MAX_SPEED / speed
            player_vx *= scale_v
            player_vy *= scale_v
        
        if abs(player_vx) < 0.1: player_vx = 0
        if abs(player_vy) < 0.1: player_vy = 0

        x += player_vx
        y += player_vy

        score += 1

        if not level_flipped:
            fall_speed = min(START_SPEED + (score * SPEED_INCREASE), MAX_FALL_SPEED)
            level_mode = "down"
        elif level_flipped and not level_side:
            fall_speed = max(-START_SPEED - (score * SPEED_INCREASE), -MAX_FALL_SPEED)
            level_mode = "up"
        else:
            fall_speed = max(-START_SPEED - (score * SPEED_INCREASE), -MAX_FALL_SPEED)
            level_mode = "side"

        update_blocks(blocks, fall_speed, score, level_mode)

        x = max(PLAYER_RADIUS, min(W - PLAYER_RADIUS, x))
        y = max(PLAYER_RADIUS, min(H - PLAYER_RADIUS, y))
        player_rect = pygame.Rect(x - PLAYER_RADIUS, y - PLAYER_RADIUS, PLAYER_RADIUS * 2, PLAYER_RADIUS * 2)

        portal_rect = None
        portal_y_top = int(20 * SCALE)
        portal_y_bot = H - int(40 * SCALE)
        
        if portal1: portal_rect = pygame.Rect(W//2 - portal_w//2, portal_y_top, portal_w, portal_h)
        elif portal2: portal_rect = pygame.Rect(W//2 - portal_w//2, portal_y_bot, portal_w, portal_h)

        if portal_rect:
            dx, dy = portal_rect.centerx - x, portal_rect.centery - y
            x += dx * 0.05
            y += dy * 0.05
            player_rect.center = (x, y)

            if player_rect.colliderect(portal_rect):
                if not level_flipped:
                    level_flipped = True
                    x, y = W // 2, int(100 * SCALE)
                    blocks = create_blocks("up")
                else:
                    level_side = True
                    x, y = int(100 * SCALE), H // 2
                    blocks = create_blocks("side")
                player_vx, player_vy = 0, 0
                continue

        for block in blocks:
            b_rect = pygame.Rect(block["x"], block["y"], block["size"], block["size"])
            hitbox = b_rect.inflate(int(-6 * SCALE), int(-6 * SCALE))
            
            if player_rect.colliderect(hitbox) and immunity_timer == 0 and not portal_active:
                lives -= 1
                render_frame(screen, blocks, x, y, score, lives, 1, bg_img, imgs, p_img, portal_rect, portal_img)
                pygame.time.delay(300)
                immunity_timer = 90

                if lives <= 0:
                    show_game_over(screen, score)
                    lives, score, fall_speed = 3, 0, START_SPEED
                    level_flipped, level_side = False, False
                    x, y = W // 2, H - int(100 * SCALE)
                    player_vx, player_vy = 0, 0
                    blocks = create_blocks("down")
                break

        render_frame(screen, blocks, x, y, score, lives, immunity_timer, bg_img, imgs, p_img, portal_rect, portal_img)
        
        heart_margin = int(20 * SCALE)
        heart_spacing = int(35 * SCALE)
        for i in range(lives):
            screen.blit(heart_img, (heart_margin + (i * heart_spacing), heart_margin))
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()