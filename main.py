import pygame
import audio
import audio_path
pygame.init()



#scherm
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Hier Moet Onze Game Naam Komen")    





#main loop

running = True
while running:
    pygame.time.delay(10)


    for event in pygame.event.get():
       if event.type == pygame.QUIT:
           running = False

pygame.quit()