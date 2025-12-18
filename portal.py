import pygame
import random
import sys

pygame.init()

BLACK = (0, 0, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 100, 255)
GREEN = (0, 255, 0)

SCREEN_SIZE = (1400, 800)
BLOCK_COUNT = 5
PLAYER_RADIUS = 20

MOVEMENT_SPEED = 8
START_SPEED = 3
SPEED_INCREASE = 0.001
MAX_SPEED = 12

FONT_GAME_OVER = pygame.font.SysFont("Arial", 72, bold=True)
FONT_RETRY = pygame.font.SysFont("Arial", 30)
FONT_SCORE = pygame.font.SysFont("Arial", 30, bold=True)

def create_main_surface(screen_size):
    return pygame.display.set_mode(screen_size)

def create_blocks(level_mode="down"):
    blocks = []
    for _ in range(BLOCK_COUNT):
        size = random.randint(20, 60)
        if level_mode == "side":
            bx = random.randint(SCREEN_SIZE[0], SCREEN_SIZE[0] + 500)
            by = random.randint(0, SCREEN_SIZE[1] - size)
        elif level_mode == "up":
            bx = random.randint(0, SCREEN_SIZE[0] - size)
            by = random.randint(SCREEN_SIZE[1], SCREEN_SIZE[1] + 500)
        else:
            bx = random.randint(0, SCREEN_SIZE[0] - size)
            by = random.randint(-500, 0)
        blocks.append([bx, by, size])
    return blocks

