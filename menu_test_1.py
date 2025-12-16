import pygame
import pygame.freetype
from enum import Enum
from pygame.sprite import Sprite, RenderUpdates

# --- INSTELLINGEN ---
# Hier passen we de resolutie aan zoals in je eerste screenshot
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
CENTER_X = SCREEN_WIDTH / 2

BLUE = (106, 159, 181)
WHITE = (255, 255, 255)
RED = (255, 0 , 0)

class GameState(Enum):
    QUIT = -1
    TITLE = 0
    PLAYING = 1
    GAMEOVER = 2
    OPTIONS = 3



def create_surface_with_text(text, font_size, text_rgb, bg_rgb):
    """ Hulpfunctie om tekst om te zetten in een plaatje """
    font = pygame.freetype.SysFont("Courier", font_size, bold=True)
    surface, _ = font.render(text=text, fgcolor=text_rgb, bgcolor=bg_rgb)
    return surface.convert_alpha()


class UIElement(Sprite):
    def __init__(self, center_position, text, font_size, bg_rgb, text_rgb, action=None):
        super().__init__()
        self.mouse_over = False 
        self.action = action 

        default_image = create_surface_with_text(text, font_size, text_rgb, bg_rgb)
        highlighted_image = create_surface_with_text(text, int(font_size * 1.2), text_rgb, bg_rgb)

        self.images = [default_image, highlighted_image]
        self.rects = [
            default_image.get_rect(center=center_position),
            highlighted_image.get_rect(center=center_position),
        ]

    # --- BELANGRIJK: DE FIX VOOR JE FOUTMELDING ---
    # De '@property' zorgt ervoor dat we self.image kunnen gebruiken als variabele
    # in plaats van als functie. Zonder dit crasht de game.
    @property
    def image(self):
        return self.images[1] if self.mouse_over else self.images[0]

    @property
    def rect(self):
        return self.rects[1] if self.mouse_over else self.rects[0]
    

    def update(self, mouse_pos, mouse_up):
    
        if self.rect.collidepoint(mouse_pos):
            self.mouse_over = True
            if mouse_up:
                return self.action
        else:
            self.mouse_over = False
        return None
    
    def draw(self, surface):
        surface.blit(self.image, self.rect)


def game_loop(screen, buttons):
    
    while True:
        mouse_up = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return GameState.QUIT
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                mouse_up = True

        screen.fill(BLUE)

        for button in buttons:
            ui_action = button.update(pygame.mouse.get_pos(), mouse_up)
            if ui_action is not None:
                return ui_action
            button.draw(screen)

        pygame.display.flip()


def title_screen(screen):
    options_btn = UIElement(
        center_position=(CENTER_X, 400),
        font_size=30,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text="Options",
        action=GameState.OPTIONS,
    )

    start_btn = UIElement(
        center_position=(CENTER_X, 350), #in het midden
        font_size=30,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text="Start Game",
        action=GameState.PLAYING,
    )
    quit_btn = UIElement(
        center_position=(CENTER_X, 450),
        font_size=30,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text="Afsluiten",
        action=GameState.QUIT,
    )
    return game_loop(screen, RenderUpdates(start_btn, quit_btn, options_btn))

def options_screen(screen):
    TITLE = UIElement(
        center_position=(CENTER_X, 250),
        font_size=50,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text="SETTINGS",
        action=None,
    )

    sound_btn = UIElement(
        center_position=(CENTER_X, 150),  
        font_size=30,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text="Sound: ON",
        action=None,
    )

    controls_button = UIElement(
        center_position=(CENTER_X, 325),
        font_size=30,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text="CONTROLS",
        action=None,
    )

    

    back_btn = UIElement(
        center_position=(CENTER_X, 600),
        font_size=50,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text="Back",
        action=GameState.TITLE,
    )

    return game_loop(screen, RenderUpdates(TITLE, back_btn))



def play_level(screen):
    
    info_text = UIElement(
        center_position=(CENTER_X, 300),
        font_size=20,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text="(Hier moet de gameplay komen)",
        action=None,
    )
    
    stop_btn = UIElement(
        center_position=(CENTER_X, 400),
        font_size=30,
        bg_rgb=BLUE,
        text_rgb=RED,
        text="Simuleer 'Game Over'",
        action=GameState.GAMEOVER,
    )
    return game_loop(screen, RenderUpdates(info_text, stop_btn))

def game_over_screen(screen):
    tekst_btn = UIElement(
        center_position=(CENTER_X, 200),
        font_size=50,
        bg_rgb=BLUE,
        text_rgb=RED,
        text="GAME OVER",
        action=None,
    )
    restart_btn = UIElement(
        center_position=(CENTER_X, 350),
        font_size=30,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text="Opnieuw spelen",
        action=GameState.PLAYING,
    )
    menu_btn = UIElement(
        center_position=(CENTER_X, 450),
        font_size=30,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text="Hoofdmenu",
        action=GameState.TITLE,
    )
    return game_loop(screen, RenderUpdates(tekst_btn, restart_btn, menu_btn))


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Dodge Blocks - Menu Test")
    
    game_state = GameState.TITLE

    while True:
        if game_state == GameState.TITLE:
            game_state = title_screen(screen)

        if game_state == GameState.PLAYING:
            game_state = play_level(screen)
        
        if game_state == GameState.GAMEOVER:
            game_state = game_over_screen(screen)
        
        if game_state == GameState.OPTIONS:
            game_state = options_screen(screen)
        
        

        if game_state == GameState.QUIT:
            pygame.quit()
            return

if __name__ == "__main__":
    main()