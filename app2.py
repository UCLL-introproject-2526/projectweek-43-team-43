import pygame
from pygame.draw import circle
from pygame.display import flip

pygame.init()

BLACK = (0, 0, 0)
RED = (255, 0, 0)

def create_main_surface(screen_size):
    surface = pygame.display.set_mode(screen_size)
    return surface

def render_frame(surface, x_coord, y_coord):
    surface.fill(BLACK) 
    
    radius = 50
    
    circle(surface, RED, (x_coord, y_coord), radius)

    flip()

def main():
    screen_size = (1024, 768)
    surface = create_main_surface(screen_size)
    
    x = surface.get_width() // 2 
    y = surface.get_height() // 2
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        render_frame(surface, x, y)
        
        x += 0.2
        y += 0.3

    pygame.quit()

if __name__ == '__main__':
    main()