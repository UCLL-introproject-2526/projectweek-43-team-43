import pygame
import random
import sys


pygame.init()

BLACK = (0, 0, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 100, 255)
GREEN = (0, 255, 0)
PURPLE = (138, 43, 226)

SCREEN_SIZE = (1024, 768)
BLOCK_COUNT = 1
PLAYER_RADIUS = 20

MOVEMENT_SPEED = 7
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
        if fall_speed > 0 and block[1] > SCREEN_SIZE[1]:
            block[2] = random.randint(20, 60)
            block[1] = random.randint(-150, 0)
            block[0] = random.randint(0, SCREEN_SIZE[0] - block[2])
        
        elif fall_speed < 0 and block[1] < -block[2]:
            block[2] = random.randint(20, 60)
            block[1] = random.randint(SCREEN_SIZE[1], SCREEN_SIZE[1] + 150)
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

def render_frame(surface, blocks, player_x, player_y, current_score, heart_img, current_lives, immunity_timer, background_img, img_small, img_medium, img_large, portal_rect=None, portal_img=None):
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

    meteor_small = pygame.image.load("images/neptunus.png").convert_alpha()
    meteor_medium = pygame.image.load("images/mars.png").convert_alpha()
    meteor_large = pygame.image.load("images/jupiter.png").convert_alpha()


    
    heart_image = pygame.image.load("images/lives.png").convert_alpha()
    heart_image = pygame.transform.scale(heart_image, (30, 30))

    portal_img = pygame.image.load("images/portal.png").convert_alpha()
    portal_img = pygame.transform.scale(portal_img, (200, 40))

    
    x = SCREEN_SIZE[0] // 2
    y = SCREEN_SIZE[1] - 100
    x_velocity = 0
    y_velocity = 0
    blocks = create_blocks()
    fall_speed = START_SPEED
    score = 0
    lives = 3
    immunity_timer = 0

    level_flipped = False
    portal_active = False

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
                if event.key == pygame.K_RIGHT: 
                    x_velocity = MOVEMENT_SPEED
                if event.key == pygame.K_LEFT: 
                    x_velocity = -MOVEMENT_SPEED
                if event.key == pygame.K_UP: 
                    y_velocity = -MOVEMENT_SPEED
                if event.key == pygame.K_DOWN:
                    y_velocity = MOVEMENT_SPEED
            
            if event.type == pygame.KEYUP:
                if event.key in [pygame.K_RIGHT, pygame.K_LEFT]:
                    x_velocity = 0
            if event.type == pygame.KEYUP:
                if event.key in [pygame.K_UP, pygame.K_DOWN]:
                    y_velocity = 0

        
        x += x_velocity
        y += y_velocity
        score += 1 
        if not level_flipped:
            fall_speed = min(fall_speed + SPEED_INCREASE, MAX_SPEED)
        else:
            fall_speed = max(fall_speed - SPEED_INCREASE, -MAX_SPEED)
        update_blocks(blocks, fall_speed)

      
        if x < PLAYER_RADIUS: x = PLAYER_RADIUS
        if x > SCREEN_SIZE[0] - PLAYER_RADIUS: x = SCREEN_SIZE[0] - PLAYER_RADIUS
        if y < PLAYER_RADIUS: y = PLAYER_RADIUS
        if y > SCREEN_SIZE[1] - PLAYER_RADIUS: y = SCREEN_SIZE[1] - PLAYER_RADIUS

        player_rect = pygame.Rect(x - PLAYER_RADIUS, y - PLAYER_RADIUS, PLAYER_RADIUS * 2, PLAYER_RADIUS * 2)

        portal_rect = None
        if score // 10 >= 100 and not level_flipped:
            portal_active = True
            
            portal_rect = pygame.Rect(SCREEN_SIZE[0]//2 - 100, 20, 200, 40)
            portal_center = (portal_rect.centerx, portal_rect.centery)

            dist_x = portal_center[0] - x
            dist_y = portal_center[1] - y
            
            x += dist_x * 0.05
            y += dist_y * 0.05

            if player_rect.colliderect(portal_rect):
                for i in range(40):
                   
                    render_frame(surface, blocks, x, y, score, heart_image, lives, 0, background_image, meteor_small, meteor_medium, meteor_large, portal_rect, portal_img)
                    
                   
                    x += (portal_center[0] - x) * 0.2
                    y += (portal_center[1] - y) * 0.2
                    
                    radius = int(PLAYER_RADIUS * (1 - i/40))
                    if radius > 0:
                        pygame.draw.circle(surface, BLUE, (int(x), int(y)), radius)
                    
                    pygame.display.flip()
                    clock.tick(60)

                
                level_flipped = True
                portal_active = False
                fall_speed = -fall_speed 
                x, y = SCREEN_SIZE[0]//2, 100 
                
                blocks = [] 
                for _ in range(BLOCK_COUNT):
                    size = random.randint(20, 60)
                    bx = random.randint(0, SCREEN_SIZE[0] - size)                    
                    by = random.randint(SCREEN_SIZE[1], SCREEN_SIZE[1] + 500)
                    blocks.append([bx, by, size])
                    
                continue 
            

        
        for block in blocks:
            block_rect = pygame.Rect(block[0], block[1], block[2], block[2])
            
            if player_rect.colliderect(block_rect) and immunity_timer == 0:                
                lives -= 1
                render_frame(surface, blocks, x, y, score, heart_image, lives, 1, background_image, meteor_small, meteor_medium, meteor_large, portal_rect, portal_img)
                pygame.time.delay(300)
                immunity_timer = 90
                
                if lives <= 0:
                    show_game_over(surface, score) 
                    lives = 3  
                    score = 0
                    fall_speed = START_SPEED
                    level_flipped = False
                    x = SCREEN_SIZE[0] // 2
                    y = SCREEN_SIZE[1] - 100
                    x_velocity = 0
                    blocks = create_blocks()
                break 

        
        render_frame(surface, blocks, x, y, score, heart_image, lives, immunity_timer, background_image, meteor_small, meteor_medium, meteor_large, portal_rect, portal_img)

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()