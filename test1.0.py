
from pygame.draw import circle
from pygame.display import flip





MOVEMENT_SPEED = 0.5 

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
    
    # Startpositie
    x = surface.get_width() // 2 
    y = surface.get_height() // 2 
    
    # --- Nieuwe Snelheidsvariabele voor vloeiende beweging ---
    x_velocity = 0 # Houdt de huidige snelheid in de x-richting bij
    
    running = True
    while running:
        # Event Handling: Verwerken van alle gebeurtenissen
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            
            # 1. Toets ingedrukt (KEYDOWN) - Start de beweging
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_d:
                    x_velocity = MOVEMENT_SPEED  # Snelheid instellen op +5 (rechts)
                elif event.key == pygame.K_q:
                    x_velocity = -MOVEMENT_SPEED # Snelheid instellen op -5 (links)
            
            # 2. Toets losgelaten (KEYUP) - Stop de beweging
            if event.type == pygame.KEYUP:
                # Als de losgelaten toets D of Q is, stop dan de beweging door de snelheid op 0 te zetten
                if event.key == pygame.K_d or event.key == pygame.K_q:
                    x_velocity = 0

        # --- Update-fase (buiten de event-lus) ---
        # 3. Positie bijwerken door de snelheid toe te voegen
        x += x_velocity

        render_frame(surface, x, y)
        
    pygame.quit()

if __name__ == '__main__':
    main()