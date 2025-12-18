import pygame
import random
import sys

pygame.init()

BLACK = (0, 0, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
SCREEN_SIZE = (1024, 768)
BLOCK_COUNT = 3
PLAYER_RADIUS = 20
MOVEMENT_SPEED = 8
START_SPEED = 3
SPEED_INCREASE = 0.0005
MAX_SPEED = 12
MAX_BLOCKS = 15

FONT_GAME_OVER = pygame.font.SysFont("Arial", 72, bold=True)
FONT_RETRY = pygame.font.SysFont("Arial", 30)
FONT_SCORE = pygame.font.SysFont("Arial", 30, bold=True)

def create_main_surface(screen_size):
    return pygame.display.set_mode(screen_size)

def create_blocks():
    blocks = []
    for _ in range(BLOCK_COUNT):
        size = random.randint(20, 60)
        bx = random.randint(0, SCREEN_SIZE[0] - size)
        by = random.randint(-500, 0)
        blocks.append([bx, by, size])
    return blocks

def update_blocks(blocks, fall_speed, current_score):
    for block in blocks:
        block[1] += fall_speed
        if block[1] > SCREEN_SIZE[1]: 
            block[2] = random.randint(20, 60)
            block[1] = random.randint(-150, 0)
            block[0] = random.randint(0, SCREEN_SIZE[0] - block[2])

    zichtbare_score = current_score // 10
    aantal_planeten = BLOCK_COUNT + (zichtbare_score // 50) * 1

    if aantal_planeten > MAX_BLOCKS:
        aantal_planeten = MAX_BLOCKS

    if len(blocks) < aantal_planeten:
        size = random.randint(20, 60)
        blocks.append([random.randint(0, SCREEN_SIZE[0] - size), random.randint(-150, 0), size])

def show_game_over(surface, final_score):
    waiting = True
    while waiting:
        surface.fill(BLACK)
        text_surface = FONT_GAME_OVER.render("GAME OVER", True, RED)
        score_text = "Jouw Score: " + str(final_score // 10)
        final_score_surface = FONT_RETRY.render(score_text, True, WHITE)
        retry_surface = FONT_RETRY.render("Druk op SPATIE om opnieuw te starten", True, GREEN)
        
        surface.blit(text_surface, text_surface.get_rect(center=(SCREEN_SIZE[0]//2, SCREEN_SIZE[1]//2 - 80)))
        surface.blit(final_score_surface, final_score_surface.get_rect(center=(SCREEN_SIZE[0]//2, SCREEN_SIZE[1]//2)))
        surface.blit(retry_surface, retry_surface.get_rect(center=(SCREEN_SIZE[0]//2, SCREEN_SIZE[1]//2 + 80)))
        
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    waiting = False

def render_frame(surface, blocks, player_x, player_y, current_score, heart_img, current_lives, immunity_timer, background_img, img_small, img_medium, img_large, player_img):
    surface.fill(BLACK)
    surface.blit(background_img, (0,0))
    
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
    
    score_surface = FONT_SCORE.render("Score: " + str(current_score // 10), True, WHITE)
    surface.blit(score_surface, (SCREEN_SIZE[0] - 180, 20))
    
    for i in range(current_lives):
        surface.blit(heart_img, (20 + (i * 35), 20))
    pygame.display.flip()

def main():
    surface = create_main_surface(SCREEN_SIZE)
    pygame.display.set_caption("Ontwijk de planeten!")
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

    x, y = SCREEN_SIZE[0] // 2, SCREEN_SIZE[1] - 100
    x_velocity, y_velocity = 0, 0
    blocks = create_blocks()
    score, lives, immunity_timer = 0, 3, 0

    running = True
    while running:
        clock.tick(60)
        if immunity_timer > 0:
            immunity_timer -= 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT: x_velocity = MOVEMENT_SPEED
                if event.key == pygame.K_LEFT: x_velocity = -MOVEMENT_SPEED
                if event.key == pygame.K_UP: y_velocity = -MOVEMENT_SPEED
                if event.key == pygame.K_DOWN: y_velocity = MOVEMENT_SPEED
            if event.type == pygame.KEYUP:
                if event.key in [pygame.K_RIGHT, pygame.K_LEFT]: x_velocity = 0
                if event.key in [pygame.K_UP, pygame.K_DOWN]: y_velocity = 0

        x += x_velocity
        y += y_velocity
        score += 1

        fall_speed = min(START_SPEED + (score * SPEED_INCREASE), MAX_SPEED)
        update_blocks(blocks, fall_speed, score)

        x = max(PLAYER_RADIUS, min(SCREEN_SIZE[0] - PLAYER_RADIUS, x))
        y = max(PLAYER_RADIUS, min(SCREEN_SIZE[1] - PLAYER_RADIUS, y))
        player_rect = pygame.Rect(x - PLAYER_RADIUS, y - PLAYER_RADIUS, PLAYER_RADIUS * 2, PLAYER_RADIUS * 2)

        for block in blocks:
            block_rect = pygame.Rect(block[0], block[1], block[2], block[2])
            if player_rect.colliderect(block_rect) and immunity_timer == 0:                
                lives -= 1
                render_frame(surface, blocks, x, y, score, heart_image, lives, 1, background_image, meteor_small, meteor_medium, meteor_large, player_img)
                pygame.time.delay(300)
                immunity_timer = 90
                if lives <= 0:
                    show_game_over(surface, score) 
                    lives, score = 3, 0
                    x, y = SCREEN_SIZE[0] // 2, SCREEN_SIZE[1] - 100
                    blocks = create_blocks()
                break 

        render_frame(surface, blocks, x, y, score, heart_image, lives, immunity_timer, background_image, meteor_small, meteor_medium, meteor_large, player_img)

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()