def update_blocks(blocks, fall_speed, current_score, level_mode):
    for block in blocks:
        if level_mode == "side":
            block[0] += fall_speed 
            if block[0] < -block[2]:
                block[2] = random.randint(20, 60)
                block[0] = random.randint(SCREEN_SIZE[0], SCREEN_SIZE[0] + 150)
                block[1] = random.randint(0, SCREEN_SIZE[1] - block[2])
        else:
            block[1] += fall_speed
            if fall_speed > 0 and block[1] > SCREEN_SIZE[1]: 
                block[2] = random.randint(20, 60)
                block[1] = random.randint(-150, 0)
                block[0] = random.randint(0, SCREEN_SIZE[0] - block[2])
            elif fall_speed < 0 and block[1] < -block[2]: 
                block[2] = random.randint(20, 60)
                block[1] = random.randint(SCREEN_SIZE[1], SCREEN_SIZE[1] + 150)
                block[0] = random.randint(0, SCREEN_SIZE[0] - block[2])

    zichtbare_score = current_score // 10
    extra_planeten = (zichtbare_score // 100) * 2
    if len(blocks) < BLOCK_COUNT + extra_planeten:
        size = random.randint(20, 60)
        if level_mode == "side":
            blocks.append([random.randint(SCREEN_SIZE[0], SCREEN_SIZE[0] + 150), random.randint(0, SCREEN_SIZE[1] - size), size])
        elif level_mode == "up":
            blocks.append([random.randint(0, SCREEN_SIZE[0] - size), random.randint(SCREEN_SIZE[1], SCREEN_SIZE[1] + 150), size])
        else:
            blocks.append([random.randint(0, SCREEN_SIZE[0] - size), random.randint(-150, 0), size])

def show_game_over(surface, final_score):
    waiting = True
    while waiting:
        surface.fill(BLACK)
        text_surface = FONT_GAME_OVER.render("GAME OVER", True, RED)
        score_text = "Jouw Score: " + str(final_score // 10)
        final_score_surface = FONT_RETRY.render(score_text, True, WHITE)
        retry_surface = FONT_RETRY.render("Druk op SPATIE om opnieuw te starten", True, GREEN)
        
        text_rect = text_surface.get_rect(center=(SCREEN_SIZE[0]//2, SCREEN_SIZE[1]//2 - 80))
        final_score_rect = final_score_surface.get_rect(center=(SCREEN_SIZE[0]//2, SCREEN_SIZE[1]//2))
        retry_rect = retry_surface.get_rect(center=(SCREEN_SIZE[0]//2, SCREEN_SIZE[1]//2 + 80))
        
        surface.blit(text_surface, text_rect)
        surface.blit(final_score_surface, final_score_rect)
        surface.blit(retry_surface, retry_rect)
        
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    waiting = False

def render_frame(surface, blocks, player_x, player_y, current_score, heart_img, current_lives, immunity_timer, background_img, img_small, img_medium, img_large, player_img, portal_rect=None, portal_img=None ):
    surface.fill(BLACK)
    surface.blit(background_img, (0,0))
    if portal_rect and portal_img:
        surface.blit(portal_img, (portal_rect.x, portal_rect.y))
    
    for block in blocks:
        x_pos, y_pos, size = block[0], block[1], block[2]
        if size < 40:
            chosen_img = img_small
        elif size < 50:
            chosen_img = img_medium
        else:
            chosen_img = img_large
        scaled_meteor = pygame.transform.scale(chosen_img, (size, size))
        surface.blit(scaled_meteor, (x_pos, y_pos))

    if immunity_timer == 0 or (immunity_timer // 5) % 2 == 0:
        img_rect = player_img.get_rect(center=(int(player_x), int(player_y)))
        surface.blit(player_img, img_rect)    
    
    score_display = "Score: " + str(current_score // 10)
    score_surface = FONT_SCORE.render(score_display, True, WHITE)
    surface.blit(score_surface, (SCREEN_SIZE[0] - 180, 20))
    
    for i in range(current_lives):
        surface.blit(heart_img, (20 + (i * 35), 20))
    pygame.display.flip()

def main():
    surface = create_main_surface(SCREEN_SIZE)
    pygame.display.set_caption("Ontwijk de blokken!")
    clock = pygame.time.Clock()

    player_img = pygame.image.load("images/spaceshipp.png").convert_alpha()
    player_img = pygame.transform.scale(player_img, (PLAYER_RADIUS * 2, PLAYER_RADIUS * 2))
    background_image = pygame.image.load("images/galaxy.png").convert()
    background_image = pygame.transform.scale(background_image, SCREEN_SIZE)
    meteor_small = pygame.image.load("images/neptunus.png").convert_alpha()
    meteor_medium = pygame.image.load("images/mars.png").convert_alpha()
    meteor_large = pygame.image.load("images/jupiter.png").convert_alpha()
    heart_image = pygame.image.load("images/lives.png").convert_alpha()
    heart_image = pygame.transform.scale(heart_image, (30, 30))
    portal_img = pygame.image.load("images/portal.png").convert_alpha()
    portal_img = pygame.transform.scale(portal_img, (200, 40))

    x, y = SCREEN_SIZE[0] // 2, SCREEN_SIZE[1] - 100
    x_velocity, y_velocity = 0, 0
    blocks = create_blocks()
    fall_speed = START_SPEED
    score, lives, immunity_timer = 0, 3, 0
    level_flipped, level_side = False, False

    running = True
    while running:
        clock.tick(60)
        zichtbare_score = score // 10
        portal1_active = (zichtbare_score >= 500 and not level_flipped)
        portal2_active = (zichtbare_score >= 1000 and level_flipped and not level_side)
        is_portal_active = portal1_active or portal2_active

        if immunity_timer > 0:
            immunity_timer -= 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False
                if event.key == pygame.K_RIGHT: x_velocity = MOVEMENT_SPEED
                if event.key == pygame.K_LEFT: x_velocity = -MOVEMENT_SPEED
                if event.key == pygame.K_UP: y_velocity = -MOVEMENT_SPEED
                if event.key == pygame.K_DOWN: y_velocity = MOVEMENT_SPEED
            if event.type == pygame.KEYUP:
                if event.key in [pygame.K_RIGHT, pygame.K_LEFT]: x_velocity = 0
                if event.key in [pygame.K_UP, pygame.K_DOWN]: y_velocity = 0

        if not is_portal_active:
            x += x_velocity
            y += y_velocity
        else:
            x_velocity, y_velocity = 0, 0

        score += 1

        if not level_flipped:
            fall_speed = min(START_SPEED + (score * SPEED_INCREASE), MAX_SPEED)
            level_mode = "down"
        elif level_flipped and not level_side:
            fall_speed = max(-START_SPEED - (score * SPEED_INCREASE), -MAX_SPEED)
            level_mode = "up"
        else:
            fall_speed = max(-START_SPEED - (score * SPEED_INCREASE), -MAX_SPEED)
            level_mode = "side"

        update_blocks(blocks, fall_speed, score, level_mode)

        x = max(PLAYER_RADIUS, min(SCREEN_SIZE[0] - PLAYER_RADIUS, x))
        y = max(PLAYER_RADIUS, min(SCREEN_SIZE[1] - PLAYER_RADIUS, y))
        player_rect = pygame.Rect(x - PLAYER_RADIUS, y - PLAYER_RADIUS, PLAYER_RADIUS * 2, PLAYER_RADIUS * 2)

        portal_rect = None
        if portal1_active:
            portal_rect = pygame.Rect(SCREEN_SIZE[0]//2 - 100, 20, 200, 40)
        elif portal2_active:
            portal_rect = pygame.Rect(SCREEN_SIZE[0]//2 - 100, SCREEN_SIZE[1] - 40, 200, 40)

        if portal_rect:
            portal_center = portal_rect.center
            x += (portal_center[0] - x) * 0.05
            y += (portal_center[1] - y) * 0.05

            if player_rect.colliderect(portal_rect):
                for i in range(40):
                    render_frame(surface, blocks, x, y, score, heart_image, lives, 0, background_image, meteor_small, meteor_medium, meteor_large, pygame.Surface((0,0)), portal_rect, portal_img)
                    x += (portal_center[0] - x) * 0.2
                    y += (portal_center[1] - y) * 0.2
                    current_size = int((PLAYER_RADIUS * 2) * (1 - i/40))
                    if current_size > 0:
                        scaled_ship = pygame.transform.scale(player_img, (current_size, current_size))            
                        surface.blit(scaled_ship, scaled_ship.get_rect(center=(int(x), int(y))))
                    pygame.display.flip()
                    clock.tick(60)
                
                if not level_flipped:
                    level_flipped = True
                    x, y = SCREEN_SIZE[0]//2, 100 
                    blocks = create_blocks("up") 
                else:
                    level_side = True
                    x, y = 100, SCREEN_SIZE[1]//2 
                    blocks = create_blocks("side") 
                continue

        for block in blocks:
            block_rect = pygame.Rect(block[0], block[1], block[2], block[2])
            if player_rect.colliderect(block_rect) and immunity_timer == 0 and not is_portal_active:                
                lives -= 1
                render_frame(surface, blocks, x, y, score, heart_image, lives, 1, background_image, meteor_small, meteor_medium, meteor_large, player_img, portal_rect, portal_img )
                pygame.time.delay(300)
                immunity_timer = 90
                if lives <= 0:
                    show_game_over(surface, score) 
                    lives, score, fall_speed = 3, 0, START_SPEED
                    level_flipped, level_side = False, False
                    x, y = SCREEN_SIZE[0] // 2, SCREEN_SIZE[1] - 100
                    blocks = create_blocks("down")
                break 

        render_frame(surface, blocks, x, y, score, heart_image, lives, immunity_timer, background_image, meteor_small, meteor_medium, meteor_large, player_img, portal_rect, portal_img)

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()