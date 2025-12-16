import pygame
pygame.init()

SCREEN_WIDTH = 1024 
SCREEN_HEIGHT = 768
x=500
y=300
speed = 5
radius = 25

spaceship = pygame.image.load('./images/spaceship.png')
spaceship = pygame.transform.scale(spaceship, (150,150))

pygame.display.set_caption("Dodge Master")
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

def redraw_screen():
    screen.blit(spaceship, (x,y))
    pygame.display.update()

running = True
while running:
    pygame.time.delay(10)

    

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    if keys[pygame.K_q] and x > -15:
        x -= speed
    if keys[pygame.K_d] and x < SCREEN_WIDTH - 135:
        x += speed
    if keys[pygame.K_z] and y > -15:
        y -= speed
    if keys[pygame.K_s] and y < SCREEN_HEIGHT - 135:
        y += speed
    screen.fill((0,0,0))

    redraw_screen()
pygame.quit()