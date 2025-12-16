import pygame
import random
import sys


pygame.init()

BLACK = (0, 0, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 100, 255)
GREEN = (0, 255, 0)

SCREEN_SIZE = (1024, 768)
BLOCK_COUNT = 30
PLAYER_RADIUS = 20

MOVEMENT_SPEED = 2
START_SPEED = 3
SPEED_INCREASE = 0.002
MAX_SPEED = 12


FONT_GAME_OVER = pygame.font.SysFont("Arial", 72, bold=True)
FONT_RETRY = pygame.font.SysFont("Arial", 30)
FONT_SCORE = pygame.font.SysFont("Arial", 30, bold=True)

def create_main_surface(screen_size):
    return pygame.display.set_mode(screen_size)

def create_blocks():
    blocks = []
    for _ in range(BLOCK_COUNT):
        size = random.randint(20,60)
        x = random.randint(0, SCREEN_SIZE[0] - size)
        y = random.randint(-SCREEN_SIZE[1], 0)
        blocks.append([x, y, size])
    return blocks

def update_blocks(blocks, fall_speed):
    for block in blocks:
        block[1] += fall_speed
        if block[1] > SCREEN_SIZE[1]:
            block[2] = random.randint(20, 60)
            block[1] = random.randint(-150, 0)
            block[0] = random.randint(0, SCREEN_SIZE[0] - block[2])

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

def render_frame(surface, blocks, player_x, player_y, current_score, heart_img, current_lives, immunity_timer, background_img, spaceship_img):
    surface.fill(BLACK)
    surface.blit(background_img, (0,0))
    
    
    for block in blocks:
        pygame.draw.rect(surface, RED, (block[0], block[1], block[2], block[2]))

    if immunity_timer == 0 or (immunity_timer // 5) % 2 == 0:
        if spaceship_img:
            draw_x = int(player_x - PLAYER_RADIUS)
            draw_y = int(player_y - PLAYER_RADIUS)
            surface.blit(spaceship_img, (draw_x, draw_y))
        else:
            pygame.draw.circle(surface, BLUE, (int(player_x), int(player_y)), PLAYER_RADIUS)
    
    
    
    
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

    background_image = pygame.image.load("images/galaxy.png").convert()
    background_image = pygame.transform.scale(background_image, SCREEN_SIZE)

    
    heart_image = pygame.image.load("images/lives.png").convert_alpha()
    heart_image = pygame.transform.scale(heart_image, (30, 30))

    try:
        spaceship_image = pygame.image.load("images/spaceshipp.png").convert_alpha()
        spaceship_image = pygame.transform.scale(spaceship_image, (PLAYER_RADIUS * 2, PLAYER_RADIUS * 2))
    except pygame.error:
        spaceship_image = None
    
    
    x = SCREEN_SIZE[0] // 2
    y = SCREEN_SIZE[1] - 100
    x_velocity = 0
    y_velocity = 0
    blocks = create_blocks()
    fall_speed = START_SPEED
    score = 0
    lives = 3
    immunity_timer = 0

    running = True
    while running:
        clock.tick(60)

        if immunity_timer > 0:
            immunity_timer -= 1
        

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_d: 
                    x_velocity = MOVEMENT_SPEED
                if event.key == pygame.K_q: 
                    x_velocity = -MOVEMENT_SPEED
                if event.key == pygame.K_z:
                    y_velocity = -MOVEMENT_SPEED
                if event.key == pygame.K_s:
                    y_velocity = MOVEMENT_SPEED
            
            if event.type == pygame.KEYUP:
                if event.key in [pygame.K_d, pygame.K_q]:
                    x_velocity = 0
            if event.type == pygame.KEYUP:
                if event.key in [pygame.K_z, pygame.K_s]:
                    y_velocity = 0

        
        x += x_velocity
        y += y_velocity
        score += 1 
        fall_speed = min(fall_speed + SPEED_INCREASE, MAX_SPEED)
        update_blocks(blocks, fall_speed)

      
        if x < PLAYER_RADIUS: x = PLAYER_RADIUS
        if x > SCREEN_SIZE[0] - PLAYER_RADIUS: x = SCREEN_SIZE[0] - PLAYER_RADIUS

        player_rect = pygame.Rect(x - PLAYER_RADIUS, y - PLAYER_RADIUS, PLAYER_RADIUS * 2, PLAYER_RADIUS * 2)
        
        for block in blocks:
            block_rect = pygame.Rect(block[0], block[1], block[2], block[2])
            
            if player_rect.colliderect(block_rect) and immunity_timer == 0: 
                lives -= 1
                render_frame(surface, blocks, x, y, score, heart_image, lives, 1, background_image, spaceship_image)
                pygame.time.delay(300)
                immunity_timer = 90
                
                if lives <= 0:
                    show_game_over(surface, score) 
                    lives = 3 
                    score = 0
                    fall_speed = START_SPEED
                
                    x = SCREEN_SIZE[0] // 2
                    y = SCREEN_SIZE[1] - 100
                    x_velocity = 0
                    y_velocity = 0
                    blocks = create_blocks()
                break 

        
        render_frame(surface, blocks, x, y, score, heart_image, lives, immunity_timer, background_image, spaceship_image)

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()