import pygame
pygame.init()

SCREEN_WIDTH = 1024 
SCREEN_HEIGHT = 768
x=500
y=300
speed = 5
radius = 25

pygame.display.set_caption("Dodge Master")
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

running = True
while running:
    pygame.time.delay(10)

    

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    if keys[pygame.K_q] and x > radius:
        x -= speed
    if keys[pygame.K_d] and x < SCREEN_WIDTH - radius:
        x += speed
    if keys[pygame.K_z] and y > radius:
        y -= speed
    if keys[pygame.K_s] and y < SCREEN_HEIGHT - radius:
        y += speed
    screen.fill((0,0,0))

    pygame.draw.circle(screen, (255, 0, 0), (x, y), radius)
    pygame.display.update()
pygame.quit()