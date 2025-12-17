import pygame
import pygame.freetype
import random
import sys
import audio
import audio_path
from enum import Enum
from pygame.sprite import Sprite, RenderUpdates

# --- INITIALISATIE ---
pygame.init()
pygame.mixer.init()

# --- CONSTANTEN & INSTELLINGEN ---
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

BLOCK_COUNT = 2
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
MENU_BACKGROUND = None 

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

# --- HULPFUNCTIES ---

def create_surface_with_text(text, font_size, text_rgb):
    font = pygame.freetype.SysFont("Courier", font_size, bold=True)
    surface, _ = font.render(text=text, fgcolor=text_rgb, bgcolor=None)
    return surface.convert_alpha()

def key_is_taken(new_key):
    if new_key in [KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN]:
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

def update_blocks(blocks, fall_speed, current_score):
    for block in blocks:
        block[1] += fall_speed
        if fall_speed > 0 and block[1] > SCREEN_HEIGHT:
            block[2] = random.randint(20, 60)
            block[1] = random.randint(-150, 0)
            block[0] = random.randint(0, SCREEN_WIDTH - block[2])
        elif fall_speed < 0 and block[1] < -block[2]:
            block[2] = random.randint(20, 60)
            block[1] = random.randint(SCREEN_HEIGHT, SCREEN_HEIGHT + 150)
            block[0] = random.randint(0, SCREEN_WIDTH - block[2])
    
    zichtbare_score = current_score // 10

    extra_planeten = (zichtbare_score // 100) 
    if len(blocks) < BLOCK_COUNT + extra_planeten:
        size = random.randint(20, 60)
        x = random.randint(0, SCREEN_SIZE[0] - size)
        y = random.randint(-150, 0)
        blocks.append([x, y, size])

# --- UI CLASS ---

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

# --- ALGEMENE FUNCTIES ---

def wait_for_key():
    while True:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                return event.key

def game_loop(screen, buttons):
    while True:
        # Check of muziek is afgelopen (voor overgang Game Over -> Menu)
        if not pygame.mixer.music.get_busy():
            audio.play_music(audio_path.menu_music, 0.5)

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

# --- GAMEPLAY FUNCTIE ---

def render_frame(surface, blocks, player_x, player_y, current_score, heart_img, current_lives, immunity_timer, background_img, img_small, img_medium, img_large, player_image, portal_rect=None, portal_img=None):
    surface.fill(BLACK)
    if background_img:
        surface.blit(background_img, (0,0))

    if portal_rect and portal_img:
        surface.blit(portal_img, (portal_rect.x, portal_rect.y))
    
    for block in blocks:
        x_pos, y_pos, size = block[0], block[1], block[2]
        chosen_img = None
        if img_small and img_medium and img_large:
            if size < 40: chosen_img = img_small
            elif size < 50: chosen_img = img_medium
            else: chosen_img = img_large
            scaled_meteor = pygame.transform.scale(chosen_img, (size, size))
            surface.blit(scaled_meteor, (x_pos, y_pos))
        else:
            pygame.draw.rect(surface, WHITE, (x_pos, y_pos, size, size))

    if immunity_timer == 0 or (immunity_timer // 5) % 2 == 0:
        if player_image:
            img_rect = player_image.get_rect(center=(int(player_x), int(player_y)))
            surface.blit(player_image, img_rect)
        else:
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
    
    # Start gameplay muziek
    audio.play_music(audio_path.gameplay_music, 0.4)

    try:
        player_image = pygame.image.load("images/spaceshipp.png").convert_alpha()
        player_image = pygame.transform.scale(player_image, (PLAYER_RADIUS * 2, PLAYER_RADIUS * 2))
        background_image = pygame.image.load("images/galaxy.png").convert()
        background_image = pygame.transform.scale(background_image, SCREEN_SIZE)
        meteor_small = pygame.image.load("images/neptunus.png").convert_alpha()
        meteor_medium = pygame.image.load("images/mars.png").convert_alpha()
        meteor_large = pygame.image.load("images/jupiter.png").convert_alpha()
        heart_image = pygame.image.load("images/lives.png").convert_alpha()
        heart_image = pygame.transform.scale(heart_image, (30, 30))
        portal_img = pygame.image.load("images/portal.png").convert_alpha()
        portal_img = pygame.transform.scale(portal_img, (200, 40))
    except:
        background_image = meteor_small = meteor_medium = meteor_large = heart_image = player_image = None

    x, y = SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100
    x_velocity = y_velocity = 0
    blocks = create_blocks()
    fall_speed = START_SPEED
    score = 0
    lives = 3
    immunity_timer = 0
    clock = pygame.time.Clock()
    level_flipped = False
    portal_active = False

    while True:
        clock.tick(60)
        is_portal_active = (score // 10 >= 500 and not level_flipped)
        if immunity_timer > 0: immunity_timer -= 1
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return GameState.QUIT
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: return GameState.TITLE 
                if event.key == KEY_RIGHT: x_velocity = MOVEMENT_SPEED
                if event.key == KEY_LEFT: x_velocity = -MOVEMENT_SPEED
                if event.key == KEY_UP: y_velocity = -MOVEMENT_SPEED
                if event.key == KEY_DOWN: y_velocity = MOVEMENT_SPEED
            if event.type == pygame.KEYUP:
                if event.key == KEY_RIGHT and x_velocity > 0: x_velocity = 0
                if event.key == KEY_LEFT and x_velocity < 0: x_velocity = 0
                if event.key == KEY_UP and y_velocity < 0: y_velocity = 0
                if event.key == KEY_DOWN and y_velocity > 0: y_velocity = 0

        if not is_portal_active:
            x += x_velocity
            y += y_velocity
        else:
            x_velocity = y_velocity = 0

        score += 1
        
        if not level_flipped:
            fall_speed = min(fall_speed + SPEED_INCREASE, MAX_SPEED)
        else:
            fall_speed = max(fall_speed - SPEED_INCREASE, -MAX_SPEED)

        update_blocks(blocks, fall_speed, score)

        x = max(PLAYER_RADIUS, min(x, SCREEN_WIDTH - PLAYER_RADIUS))
        y = max(PLAYER_RADIUS, min(y, SCREEN_HEIGHT - PLAYER_RADIUS))

        player_rect = pygame.Rect(x - PLAYER_RADIUS, y - PLAYER_RADIUS, PLAYER_RADIUS * 2, PLAYER_RADIUS * 2)
        
        portal_rect = None
        if is_portal_active:
            portal_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, 20, 200, 40)
            portal_center = (portal_rect.centerx, portal_rect.centery)

            x += (portal_center[0] - x) * 0.05
            y += (portal_center[1] - y) * 0.05

            if player_rect.colliderect(portal_rect):
                for i in range(40):
                    render_frame(screen, blocks, x, y, score, heart_image, lives, 0, background_image, meteor_small, meteor_medium, meteor_large, player_image, portal_rect, portal_img)
                    x += (portal_center[0] - x) * 0.2
                    y += (portal_center[1] - y) * 0.2
                    current_size = int((PLAYER_RADIUS * 2) * (1 - i/40))
                    if current_size > 0 and player_image:
                        scaled_ship = pygame.transform.scale(player_image, (current_size, current_size))
                        screen.blit(scaled_ship, scaled_ship.get_rect(center=(int(x), int(y))))
                    pygame.display.flip()
                    clock.tick(60)

                level_flipped = True
                fall_speed = -fall_speed 
                x, y = SCREEN_WIDTH // 2, 100 
                
                blocks = []
                for _ in range(BLOCK_COUNT):
                    size = random.randint(20, 60)
                    bx = random.randint(0, SCREEN_WIDTH - size)
                    by = random.randint(SCREEN_HEIGHT, SCREEN_HEIGHT + 500)
                    blocks.append([bx, by, size])
                continue
        for block in blocks:
            block_rect = pygame.Rect(block[0], block[1], block[2], block[2])
            if player_rect.colliderect(block_rect) and immunity_timer == 0 and not is_portal_active:                
                lives -= 1
                if lives > 0:
                    audio.play_sfx(audio_path.hit_sound, 0.5)
                    render_frame(screen, blocks, x, y, score, heart_image, lives, 1, background_image, meteor_small, meteor_medium, meteor_large, player_image)
                    pygame.time.delay(300) 
                    immunity_timer = 90
                else:
                    LAST_SCORE = score // 10
                    return GameState.GAMEOVER

        render_frame(screen, blocks, x, y, score, heart_image, lives, immunity_timer, background_image, meteor_small, meteor_medium, meteor_large, player_image, portal_rect, portal_img)

# --- MENU SCHERMEN ---

def title_screen(screen):
    start_btn = UIElement((CENTER_X, 250), "Start Game", 50, WHITE, GameState.PLAYING)
    options_btn = UIElement((CENTER_X, 400), "Options", 50, WHITE, GameState.OPTIONS)
    quit_btn = UIElement((CENTER_X, 550), "Afsluiten", 50, WHITE, GameState.QUIT)
    return game_loop(screen, RenderUpdates(start_btn, options_btn, quit_btn))

def options_screen(screen):
    TITLE = UIElement((CENTER_X, 150), "SETTINGS", 70, WHITE)
    sound_btn = UIElement((CENTER_X, 300), "Sound", 40, WHITE, GameState.SOUND)
    controls_btn = UIElement((CENTER_X, 450), "CONTROLS", 40, WHITE, GameState.CONTROLS)
    back_btn = UIElement((CENTER_X, 600), "Back", 40, WHITE, GameState.TITLE)
    return game_loop(screen, RenderUpdates(TITLE, back_btn, controls_btn, sound_btn))

def control_screen(screen):
    global KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN
    TITLE = UIElement((CENTER_X, 100), "CLICK TO CHANGE KEYS", 50, WHITE)
    btn_left = UIElement((CENTER_X, 200), f"move left: {pygame.key.name(KEY_LEFT).upper()}", 25, WHITE, "CHANGE_LEFT")
    btn_right = UIElement((CENTER_X, 300), f"move right: {pygame.key.name(KEY_RIGHT).upper()}", 25, WHITE, "CHANGE_RIGHT")
    btn_down = UIElement((CENTER_X, 400), f"move down: {pygame.key.name(KEY_DOWN).upper()}", 25, WHITE, "CHANGE_DOWN")
    btn_up = UIElement((CENTER_X, 500), f"move up: {pygame.key.name(KEY_UP).upper()}", 25, WHITE, "CHANGE_UP")
    back_btn = UIElement((CENTER_X, 600), "Back to Options", 30, WHITE, GameState.OPTIONS)

    buttons = RenderUpdates(TITLE, btn_left, btn_right, btn_down, btn_up, back_btn)
    while True:
        mouse_up = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return GameState.QUIT
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1: mouse_up = True
        
        if MENU_BACKGROUND: screen.blit(MENU_BACKGROUND, (0,0))
        else: screen.fill(BLUE)

        for button in buttons:
            ui_action = button.update(pygame.mouse.get_pos(), mouse_up)
            if ui_action is not None:
                if isinstance(ui_action, GameState): return ui_action
                
                button.set_text("PRESS KEY...", 25, YELLOW)
                button.draw(screen); pygame.display.flip()
                new = wait_for_key()
                
                if not key_is_taken(new):
                    if ui_action == "CHANGE_LEFT": KEY_LEFT = new
                    elif ui_action == "CHANGE_RIGHT": KEY_RIGHT = new
                    elif ui_action == "CHANGE_DOWN": KEY_DOWN = new
                    elif ui_action == "CHANGE_UP": KEY_UP = new
                else: show_taken_error(button, screen)
                
                # Update alle teksten
                btn_left.set_text(f"move left: {pygame.key.name(KEY_LEFT).upper()}", 25, WHITE)
                btn_right.set_text(f"move right: {pygame.key.name(KEY_RIGHT).upper()}", 25, WHITE)
                btn_down.set_text(f"move down: {pygame.key.name(KEY_DOWN).upper()}", 25, WHITE)
                btn_up.set_text(f"move up: {pygame.key.name(KEY_UP).upper()}", 25, WHITE)

            button.draw(screen)
        pygame.display.flip()

def show_taken_error(button, screen):
    
    font = pygame.freetype.SysFont("Arial", 25, bold=True)

    text_surf, text_rect = font.render("KEY ALREADY TAKEN!", fgcolor=RED, bgcolor=None)
    
    x = button.rect.right + 20  
    y = button.rect.centery - (text_rect.height / 2) 
    screen.blit(text_surf, (x, y))
    pygame.display.flip()
    pygame.time.delay(1000)

def sound_screen(screen):
    def get_music_text():
        return "Music: ON" if audio.music_enabled else "Music: OFF"
    def get_sfx_text():
        return "Effects: ON" if audio.sfx_enabled else "Effects: OFF"
    
    TITLE = UIElement((CENTER_X, 100), "SOUNDS", 50, WHITE)
    music_btn = UIElement((CENTER_X, 300), get_music_text(), 30, WHITE, "TOGGLE_MUSIC")
    effects_btn = UIElement((CENTER_X, 400), get_sfx_text(), 30, WHITE, "TOGGLE_SFX")
    back_btn = UIElement((CENTER_X, 600), "Back to Options", 30, WHITE, GameState.OPTIONS)
    
    buttons = RenderUpdates(TITLE, music_btn, effects_btn, back_btn)

    while True:
        mouse_up = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return GameState.QUIT
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1: mouse_up = True
        
        if MENU_BACKGROUND: screen.blit(MENU_BACKGROUND, (0,0))
        else: screen.fill(BLUE)

        for button in buttons:
            ui_action = button.update(pygame.mouse.get_pos(), mouse_up)

            if ui_action == "TOGGLE_MUSIC":
                audio.toggle_music()
                button.set_text(get_music_text(), 30, WHITE)

                if audio.music_enabled:
                    audio.play_music(audio_path.menu_music, 0.5)

            elif ui_action == "TOGGLE_SFX":
                audio.toggle_sfx()
                button.set_text(get_sfx_text(), 30, WHITE)
                if audio.sfx_enabled:
                    audio.play_sfx(audio_path.hit_sound, 0.5)

            elif isinstance(ui_action, GameState):
                return ui_action
            
            button.draw(screen)

        pygame.display.flip()

def game_over_screen(screen):
    tekst_btn = UIElement((CENTER_X, 150), "GAME OVER", 60, RED)
    score_display = UIElement((CENTER_X, 250), f"Jouw Score: {LAST_SCORE}", 40, YELLOW)
    restart_btn = UIElement((CENTER_X, 400), "Opnieuw spelen", 30, WHITE, GameState.PLAYING)
    menu_btn = UIElement((CENTER_X, 500), "Hoofdmenu", 30, WHITE, GameState.TITLE)
    return game_loop(screen, RenderUpdates(tekst_btn, score_display, restart_btn, menu_btn))

def main():
    global MENU_BACKGROUND
    screen = pygame.display.set_mode(SCREEN_SIZE)
    pygame.display.set_caption("Dodge Blocks - Full Game")
    
    try:
        MENU_BACKGROUND = pygame.image.load("images/background.png").convert()
        MENU_BACKGROUND = pygame.transform.scale(MENU_BACKGROUND, SCREEN_SIZE)
    except:
        MENU_BACKGROUND = None

    game_state = GameState.TITLE

    while True:
        if game_state == GameState.TITLE:
            audio.play_music(audio_path.menu_music, 0.5)
            game_state = title_screen(screen)

        elif game_state == GameState.PLAYING:
            game_state = play_level(screen)
        
        elif game_state == GameState.GAMEOVER:
            # Speel de clip 1 keer af
            audio.play_music(audio_path.gameover_music, 0.5, loop=0)
            game_state = game_over_screen(screen)
        
        elif game_state == GameState.OPTIONS:
            game_state = options_screen(screen)
        
        elif game_state == GameState.CONTROLS:
            game_state = control_screen(screen)

        elif game_state == GameState.SOUND:
            game_state = sound_screen(screen)
        
        elif game_state == GameState.QUIT:
            pygame.quit()
            sys.exit()

if __name__ == "__main__":
    main()
    