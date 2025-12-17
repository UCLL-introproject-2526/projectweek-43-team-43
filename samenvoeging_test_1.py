import pygame
import pygame.freetype
import random
import sys
import audio
import audio_path
from enum import Enum
from pygame.sprite import Sprite, RenderUpdates

pygame.init()
pygame.mixer.init()

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
SCREEN_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)
CENTER_X = SCREEN_WIDTH / 2

BLUE = (106, 159, 181) 
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0 , 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
GAME_BLUE = (0, 100, 255) 

BLOCK_COUNT = 30
PLAYER_RADIUS = 20
MOVEMENT_SPEED = 5 
START_SPEED = 3
SPEED_INCREASE = 0.002
MAX_SPEED = 12

KEY_LEFT = pygame.K_LEFT
KEY_RIGHT = pygame.K_RIGHT
KEY_UP = pygame.K_UP
KEY_DOWN = pygame.K_DOWN

LAST_SCORE = 0 
<<<<<<< HEAD

=======
MENU_BACKGROUND = None 

try:
    pygame.mixer.music.load("./audio/music.mp3")
    pygame.mixer.music.play(-1)
except:
    print("Let op: Muziekbestand niet gevonden.")
>>>>>>> 5cd68de8c5ed7629a8f980f666cb3a4f2765cc6e

FONT_SCORE = pygame.font.SysFont("Arial", 30, bold=True)

class GameState(Enum):
    QUIT = -1
    TITLE = 0
    PLAYING = 1
    GAMEOVER = 2
    OPTIONS = 3
    VIDEO_SETTINGS = 4
    SOUND = 5
    CONTROLS = 6

def create_surface_with_text(text, font_size, text_rgb):
    font = pygame.freetype.SysFont("Courier", font_size, bold=True)
    surface, _ = font.render(text=text, fgcolor=text_rgb, bgcolor=None)
    return surface.convert_alpha()

def key_is_taken(new_key):
    if new_key == KEY_LEFT or new_key == KEY_RIGHT or new_key == KEY_UP or new_key == KEY_DOWN:
        return True
    return False

def create_blocks():
    blocks = []
    for _ in range(BLOCK_COUNT):
        size = random.randint(20,60)
        x = random.randint(0, SCREEN_WIDTH - size)
        y = random.randint(-SCREEN_HEIGHT, 0)
        blocks.append([x, y, size])
    return blocks

def update_blocks(blocks, fall_speed):
    for block in blocks:
        block[1] += fall_speed
        if block[1] > SCREEN_HEIGHT:
            block[2] = random.randint(20, 60) 
            block[1] = random.randint(-150, 0) 
            block[0] = random.randint(0, SCREEN_WIDTH - block[2]) 

class UIElement(Sprite):
    def __init__(self, center_position, text, font_size, text_rgb, action=None):
        super().__init__()
        self.mouse_over = False 
        self.action = action 
        
        self.font_size = font_size
        self.text_rgb = text_rgb

        default_image = create_surface_with_text(text, font_size, text_rgb)
        highlighted_image = create_surface_with_text(text, int(font_size * 1.2), text_rgb)

        self.images = [default_image, highlighted_image]
        self.rects = [
            default_image.get_rect(center=center_position),
            highlighted_image.get_rect(center=center_position),
        ]

    def set_text(self, text, font_size, text_rgb):
        default_image = create_surface_with_text(text, font_size, text_rgb)
        highlighted_image = create_surface_with_text(text, int(font_size * 1.2), text_rgb)

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

        if MENU_BACKGROUND:
            screen.blit(MENU_BACKGROUND, (0,0))
        else:
            screen.fill(BLUE)

        for button in buttons:
            ui_action = button.update(pygame.mouse.get_pos(), mouse_up)
            if ui_action is not None:
                return ui_action
            button.draw(screen)

        pygame.display.flip()

