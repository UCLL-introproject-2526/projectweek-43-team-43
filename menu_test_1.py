import pygame
import pygame.freetype
from enum import Enum
from pygame.sprite import Sprite, RenderUpdates

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
CENTER_X = SCREEN_WIDTH / 2


KEY_LEFT = pygame.K_LEFT
KEY_RIGHT = pygame.K_RIGHT
KEY_UP = pygame.K_UP
KEY_DOWN = pygame.K_DOWN

BLUE = (106, 159, 181)
WHITE = (255, 255, 255)
RED = (255, 0 , 0)
YELLOW = (255, 255, 0) 

class GameState(Enum):
    QUIT = -1
    TITLE = 0
    PLAYING = 1
    GAMEOVER = 2
    OPTIONS = 3
    CONTROLS = 6

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

    
    def set_text(self, text, font_size, bg_rgb, text_rgb):
        default_image = create_surface_with_text(text, font_size, text_rgb, bg_rgb)
        highlighted_image = create_surface_with_text(text, int(font_size * 1.2), text_rgb, bg_rgb)

        self.images = [default_image, highlighted_image]
        
        
        current_center = self.rects[0].center
        self.rects = [
            default_image.get_rect(center=current_center),
            highlighted_image.get_rect(center=current_center),
        ]

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



def wait_for_key():
    """ Wacht tot de gebruiker een toets indrukt (staat nu BUITEN de class) """
    while True:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                return event.key

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
        font_size=50,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text="Options",
        action=GameState.OPTIONS,
    )

    start_btn = UIElement(
        center_position=(CENTER_X, 250),
        font_size=50,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text="Start Game",
        action=GameState.PLAYING,
    )
    quit_btn = UIElement(
        center_position=(CENTER_X, 550),
        font_size=50,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text="Afsluiten",
        action=GameState.QUIT,
    )
    return game_loop(screen, RenderUpdates(start_btn, quit_btn, options_btn))

def options_screen(screen):
    TITLE = UIElement(
        center_position=(CENTER_X, 150),
        font_size=50,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text="VIDEO SETTINGS",
        action=None,
    )

    sound_btn = UIElement(
        center_position=(CENTER_X, 300),  
        font_size=50,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text="Sound: ON",
        action=None,
    )

    controls_button = UIElement(
        center_position=(CENTER_X, 450),
        font_size=50,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text="CONTROLS",
        action=GameState.CONTROLS,
    )

    back_btn = UIElement(
        center_position=(CENTER_X, 600),
        font_size=50,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text="Back",
        action=GameState.TITLE,
    )

    return game_loop(screen, RenderUpdates(TITLE, back_btn, controls_button, sound_btn))

def control_screen(screen):
    global KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN

    TITLE = UIElement(
        center_position=(CENTER_X, 100),
        font_size=50,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text="CLICK TO CHANGE KEYS",
        action=None,
    )

    btn_left = UIElement(
        center_position=(CENTER_X, 200),
        font_size=25,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text=f"move left: {pygame.key.name(KEY_LEFT).upper()}",
        action="CHANGE_LEFT",
    )

    btn_right = UIElement(
        center_position=(CENTER_X, 300),
        font_size=25, 
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text=f"move right: {pygame.key.name(KEY_RIGHT).upper()}",
        action="CHANGE_RIGHT",
    )

    btn_down = UIElement(
        center_position=(CENTER_X, 400),
        font_size=25,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text=f"move down: {pygame.key.name(KEY_DOWN).upper()}",
        action="CHANGE_DOWN",
    )

    btn_up = UIElement(
        center_position=(CENTER_X, 500),
        font_size=25,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text=f"move up: {pygame.key.name(KEY_UP).upper()}",
        action="CHANGE_UP",
    )

    back_btn = UIElement(
        center_position=(CENTER_X, 600),
        font_size=30,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text="Back to Options",
        action=GameState.OPTIONS,
    )

    buttons = RenderUpdates(TITLE, btn_left, btn_right, btn_down, btn_up, back_btn)

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
                
                if isinstance(ui_action, GameState):
                    return ui_action
                
                
                
                if ui_action == "CHANGE_LEFT":
                    button.set_text("PRESS ANY KEY...", 25, BLUE, YELLOW)
                    button.draw(screen)
                    pygame.display.flip()
                    
                    KEY_LEFT = wait_for_key() 
                    button.set_text(f"move left: {pygame.key.name(KEY_LEFT).upper()}", 25, BLUE, WHITE)

                elif ui_action == "CHANGE_RIGHT":
                    button.set_text("PRESS ANY KEY...", 25, BLUE, YELLOW)
                    button.draw(screen)
                    pygame.display.flip()
                    
                    KEY_RIGHT = wait_for_key()
                    button.set_text(f"move right: {pygame.key.name(KEY_RIGHT).upper()}", 25, BLUE, WHITE)

                elif ui_action == "CHANGE_DOWN":
                    button.set_text("PRESS ANY KEY...", 25, BLUE, YELLOW)
                    button.draw(screen)
                    pygame.display.flip()
                    
                    KEY_DOWN = wait_for_key()
                    button.set_text(f"move down: {pygame.key.name(KEY_DOWN).upper()}", 25, BLUE, WHITE)

                elif ui_action == "CHANGE_UP":
                    button.set_text("PRESS ANY KEY...", 25, BLUE, YELLOW)
                    button.draw(screen)
                    pygame.display.flip()
                    
                    KEY_UP = wait_for_key()
                    button.set_text(f"move up: {pygame.key.name(KEY_UP).upper()}", 25, BLUE, WHITE)

            button.draw(screen)

        pygame.display.flip()

def play_level(screen):
    info_text = UIElement(
        center_position=(CENTER_X, 300),
        font_size=20,
        bg_rgb=BLUE,
        text_rgb=WHITE,
        text="(Gebruik nu je nieuwe toetsen!)",
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
        
        if game_state == GameState.CONTROLS:
            game_state = control_screen(screen)
        
        if game_state == GameState.QUIT:
            pygame.quit()
            return

if __name__ == "__main__":
    main()