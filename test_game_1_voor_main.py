import pygame
import random
import sys
import math

pygame.init()

BLACK = (0, 0, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

SCREEN_SIZE = (1024, 768)
BLOCK_COUNT = 4
PLAYER_RADIUS = 20

PLAYER_MAX_SPEED = 11
PLAYER_ACCEL = 1.8
PLAYER_FRICTION = 0.82

START_SPEED = 3.5
SPEED_INCREASE = 0.0007
MAX_FALL_SPEED = 14

SPLITTER_CHANCE = 0.22
SPLIT_TRIGGER_MARGIN = 40
SPLIT_CHILD_SPREAD = 3.8
SPLIT_MAX_EXTRA = 8

FONT_GAME_OVER = pygame.font.SysFont("Arial", 72, bold=True)
FONT_RETRY = pygame.font.SysFont("Arial", 30)
FONT_SCORE = pygame.font.SysFont("Arial", 30, bold=True)

def create_main_surface(screen_size):
    return pygame.display.set_mode(screen_size)

def make_block(level_mode="down"):
    size = random.randint(20, 65)
    if level_mode == "side":
        x = random.randint(SCREEN_SIZE[0], SCREEN_SIZE[0] + 500)
        y = random.randint(0, SCREEN_SIZE[1] - size)
    elif level_mode == "up":
        x = random.randint(0, SCREEN_SIZE[0] - size)
        y = random.randint(SCREEN_SIZE[1], SCREEN_SIZE[1] + 500)
    else:
        x = random.randint(0, SCREEN_SIZE[0] - size)
        y = random.randint(-500, 0)

    is_splitter = (random.random() < SPLITTER_CHANCE)
    drift_strength = 1.2
    return {
        "x": float(x),
        "y": float(y),
        "size": size,
        "splitter": is_splitter,
        "split_done": False,
        "vx": random.uniform(-drift_strength, drift_strength),
        "vy": random.uniform(-0.5, 0.5),
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
        mid_x = SCREEN_SIZE[0] / 2
        if abs(block["x"] - mid_x) > SPLIT_TRIGGER_MARGIN: return
    else:
        mid_y = SCREEN_SIZE[1] / 2
        if abs(block["y"] - mid_y) > SPLIT_TRIGGER_MARGIN: return

    block["split_done"] = True
    parent_size = block["size"]
    child_size = max(18, parent_size // 2)
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
            if fall_speed > 0 and block["y"] > SCREEN_SIZE[1]: respawn_block(block, "down")
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
        
        cx, cy = SCREEN_SIZE[0]//2, SCREEN_SIZE[1]//2
        surface.blit(t1, t1.get_rect(center=(cx, cy - 80)))
        surface.blit(t2, t2.get_rect(center=(cx, cy)))
        surface.blit(t3, t3.get_rect(center=(cx, cy + 80)))

        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                waiting = False

def render_frame(surface, blocks, px, py, score, lives, immunity, bg_img, imgs, p_img, portal_rect, portal_img):
    surface.fill(BLACK)
    surface.blit(bg_img, (0, 0))

    if portal_rect and portal_img:
        surface.blit(portal_img, portal_rect)

    for b in blocks:
        if b["size"] < 40: img = imgs[0]
        elif b["size"] < 50: img = imgs[1]
        else: img = imgs[2]
        surface.blit(pygame.transform.scale(img, (b["size"], b["size"])), (b["x"], b["y"]))
        
        if b["splitter"] and not b["split_done"]:
             pygame.draw.circle(surface, YELLOW, (int(b["x"])+b["size"]//2, int(b["y"])+b["size"]//2), b["size"]//2 + 8, 3)

    if immunity == 0 or (immunity // 5) % 2 == 0:
        surface.blit(p_img, p_img.get_rect(center=(int(px), int(py))))

    surface.blit(FONT_SCORE.render(f"Score: {score // 10}", True, WHITE), (SCREEN_SIZE[0] - 180, 20))

def main():
    surface = create_main_surface(SCREEN_SIZE)
    pygame.display.set_caption("Space Dodger")
    clock = pygame.time.Clock()

    p_img = pygame.image.load("images/spaceshipp.png").convert_alpha()
    p_img = pygame.transform.scale(p_img, (PLAYER_RADIUS * 2, PLAYER_RADIUS * 2))
    bg_img = pygame.image.load("images/galaxy.png").convert()
    bg_img = pygame.transform.scale(bg_img, SCREEN_SIZE)
    met_s = pygame.image.load("images/neptunus.png").convert_alpha()
    met_m = pygame.image.load("images/mars.png").convert_alpha()
    met_l = pygame.image.load("images/jupiter.png").convert_alpha()
    heart_img = pygame.image.load("images/lives.png").convert_alpha()
    heart_img = pygame.transform.scale(heart_img, (30, 30))
    portal_img = pygame.image.load("images/portal.png").convert_alpha()
    portal_img = pygame.transform.scale(portal_img, (200, 40))

    imgs = [met_s, met_m, met_l]

    x, y = SCREEN_SIZE[0] // 2, SCREEN_SIZE[1] - 100
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
            scale = PLAYER_MAX_SPEED / speed
            player_vx *= scale
            player_vy *= scale
        
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

        x = max(PLAYER_RADIUS, min(SCREEN_SIZE[0] - PLAYER_RADIUS, x))
        y = max(PLAYER_RADIUS, min(SCREEN_SIZE[1] - PLAYER_RADIUS, y))
        player_rect = pygame.Rect(x - PLAYER_RADIUS, y - PLAYER_RADIUS, PLAYER_RADIUS * 2, PLAYER_RADIUS * 2)

        portal_rect = None
        if portal1: portal_rect = pygame.Rect(SCREEN_SIZE[0]//2-100, 20, 200, 40)
        elif portal2: portal_rect = pygame.Rect(SCREEN_SIZE[0]//2-100, SCREEN_SIZE[1]-40, 200, 40)

        if portal_rect:
            dx, dy = portal_rect.centerx - x, portal_rect.centery - y
            x += dx * 0.05
            y += dy * 0.05
            player_rect.center = (x, y)

            if player_rect.colliderect(portal_rect):
                if not level_flipped:
                    level_flipped = True
                    x, y = SCREEN_SIZE[0]//2, 100
                    blocks = create_blocks("up")
                else:
                    level_side = True
                    x, y = 100, SCREEN_SIZE[1]//2
                    blocks = create_blocks("side")
                player_vx, player_vy = 0, 0
                continue

        for block in blocks:
            b_rect = pygame.Rect(block["x"], block["y"], block["size"], block["size"])
            hitbox = b_rect.inflate(-6, -6)
            
            if player_rect.colliderect(hitbox) and immunity_timer == 0 and not portal_active:
                lives -= 1
                render_frame(surface, blocks, x, y, score, lives, 1, bg_img, imgs, p_img, portal_rect, portal_img)
                pygame.time.delay(300)
                immunity_timer = 90

                if lives <= 0:
                    show_game_over(surface, score)
                    lives, score, fall_speed = 3, 0, START_SPEED
                    level_flipped, level_side = False, False
                    x, y = SCREEN_SIZE[0] // 2, SCREEN_SIZE[1] - 100
                    player_vx, player_vy = 0, 0
                    blocks = create_blocks("down")
                break

        render_frame(surface, blocks, x, y, score, lives, immunity_timer, bg_img, imgs, p_img, portal_rect, portal_img)
        
        for i in range(lives):
            surface.blit(heart_img, (20 + (i * 35), 20))
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()