def render_frame(surface, blocks, player_x, player_y, current_score, heart_img, current_lives, immunity_timer, background_img, img_small, img_medium, img_large):
    surface.fill(BLACK)
    if background_img:
        surface.blit(background_img, (0,0))
    
    for block in blocks:
        x_pos, y_pos, size = block[0], block[1], block[2]

        chosen_img = None
        if img_small and img_medium and img_large:
            if size < 40:
                chosen_img = img_small
            elif size < 50:
                chosen_img = img_medium
            else:
                chosen_img = img_large
            
            scaled_meteor = pygame.transform.scale(chosen_img, (size, size))
            surface.blit(scaled_meteor, (x_pos, y_pos))
        else:
            pygame.draw.rect(surface, WHITE, (x_pos, y_pos, size, size))

    if immunity_timer == 0 or (immunity_timer // 5) % 2 == 0:
        pygame.draw.circle(surface, GAME_BLUE, (int(player_x), int(player_y)), PLAYER_RADIUS)
    
    score_display = "Score: " + str(current_score // 10)
    score_surface = FONT_SCORE.render(score_display, True, WHITE)
    surface.blit(score_surface, (SCREEN_WIDTH - 200, 20))
    
    if heart_img:
        for i in range(current_lives):
            surface.blit(heart_img, (20 + (i * 35), 20))
    else:
        lives_surface = FONT_SCORE.render(f"Lives: {current_lives}", True, RED)
        surface.blit(lives_surface, (20, 20))
    
    pygame.display.flip()

def play_level(screen):
    global LAST_SCORE
    
    try:
        background_image = pygame.image.load("images/galaxy.png").convert()
        background_image = pygame.transform.scale(background_image, SCREEN_SIZE)

        meteor_small = pygame.image.load("images/meteoriet2.png").convert_alpha()
        meteor_medium = pygame.image.load("images/mars.png").convert_alpha()
        meteor_large = pygame.image.load("images/jupiter.png").convert_alpha()
        
        heart_image = pygame.image.load("images/lives.png").convert_alpha()
        heart_image = pygame.transform.scale(heart_image, (30, 30))
    except FileNotFoundError:
        print("Waarschuwing: Een of meer afbeeldingen niet gevonden in 'images/' map. Gebruikt fallback.")
        background_image = None
        meteor_small = None
        meteor_medium = None
        meteor_large = None
        heart_image = None

    x = SCREEN_WIDTH // 2
    y = SCREEN_HEIGHT - 100
    x_velocity = 0
    y_velocity = 0
    
    blocks = create_blocks()
    fall_speed = START_SPEED
    score = 0
    lives = 3
    immunity_timer = 0
    
    clock = pygame.time.Clock()
    running = True

    while running:
        clock.tick(60)

        if immunity_timer > 0:
            immunity_timer -= 1
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return GameState.QUIT
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return GameState.TITLE 
                
                if event.key == KEY_RIGHT: 
                    x_velocity = MOVEMENT_SPEED
                if event.key == KEY_LEFT: 
                    x_velocity = -MOVEMENT_SPEED
                if event.key == KEY_UP:
                    y_velocity = -MOVEMENT_SPEED
                if event.key == KEY_DOWN:
                    y_velocity = MOVEMENT_SPEED
            
            if event.type == pygame.KEYUP:
                if event.key == KEY_RIGHT and x_velocity > 0:
                    x_velocity = 0
                if event.key == KEY_LEFT and x_velocity < 0:
                    x_velocity = 0
                if event.key == KEY_UP and y_velocity < 0:
                    y_velocity = 0
                if event.key == KEY_DOWN and y_velocity > 0:
                    y_velocity = 0

        x += x_velocity
        y += y_velocity
        score += 1 
        fall_speed = min(fall_speed + SPEED_INCREASE, MAX_SPEED)
        update_blocks(blocks, fall_speed)

        if x < PLAYER_RADIUS: x = PLAYER_RADIUS
        if x > SCREEN_WIDTH - PLAYER_RADIUS: x = SCREEN_WIDTH - PLAYER_RADIUS
        if y < PLAYER_RADIUS: y = PLAYER_RADIUS
        if y > SCREEN_HEIGHT - PLAYER_RADIUS: y = SCREEN_HEIGHT - PLAYER_RADIUS

        player_rect = pygame.Rect(x - PLAYER_RADIUS, y - PLAYER_RADIUS, PLAYER_RADIUS * 2, PLAYER_RADIUS * 2)
        
        for block in blocks:
            block_rect = pygame.Rect(block[0], block[1], block[2], block[2])
            
            if player_rect.colliderect(block_rect) and immunity_timer == 0:                
                lives -= 1
                render_frame(screen, blocks, x, y, score, heart_image, lives, 1, background_image, meteor_small, meteor_medium, meteor_large)
                pygame.time.delay(300) 
                immunity_timer = 90
                
                if lives <= 0:
<<<<<<< HEAD
                    LAST_SCORE = score // 10 # Sla score op
                        
                    audio.play_music(audio_path.gameover_music, 0.5, 0) # Speel de korte game over muziek (0 = één keer afspelen)
                    
                    return GameState.GAMEOVER # Ga terug naar main menu flow
=======
                    LAST_SCORE = score // 10 
                    return GameState.GAMEOVER 
>>>>>>> 5cd68de8c5ed7629a8f980f666cb3a4f2765cc6e

        render_frame(screen, blocks, x, y, score, heart_image, lives, immunity_timer, background_image, meteor_small, meteor_medium, meteor_large)

def title_screen(screen):
    start_btn = UIElement(
        center_position=(CENTER_X, 250),
        font_size=50,
        text_rgb=WHITE,
        text="Start Game",
        action=GameState.PLAYING,
    )
    
    options_btn = UIElement(
        center_position=(CENTER_X, 400),
        font_size=50,
        text_rgb=WHITE,
        text="Options",
        action=GameState.OPTIONS,
    )

    quit_btn = UIElement(
        center_position=(CENTER_X, 550),
        font_size=50,
        text_rgb=WHITE,
        text="Afsluiten",
        action=GameState.QUIT,
    )
    return game_loop(screen, RenderUpdates(start_btn, options_btn, quit_btn))

def options_screen(screen):
    TITLE = UIElement(
        center_position=(CENTER_X, 150),
        font_size=70,
        text_rgb=WHITE,
        text="SETTINGS",
        action=None,
    )

    sound_btn = UIElement(
        center_position=(CENTER_X, 300),  
        font_size=40,
        text_rgb=WHITE,
        text="Sound",
        action=GameState.SOUND,
    )

    controls_button = UIElement(
        center_position=(CENTER_X, 450),
        font_size=40,
        text_rgb=WHITE,
        text="CONTROLS",
        action=GameState.CONTROLS,
    )

    back_btn = UIElement(
        center_position=(CENTER_X, 600),
        font_size=40,
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
        text_rgb=WHITE,
        text="CLICK TO CHANGE KEYS",
        action=None,
    )

    btn_left = UIElement(
        center_position=(CENTER_X, 200),
        font_size=25,
        text_rgb=WHITE,
        text=f"move left: {pygame.key.name(KEY_LEFT).upper()}",
        action="CHANGE_LEFT",
    )

    btn_right = UIElement(
        center_position=(CENTER_X, 300),
        font_size=25, 
        text_rgb=WHITE,
        text=f"move right: {pygame.key.name(KEY_RIGHT).upper()}",
        action="CHANGE_RIGHT",
    )

    btn_down = UIElement(
        center_position=(CENTER_X, 400),
        font_size=25,
        text_rgb=WHITE,
        text=f"move down: {pygame.key.name(KEY_DOWN).upper()}",
        action="CHANGE_DOWN",
    )

    btn_up = UIElement(
        center_position=(CENTER_X, 500),
        font_size=25,
        text_rgb=WHITE,
        text=f"move up: {pygame.key.name(KEY_UP).upper()}",
        action="CHANGE_UP",
    )

    back_btn = UIElement(
        center_position=(CENTER_X, 600),
        font_size=30,
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
        
        if MENU_BACKGROUND:
            screen.blit(MENU_BACKGROUND, (0,0))
        else:
            screen.fill(BLUE)

        for button in buttons:
            ui_action = button.update(pygame.mouse.get_pos(), mouse_up)
            
            if ui_action is not None:
                if isinstance(ui_action, GameState):
                    return ui_action
                
                current_key_name = ""
                if ui_action == "CHANGE_LEFT":
                    button.set_text("PRESS KEY...", 25, YELLOW)
                    button.draw(screen); pygame.display.flip()
                    new = wait_for_key()
                    if not key_is_taken(new): KEY_LEFT = new
                    else: show_taken_error(button, screen); KEY_LEFT = KEY_LEFT 
                    button.set_text(f"move left: {pygame.key.name(KEY_LEFT).upper()}", 25, WHITE)

                elif ui_action == "CHANGE_RIGHT":
                    button.set_text("PRESS KEY...", 25, YELLOW)
                    button.draw(screen); pygame.display.flip()
                    new = wait_for_key()
                    if not key_is_taken(new): KEY_RIGHT = new
                    else: show_taken_error(button, screen)
                    button.set_text(f"move right: {pygame.key.name(KEY_RIGHT).upper()}", 25, WHITE)

                elif ui_action == "CHANGE_DOWN":
                    button.set_text("PRESS KEY...", 25, YELLOW)
                    button.draw(screen); pygame.display.flip()
                    new = wait_for_key()
                    if not key_is_taken(new): KEY_DOWN = new
                    else: show_taken_error(button, screen)
                    button.set_text(f"move down: {pygame.key.name(KEY_DOWN).upper()}", 25, WHITE)

                elif ui_action == "CHANGE_UP":
                    button.set_text("PRESS KEY...", 25, YELLOW)
                    button.draw(screen); pygame.display.flip()
                    new = wait_for_key()
                    if not key_is_taken(new): KEY_UP = new
                    else: show_taken_error(button, screen)
                    button.set_text(f"move up: {pygame.key.name(KEY_UP).upper()}", 25, WHITE)

            button.draw(screen)
        pygame.display.flip()

def show_taken_error(button, screen):
    button.set_text("KEY TAKEN!", 25, RED)
    button.draw(screen)
    pygame.display.flip()
    pygame.time.delay(800)

def sound_screen(screen):
    TITLE = UIElement(
        center_position=(CENTER_X, 100),
        font_size=50,
        text_rgb=WHITE,
        text="SOUNDS",
        action=None,
    )
    
    music_btn = UIElement(
        center_position=(CENTER_X, 300),
        font_size=30,
        text_rgb=WHITE,
        text="Muziek: On/Off",
        action=None,
    )

    effects_btn = UIElement(
        center_position=(CENTER_X, 400),
        font_size=30,
        text_rgb=WHITE,
        text="Effects: On/Off",
        action=None,
    )

    back_btn = UIElement(
        center_position=(CENTER_X, 600),
        font_size=30,
        text_rgb=WHITE,
        text="Back to Options",
        action=GameState.OPTIONS,
    )

    return game_loop(screen, RenderUpdates(TITLE, music_btn, effects_btn, back_btn))

def game_over_screen(screen):
    tekst_btn = UIElement(
        center_position=(CENTER_X, 150),
        font_size=60,
        text_rgb=RED,
        text="GAME OVER",
        action=None,
    )
    
    score_display = UIElement(
        center_position=(CENTER_X, 250),
        font_size=40,
        text_rgb=YELLOW,
        text=f"Jouw Score: {LAST_SCORE}",
        action=None,
    )

    restart_btn = UIElement(
        center_position=(CENTER_X, 400),
        font_size=30,
        text_rgb=WHITE,
        text="Opnieuw spelen",
        action=GameState.PLAYING,
    )
    menu_btn = UIElement(
        center_position=(CENTER_X, 500),
        font_size=30,
        text_rgb=WHITE,
        text="Hoofdmenu",
        action=GameState.TITLE,
    )
    return game_loop(screen, RenderUpdates(tekst_btn, score_display, restart_btn, menu_btn))

def main():
    global MENU_BACKGROUND
    screen = pygame.display.set_mode(SCREEN_SIZE)
    pygame.display.set_caption("Dodge Blocks - Full Game")
    
    try:
        MENU_BACKGROUND = pygame.image.load("images/background.png").convert()
        MENU_BACKGROUND = pygame.transform.scale(MENU_BACKGROUND, SCREEN_SIZE)
    except FileNotFoundError:
        try:
            MENU_BACKGROUND = pygame.image.load("background.png").convert()
            MENU_BACKGROUND = pygame.transform.scale(MENU_BACKGROUND, SCREEN_SIZE)
        except:
            print("Geen achtergrond gevonden (background.png). Gebruik blauw scherm.")
            MENU_BACKGROUND = None

    game_state = GameState.TITLE

    while True:
        if game_state == GameState.TITLE:
            audio.play_music(audio_path.menu_music, 0.5, -1)
            game_state = title_screen(screen)

        if game_state == GameState.PLAYING:
            audio.play_music(audio_path.gameplay_music, 0.5, -1)
            game_state = play_level(screen)
        
        if game_state == GameState.GAMEOVER:
            audio.play_music(audio_path.menu_music, 0.5, -1)
            game_state = game_over_screen(screen)
        
        if game_state == GameState.OPTIONS:
            game_state = options_screen(screen)
        
        if game_state == GameState.CONTROLS:
            game_state = control_screen(screen)

        if game_state == GameState.SOUND:
            game_state = sound_screen(screen)
        
        if game_state == GameState.QUIT:
            pygame.quit()
            sys.exit()
            return

if __name__ == "__main__":
    main()