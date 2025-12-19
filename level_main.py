import pygame
import pygame.freetype
import random
import sys
import audio
import audio_path
import json
import os
from enum import Enum
from pygame.sprite import Sprite, RenderUpdates


SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
SCREEN_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)
CENTER_X = SCREEN_WIDTH / 2

BLUE = (106, 159, 181)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
GAME_BLUE = (0, 100, 255)
GRAY = (70, 70, 70)
DARK_GRAY = (40, 40, 40)

BLOCK_COUNT = 10
PLAYER_RADIUS = 20
MOVEMENT_SPEED = 8
MAX_BLOCKS = 15
START_SPEED = 3
SPEED_INCREASE = 0.0005
MAX_SPEED = 12

FONT_SCORE = None 

def load_highscore():
    if not os.path.exists("highscores.json"):
        return {
            "level1": {"EASY" : 0, "MEDIUM" : 0, "HARD" : 0},
            "level2": {"EASY" : 0, "MEDIUM" : 0, "HARD" : 0},
            "level3": {"EASY" : 0, "MEDIUM" : 0, "HARD" : 0},
            "level4": {"EASY": 0, "MEDIUM": 0, "HARD": 0}  
            }
    with open("highscores.json", "r") as f:
        return json.load(f)
    
def save_highscore(level, difficulty, score):
    scores = load_highscore()
    if score > scores[level][difficulty]:
        scores[level][difficulty] = score
        with open("highscores.json", "w") as f:
            json.dump(scores, f)

class GameState(Enum):
    QUIT = -1
    TITLE = 0
    PLAYING_LVL1 = 1
    PLAYING_LVL2 = 2
    PLAYING_LVL3 = 3
    PLAYING_LVL4 = 4
    SOUND = 5
    CONTROLS = 6
    LEVEL_SELECT = 7
    GAMEOVER = 8
    OPTIONS = 9
    VIDEO_SETTINGS = 10

class Controls:
    def __init__(self):
        self.left = pygame.K_LEFT
        self.right = pygame.K_RIGHT
        self.up = pygame.K_UP
        self.down = pygame.K_DOWN

    def key_is_taken(self, new_key: int) -> bool:
        return new_key in [self.left, self.right, self.up, self.down]

class TextFactory:
    @staticmethod
    def create_surface_with_text(text: str, font_size: int, text_rgb):
        font = pygame.freetype.SysFont("Courier", font_size, bold=True)
        surface, _ = font.render(text=text, fgcolor=text_rgb, bgcolor=None)
        return surface.convert_alpha()

class UIElement(Sprite):
    def __init__(self, center_position, text, font_size, text_rgb, action=None, box_color=None, box_size=(110, 110)):
        super().__init__()
        self._mouse_over = False
        self._action = action
        self._font_size = font_size
        self._text_rgb = text_rgb
        self._box_color = box_color
        self._box_size = box_size
        self._image_normal = self.create_button_surface(text, font_size, text_rgb, box_color, box_size)
        hover_bg = DARK_GRAY if box_color else None
        self._image_hover = self.create_button_surface(text, int(font_size * 1.1), text_rgb, hover_bg, box_size)
        self.image = self._image_normal
        self.rect = self.image.get_rect(center=center_position)

    def create_button_surface(self, text, font_size, text_rgb, bg_color, size):
        font = pygame.freetype.SysFont("Courier", font_size, bold=True)
        if bg_color:
            surface = pygame.Surface(size).convert_alpha()
            surface.fill(bg_color)
            text_surf, text_rect = font.render(text, fgcolor=text_rgb)
            text_rect.center = (size[0] // 2, size[1] // 2)
            surface.blit(text_surf, text_rect)
            pygame.draw.rect(surface, WHITE, surface.get_rect(), 2)
            return surface
        else: 
            surface, _ = font.render(text, fgcolor=text_rgb)
            return surface

    def get_action(self):
        return self._action

    def set_text(self, text, font_size=None, text_rgb=None):
        if font_size: self._font_size = font_size
        if text_rgb: self._text_rgb = text_rgb
        self._image_normal = self.create_button_surface(text, self._font_size, self._text_rgb, self._box_color, self._box_size)
        hover_bg = DARK_GRAY if self._box_color else None
        self._image_hover = self.create_button_surface(text, int(self._font_size * 1.1), self._text_rgb, hover_bg, self._box_size)
        current_center = self.rect.center
        self.image = self._image_normal
        self.rect = self.image.get_rect(center=current_center)

    def update(self, mouse_pos, mouse_up):
        if self.rect.collidepoint(mouse_pos):
            self._mouse_over = True
            self.image = self._image_hover
            if mouse_up:
                return self.get_action()
        else:
            self._mouse_over = False
            self.image = self._image_normal
        return None

    def draw(self, surface):
        surface.blit(self.image, self.rect)

class MenuScreenBase:
    def __init__(self, game):
        self.game = game

    def build_buttons(self) -> RenderUpdates:
        raise NotImplementedError

    def run(self, screen) -> GameState:
        return self.game.game_loop(screen, self.build_buttons())

class LevelSelectScreen:
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.SysFont("Arial", 40, bold=True)
        self.selected_level = None 
        self.current_difficulty = None
        self.show_highscore_step = False
        try:
            self.bg = pygame.image.load("images/galaxy.png").convert()
            self.bg = pygame.transform.scale(self.bg, SCREEN_SIZE)
        except:
            self.bg = None

    def set_difficulty(self, diff):
        if diff == "EASY":
            self.game.active_block_count = 5
            self.game.active_start_speed = 3
        elif diff == "MEDIUM":
            self.game.active_block_count = 10
            self.game.active_start_speed = 5
        elif diff == "HARD":
            self.game.active_block_count = 15
            self.game.active_start_speed = 7

    def run(self, screen):
        self.selected_level = None 
        self.show_highscore_step = False
        self.current_difficulty = None

        while True:
            if self.bg: screen.blit(self.bg, (0, 0))
            else: screen.fill(BLACK)
            
            mouse_pos = pygame.mouse.get_pos()
            
            btn_lvl1 = pygame.Rect(SCREEN_WIDTH//2 - 200, 200, 400, 70)
            btn_lvl2 = pygame.Rect(SCREEN_WIDTH//2 - 200, 300, 400, 70)
            btn_lvl3 = pygame.Rect(SCREEN_WIDTH//2 - 200, 400, 400, 70)
            btn_lvl4 = pygame.Rect(CENTER_X - 200, 500, 400, 70)
            
            btn_easy = pygame.Rect(SCREEN_WIDTH//2 - 150, 250, 300, 60)
            btn_med = pygame.Rect(SCREEN_WIDTH//2 - 150, 350, 300, 60)
            btn_hard = pygame.Rect(SCREEN_WIDTH//2 - 150, 450, 300, 60)

            if self.selected_level is None:
                title = self.font.render("KIES EEN LEVEL", True, WHITE)
                screen.blit(title, (CENTER_X - title.get_width()//2, 100))
                for btn, txt in [(btn_lvl1, "Level1"), (btn_lvl2, "Level2"), (btn_lvl3, "Level3"), (btn_lvl4, "Level4")]:
                    color = BLUE if btn.collidepoint(mouse_pos) else DARK_GRAY
                    pygame.draw.rect(screen, color, btn, border_radius=15)
                    t = self.font.render(txt, True, WHITE)
                    screen.blit(t, (btn.centerx - t.get_width()//2, btn.centery - t.get_height()//2))

            elif not self.show_highscore_step:
                title = self.font.render("KIES MOEILIJKHEID", True, WHITE)
                screen.blit(title, (CENTER_X - title.get_width()//2, 100))
                for btn, txt, color in [(btn_easy, "EASY", GREEN), (btn_med, "MEDIUM", YELLOW), (btn_hard, "HARD", RED)]:
                    bg_color = color if btn.collidepoint(mouse_pos) else GRAY
                    pygame.draw.rect(screen, bg_color, btn, border_radius=10)
                    t = self.font.render(txt, True, BLACK)
                    screen.blit(t, (btn.centerx - t.get_width()//2, btn.centery - t.get_height()//2))

            else:
                current_scores = load_highscore()
                if self.selected_level == GameState.PLAYING_LVL1: lvl_str = "level 1"
                elif self.selected_level == GameState.PLAYING_LVL2: lvl_str = "level 2"
                elif self.selected_level == GameState.PLAYING_LVL3: lvl_str = "level 3"
                elif self.selected_level == GameState.PLAYING_LVL4: lvl_str = "level 4"
                
                score = current_scores[lvl_str][self.current_difficulty]

                txt_hs = self.font.render(f"HIGHSCORE: {score}", True, YELLOW)
                txt_info = self.font.render(f"{lvl_str.upper()} - {self.current_difficulty}", True, WHITE)
                txt_start = self.font.render("Klik om te starten!", True, GREEN)
                
                screen.blit(self.font.render(f"HIGHSCORE: {score}", True, YELLOW), (CENTER_X - 150, 250))
                screen.blit(self.font.render(f"{lvl_str.upper()} - {self.current_difficulty}", True, WHITE), (CENTER_X - 150, 320))
                screen.blit(self.font.render("Klik om te starten!", True, GREEN), (CENTER_X - 150, 450))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT: return GameState.QUIT
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.selected_level is None:
                        if btn_lvl1.collidepoint(event.pos): self.selected_level = GameState.PLAYING_LVL1
                        elif btn_lvl2.collidepoint(event.pos): self.selected_level = GameState.PLAYING_LVL2
                        elif btn_lvl3.collidepoint(event.pos): self.selected_level = GameState.PLAYING_LVL3
                        elif btn_lvl4.collidepoint(event.pos): self.selected_level = GameState.PLAYING_LVL4
                    
                    elif not self.show_highscore_step:
                        if btn_easy.collidepoint(event.pos): 
                            self.set_difficulty("EASY"); self.current_difficulty = "EASY"; self.show_highscore_step = True
                        elif btn_med.collidepoint(event.pos): 
                            self.set_difficulty("MEDIUM"); self.current_difficulty = "MEDIUM"; self.show_highscore_step = True
                        elif btn_hard.collidepoint(event.pos): 
                            self.set_difficulty("HARD"); self.current_difficulty = "HARD"; self.show_highscore_step = True
                    
                    elif self.show_highscore_step:
                        return self.selected_level

class TitleScreen(MenuScreenBase):
    def build_buttons(self):
        start_btn = UIElement((CENTER_X, 250), "Start Game", 50, WHITE, GameState.LEVEL_SELECT)
        options_btn = UIElement((CENTER_X, 400), "Options", 50, WHITE, GameState.OPTIONS)    
        quit_btn = UIElement((CENTER_X, 550), "Afsluiten", 50, WHITE, GameState.QUIT)
        return RenderUpdates(start_btn, options_btn, quit_btn)

class OptionsScreen(MenuScreenBase):
    def build_buttons(self):
        title = UIElement((CENTER_X, 150), "SETTINGS", 70, WHITE)
        sound_btn = UIElement((CENTER_X, 300), "Sound", 40, WHITE, GameState.SOUND)
        controls_btn = UIElement((CENTER_X, 450), "CONTROLS", 40, WHITE, GameState.CONTROLS)
        back_btn = UIElement((CENTER_X, 600), "Back", 40, WHITE, GameState.TITLE)
        return RenderUpdates(title, back_btn, controls_btn, sound_btn)

class GameOverScreen(MenuScreenBase):
    def build_buttons(self):
        tekst_btn = UIElement((CENTER_X, 150), "GAME OVER", 60, RED)
        score_display = UIElement((CENTER_X, 250), f"Jouw Score: {self.game.last_score}", 40, YELLOW)
        restart_btn = UIElement((CENTER_X, 400), "Opnieuw spelen", 30, WHITE, self.game.current_playing_level)
        menu_btn = UIElement((CENTER_X, 500), "Hoofdmenu", 30, WHITE, GameState.TITLE)
        return RenderUpdates(tekst_btn, score_display, restart_btn, menu_btn)

class ControlsScreen:
    def __init__(self, game):
        self.game = game

    @staticmethod
    def wait_for_key():
        while True:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    return event.key

    @staticmethod
    def show_taken_error(button: UIElement, screen):
        font = pygame.freetype.SysFont("Arial", 25, bold=True)
        text_surf, text_rect = font.render("KEY ALREADY TAKEN!", fgcolor=RED, bgcolor=None)
        x = button.rect.right + 20
        y = button.rect.centery - (text_rect.height / 2)
        screen.blit(text_surf, (x, y))
        pygame.display.flip()
        pygame.time.delay(1000)

    def run(self, screen) -> GameState:
        c = self.game.controls
        title = UIElement((CENTER_X, 100), "CLICK TO CHANGE KEYS", 50, WHITE)
        btn_left = UIElement((CENTER_X, 200), f"move left: {pygame.key.name(c.left).upper()}", 25, WHITE, "CHANGE_LEFT")
        btn_right = UIElement((CENTER_X, 300), f"move right: {pygame.key.name(c.right).upper()}", 25, WHITE, "CHANGE_RIGHT")
        btn_down = UIElement((CENTER_X, 400), f"move down: {pygame.key.name(c.down).upper()}", 25, WHITE, "CHANGE_DOWN")
        btn_up = UIElement((CENTER_X, 500), f"move up: {pygame.key.name(c.up).upper()}", 25, WHITE, "CHANGE_UP")
        back_btn = UIElement((CENTER_X, 600), "Back to Options", 30, WHITE, GameState.OPTIONS)
        buttons = RenderUpdates(title, btn_left, btn_right, btn_down, btn_up, back_btn)

        while True:
            mouse_up = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return GameState.QUIT
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    mouse_up = True

            self.game.draw_menu_background(screen)
            for button in buttons:
                ui_action = button.update(pygame.mouse.get_pos(), mouse_up)
                if ui_action is not None:
                    if isinstance(ui_action, GameState):
                        return ui_action
                    button.set_text("PRESS KEY...", 25, YELLOW)
                    button.draw(screen)
                    pygame.display.flip()
                    new = self.wait_for_key()
                    if not c.key_is_taken(new):
                        if ui_action == "CHANGE_LEFT": c.left = new
                        elif ui_action == "CHANGE_RIGHT": c.right = new
                        elif ui_action == "CHANGE_DOWN": c.down = new
                        elif ui_action == "CHANGE_UP": c.up = new
                    else:
                        self.show_taken_error(button, screen)
                    btn_left.set_text(f"move left: {pygame.key.name(c.left).upper()}", 25, WHITE)
                    btn_right.set_text(f"move right: {pygame.key.name(c.right).upper()}", 25, WHITE)
                    btn_down.set_text(f"move down: {pygame.key.name(c.down).upper()}", 25, WHITE)
                    btn_up.set_text(f"move up: {pygame.key.name(c.up).upper()}", 25, WHITE)
                button.draw(screen)
            pygame.display.flip()

class SoundScreen:
    def __init__(self, game):
        self.game = game

    @staticmethod
    def get_music_text():
        return "Music: ON" if audio.music_enabled else "Music: OFF"

    @staticmethod
    def get_sfx_text():
        return "Effects: ON" if audio.sfx_enabled else "Effects: OFF"

    def run(self, screen) -> GameState:
        title = UIElement((CENTER_X, 100), "SOUNDS", 50, WHITE)
        music_btn = UIElement((CENTER_X, 300), self.get_music_text(), 30, WHITE, "TOGGLE_MUSIC")
        effects_btn = UIElement((CENTER_X, 400), self.get_sfx_text(), 30, WHITE, "TOGGLE_SFX")
        back_btn = UIElement((CENTER_X, 600), "Back to Options", 30, WHITE, GameState.OPTIONS)
        buttons = RenderUpdates(title, music_btn, effects_btn, back_btn)

        while True:
            mouse_up = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return GameState.QUIT
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    mouse_up = True

            self.game.draw_menu_background(screen)
            for button in buttons:
                ui_action = button.update(pygame.mouse.get_pos(), mouse_up)
                if ui_action == "TOGGLE_MUSIC":
                    audio.toggle_music()
                    button.set_text(self.get_music_text(), 30, WHITE)
                    if audio.music_enabled: audio.play_music(audio_path.menu_music, 0.5)
                elif ui_action == "TOGGLE_SFX":
                    audio.toggle_sfx()
                    button.set_text(self.get_sfx_text(), 30, WHITE)
                    if audio.sfx_enabled: audio.play_sfx(audio_path.hit_sound, 0.5)
                elif isinstance(ui_action, GameState):
                    return ui_action
                button.draw(screen)
            pygame.display.flip()

class LevelSession:
    def __init__(self, game):
        self.game = game
        self.load_assets()
        self.bg_scroll = 0
        self.bg_speed = 1
        self.current_bg_index = 0

    def load_assets(self):
        try:
            self.player_img = pygame.image.load("images/spaceshipp.png").convert_alpha()
            self.player_img = pygame.transform.scale(self.player_img, (PLAYER_RADIUS * 2, PLAYER_RADIUS * 2))
            self.background_image = pygame.image.load("images/galaxy.png").convert()
            self.background_image = pygame.transform.scale(self.background_image, SCREEN_SIZE)
            self.meteor_small = pygame.image.load("images/neptunus.png").convert_alpha()
            self.meteor_medium = pygame.image.load("images/mars.png").convert_alpha()
            self.meteor_large = pygame.image.load("images/jupiter.png").convert_alpha()
            self.heart_image = pygame.image.load("images/lives.png").convert_alpha()
            self.heart_image = pygame.transform.scale(self.heart_image, (30, 30))
        except Exception as e:
            print(f"Error assets L1: {e}")

        self.bg_images = []
        for i in range(1, 5):
            try:
                img = pygame.image.load(f"images/bgob{i}.png").convert()
                img = pygame.transform.scale(img, SCREEN_SIZE)
                self.bg_images.append(img)
            except:
                print(f"Kon afbeelding images/bgob{i}.png niet laden")

    def create_blocks(self):
        blocks = []
        for _ in range(self.game.active_block_count):
            size = random.randint(20, 60)
            bx = random.randint(0, SCREEN_WIDTH - size)
            by = random.randint(-500, 0)
            blocks.append([bx, by, size])
        return blocks

    def update_blocks(self, blocks, fall_speed, current_score):
        for block in blocks:
            block[1] += fall_speed
            if block[1] > SCREEN_HEIGHT: 
                block[2] = random.randint(20, 60)
                block[1] = random.randint(-150, 0)
                block[0] = random.randint(0, SCREEN_WIDTH - block[2])
        zichtbare_score = current_score // 10
        max_b = min(self.game.active_block_count + (zichtbare_score // 50), self.game.active_max_blocks)
        if len(blocks) < max_b:
            size = random.randint(20, 60)
            blocks.append([random.randint(0, SCREEN_WIDTH - size), random.randint(-150, 0), size])

    def render_frame(self, surface, blocks, player_x, player_y, current_score, current_lives, immunity_timer):
        surface.blit(self.background_image, (0, 0))
        if self.bg_images:
            self.bg_scroll += self.bg_speed
        if self.bg_scroll >= SCREEN_HEIGHT:
            self.bg_scroll = 0
            self.current_bg_index = (self.current_bg_index + 1) % len(self.bg_images)
        next_bg_index = (self.current_bg_index + 1) % len(self.bg_images)
        surface.blit(self.bg_images[self.current_bg_index], (0, self.bg_scroll))
        surface.blit(self.bg_images[next_bg_index], (0, self.bg_scroll - SCREEN_HEIGHT))

        for block in blocks:
            x_pos, y_pos, size = block[0], block[1], block[2]
            img = self.meteor_small if size < 40 else (self.meteor_medium if size < 50 else self.meteor_large)
            scaled = pygame.transform.scale(img, (size, size))
            surface.blit(scaled, (x_pos, y_pos))
        if immunity_timer == 0 or (immunity_timer // 5) % 2 == 0:
            img_rect = self.player_img.get_rect(center=(int(player_x), int(player_y)))
            surface.blit(self.player_img, img_rect)    
        score_surface = FONT_SCORE.render("Score: " + str(current_score // 10), True, WHITE)
        surface.blit(score_surface, (SCREEN_WIDTH - 180, 20))
        for i in range(current_lives):
            surface.blit(self.heart_image, (20 + (i * 35), 20))
        pygame.display.flip()

    def run(self, screen) -> GameState:
        audio.play_music(audio_path.gameplay_music, 0.4)
        c = self.game.controls
        x, y = SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100
        x_velocity, y_velocity = 0, 0
        blocks = self.create_blocks()
        score, lives, immunity_timer = 0, 3, 0
        clock = pygame.time.Clock()
        while True:
            clock.tick(60)
            if immunity_timer > 0: immunity_timer -= 1
            for event in pygame.event.get():
                if event.type == pygame.QUIT: return GameState.QUIT
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE: return GameState.TITLE
                    if event.key == c.right: x_velocity = MOVEMENT_SPEED
                    if event.key == c.left: x_velocity = -MOVEMENT_SPEED
                    if event.key == c.up: y_velocity = -MOVEMENT_SPEED
                    if event.key == c.down: y_velocity = MOVEMENT_SPEED
                if event.type == pygame.KEYUP:
                    if event.key in [c.right, c.left]: x_velocity = 0
                    if event.key in [c.up, c.down]: y_velocity = 0
            x += x_velocity
            y += y_velocity
            score += 1
            fall_speed = min(self.game.active_start_speed + (score * self.game.active_speed_increase), MAX_SPEED)
            self.update_blocks(blocks, fall_speed, score)
            x = max(PLAYER_RADIUS, min(SCREEN_WIDTH - PLAYER_RADIUS, x))
            y = max(PLAYER_RADIUS, min(SCREEN_HEIGHT - PLAYER_RADIUS, y))
            player_rect = pygame.Rect(x - PLAYER_RADIUS, y - PLAYER_RADIUS, PLAYER_RADIUS * 2, PLAYER_RADIUS * 2)
            for block in blocks:
                block_rect = pygame.Rect(block[0], block[1], block[2], block[2])
                if player_rect.colliderect(block_rect) and immunity_timer == 0:                
                    lives -= 1
                    audio.play_sfx(audio_path.hit_sound, 0.5)
                    if lives <= 0:
                        self.game.last_score = score // 10
                        return GameState.GAMEOVER
                    immunity_timer = 90
                    break 
            self.render_frame(screen, blocks, x, y, score, lives, immunity_timer)

class LevelSession2:
    def __init__(self, game):
        self.game = game
        self.load_assets()
        self.level_flipped = False
        self.level_side = False
        self.bg_scroll = 0
        self.bg_speed = 1
        self.current_bg_index = 0

    def load_assets(self):
        self.player_img = pygame.image.load("images/spaceshipp.png").convert_alpha()
        self.player_img = pygame.transform.scale(self.player_img, (PLAYER_RADIUS * 2, PLAYER_RADIUS * 2))
        self.background_image = pygame.image.load("images/galaxy.png").convert()
        self.background_image = pygame.transform.scale(self.background_image, SCREEN_SIZE)
        self.meteor_small = pygame.image.load("images/neptunus.png").convert_alpha()
        self.meteor_medium = pygame.image.load("images/mars.png").convert_alpha()
        self.meteor_large = pygame.image.load("images/jupiter.png").convert_alpha()
        self.heart_image = pygame.image.load("images/lives.png").convert_alpha()
        self.heart_image = pygame.transform.scale(self.heart_image, (30, 30))
        self.portal_img = pygame.image.load("images/portal.png").convert_alpha()
        self.portal_img = pygame.transform.scale(self.portal_img, (200, 40))
        self.bg_images = []
        for i in range(1, 5):
            try:
                img = pygame.image.load(f"images/bgob{i}.png").convert()
                img = pygame.transform.scale(img, SCREEN_SIZE)
                self.bg_images.append(img)
            except:
                print(f"Kon afbeelding images/bgob{i}.png niet laden")

    def create_blocks(self, level_mode="down"):
        blocks = []
        for _ in range(self.game.active_block_count):
            size = random.randint(20, 60)
            if level_mode == "side":
                bx = random.randint(SCREEN_WIDTH, SCREEN_WIDTH + 500)
                by = random.randint(0, SCREEN_HEIGHT - size)
            elif level_mode == "up":
                bx = random.randint(0, SCREEN_WIDTH - size)
                by = random.randint(SCREEN_HEIGHT, SCREEN_HEIGHT + 500)
            else:
                bx = random.randint(0, SCREEN_WIDTH - size)
                by = random.randint(-500, -60)
            blocks.append([bx, by, size])
        return blocks

    def update_blocks(self, blocks, fall_speed, current_score, level_mode):
        current_speed = abs(fall_speed)
        for block in blocks:
            if level_mode == "side":
                block[0] -= current_speed 
                if block[0] < -block[2]:
                    block[2] = random.randint(20, 60)
                    block[0] = random.randint(SCREEN_WIDTH, SCREEN_WIDTH + 200)
                    block[1] = random.randint(0, SCREEN_HEIGHT - block[2])
            elif level_mode == "up":
                block[1] += fall_speed 
                if block[1] < -block[2]:
                    block[2] = random.randint(20, 60)
                    block[1] = random.randint(SCREEN_HEIGHT, SCREEN_HEIGHT + 200)
                    block[0] = random.randint(0, SCREEN_WIDTH - block[2])
            else: 
                block[1] += fall_speed 
                if block[1] > SCREEN_HEIGHT:
                    block[2] = random.randint(20, 60)
                    block[1] = random.randint(-200, -60)
                    block[0] = random.randint(0, SCREEN_WIDTH - block[2])
        zichtbare_score = current_score // 10
        max_b = min(self.game.active_block_count + (zichtbare_score // 100), self.game.active_max_blocks)
        if len(blocks) < max_b:
            size = random.randint(20, 60)
            if level_mode == "side": blocks.append([random.randint(SCREEN_WIDTH, SCREEN_WIDTH + 200), random.randint(0, SCREEN_HEIGHT - size), size])
            elif level_mode == "up": blocks.append([random.randint(0, SCREEN_WIDTH - size), random.randint(SCREEN_HEIGHT, SCREEN_HEIGHT + 200), size])
            else: blocks.append([random.randint(0, SCREEN_WIDTH - size), random.randint(-200, -60), size])

    def render_frame(self, surface, blocks, player_x, player_y, current_score, current_lives, immunity_timer, portal_rect=None):
        surface.blit(self.background_image, (0, 0))
        if self.bg_images:
            self.bg_scroll += self.bg_speed
        if self.bg_scroll >= SCREEN_HEIGHT:
            self.bg_scroll = 0
            self.current_bg_index = (self.current_bg_index + 1) % len(self.bg_images)
        next_bg_index = (self.current_bg_index + 1) % len(self.bg_images)
        surface.blit(self.bg_images[self.current_bg_index], (0, self.bg_scroll))
        surface.blit(self.bg_images[next_bg_index], (0, self.bg_scroll - SCREEN_HEIGHT))
        if portal_rect: surface.blit(self.portal_img, (portal_rect.x, portal_rect.y))
        for block in blocks:
            x_pos, y_pos, size = block[0], block[1], block[2]
            img = self.meteor_small if size < 40 else (self.meteor_medium if size < 50 else self.meteor_large)
            scaled = pygame.transform.scale(img, (size, size))
            surface.blit(scaled, (x_pos, y_pos))
        if immunity_timer == 0 or (immunity_timer // 5) % 2 == 0:
            rect = self.player_img.get_rect(center=(int(player_x), int(player_y)))
            surface.blit(self.player_img, rect)
        score_surf = FONT_SCORE.render(f"Score: {current_score // 10}", True, WHITE)
        surface.blit(score_surf, (SCREEN_WIDTH - 180, 20))
        for i in range(current_lives): surface.blit(self.heart_image, (20 + (i * 35), 20))
        pygame.display.flip()

    def run(self, screen):
        c = self.game.controls
        x, y = SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100
        x_vel, y_vel = 0, 0
        
        blocks = self.create_blocks("down") 
        
        score, lives, immunity = 0, 3, 0
        clock = pygame.time.Clock()
        
        while True:
            clock.tick(60)
            zichtbare_score = score // 10
            portal1_active = (zichtbare_score >= 500 and not self.level_flipped)
            portal2_active = (zichtbare_score >= 1000 and self.level_flipped and not self.level_side)
            is_portal = portal1_active or portal2_active
            
            if immunity > 0: immunity -= 1
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: return GameState.QUIT
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE: return GameState.TITLE
                    if event.key == c.right: x_vel = MOVEMENT_SPEED
                    if event.key == c.left: x_vel = -MOVEMENT_SPEED
                    if event.key == c.up: y_vel = -MOVEMENT_SPEED
                    if event.key == c.down: y_vel = MOVEMENT_SPEED
                if event.type == pygame.KEYUP:
                    if event.key in [c.right, c.left]: x_vel = 0
                    if event.key in [c.up, c.down]: y_vel = 0

            current_portal_rect = None
            if is_portal:
                p_y = 20 if portal1_active else SCREEN_HEIGHT - 40
                current_portal_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, p_y, 200, 40)
                x += (current_portal_rect.centerx - x) * 0.05
                y += (current_portal_rect.centery - y) * 0.05
                p_rect_player = pygame.Rect(x-PLAYER_RADIUS, y-PLAYER_RADIUS, PLAYER_RADIUS*2, PLAYER_RADIUS*2)
                if p_rect_player.colliderect(current_portal_rect):
                    if not self.level_flipped:
                        self.level_flipped = True
                        x, y = SCREEN_WIDTH//2, 120
                        blocks = self.create_blocks("up")
                    else:
                        self.level_side = True
                        x, y = 120, SCREEN_HEIGHT//2
                        blocks = self.create_blocks("side")
                    continue 
            else:
                x += x_vel
                y += y_vel

            score += 1

            base_speed = self.game.active_start_speed + (score * self.game.active_speed_increase)
            
            if not self.level_flipped: 
                speed, mode = min(base_speed, MAX_SPEED), "down"
            elif not self.level_side: 
                speed, mode = max(-base_speed, -MAX_SPEED), "up"
            else: 
                speed, mode = max(-base_speed, -MAX_SPEED), "side"

            self.update_blocks(blocks, speed, score, mode)
            
            x = max(PLAYER_RADIUS, min(SCREEN_WIDTH - PLAYER_RADIUS, x))
            y = max(PLAYER_RADIUS, min(SCREEN_HEIGHT - PLAYER_RADIUS, y))
            
            if not is_portal:
                p_rect = pygame.Rect(x-PLAYER_RADIUS, y-PLAYER_RADIUS, PLAYER_RADIUS*2, PLAYER_RADIUS*2)
                for b in blocks:
                    if p_rect.colliderect(pygame.Rect(b[0], b[1], b[2], b[2])) and immunity == 0:
                        lives -= 1
                        audio.play_sfx(audio_path.hit_sound, 0.5)
                        if lives <= 0:
                            self.game.last_score = score // 10
                            return GameState.GAMEOVER
                        immunity = 90
                        break
            self.render_frame(screen, blocks, x, y, score, lives, immunity, current_portal_rect)

class LevelSession3:
    def __init__(self, game):
        self.game = game
        self.load_assets()
        self.bg_scroll = 0
        self.bg_speed = 1
        self.current_bg_index = 0

    def load_assets(self):
        try:
            self.player_img = pygame.image.load("images/spaceshipp.png").convert_alpha()
            self.player_img = pygame.transform.scale(self.player_img, (PLAYER_RADIUS * 2, PLAYER_RADIUS * 2))
            self.background_image = pygame.image.load("images/galaxy.png").convert()
            self.background_image = pygame.transform.scale(self.background_image, SCREEN_SIZE)
            self.meteor_small = pygame.image.load("images/neptunus.png").convert_alpha()
            self.meteor_medium = pygame.image.load("images/mars.png").convert_alpha()
            self.meteor_large = pygame.image.load("images/jupiter.png").convert_alpha()
            self.heart_image = pygame.image.load("images/lives.png").convert_alpha()
            self.heart_image = pygame.transform.scale(self.heart_image, (30, 30))
        except Exception as e:
            print(f"Error assets L1: {e}")

        self.bg_images = []
        for i in range(1, 5):
            try:
                img = pygame.image.load(f"images/bgob{i}.png").convert()
                img = pygame.transform.scale(img, SCREEN_SIZE)
                self.bg_images.append(img)
            except:
                print(f"Kon afbeelding images/bgob{i}.png niet laden")

    def create_blocks(self):
        blocks = []
        for _ in range(self.game.active_block_count):
            size = random.randint(20, 60)
            richting = random.choice([0, 1])
            
            if richting == 0:
                bx = random.randint(SCREEN_WIDTH, SCREEN_WIDTH + 500)
            else:
                bx = random.randint(-500, -size)
                
            by = random.randint(0, SCREEN_HEIGHT - size)
            blocks.append([bx, by, size, richting])
        return blocks

    def update_blocks(self, blocks, fall_speed, current_score):
        for block in blocks:

            if block[3] == 0:
                block[0] -= fall_speed  
                if block[0] < -block[2]:
                    block[0] = random.randint(SCREEN_WIDTH, SCREEN_WIDTH + 150)
                    block[1] = random.randint(0, SCREEN_HEIGHT - block[2])
                    block[2] = random.randint(20, 60)
            else:
                block[0] += fall_speed 
                if block[0] > SCREEN_WIDTH:
                    block[0] = random.randint(-150, -block[2])
                    block[1] = random.randint(0, SCREEN_HEIGHT - block[2])
                    block[2] = random.randint(20, 60)

        zichtbare_score = current_score // 10
        max_b = min(self.game.active_block_count + (zichtbare_score // 50), self.game.active_max_blocks)
        if len(blocks) < max_b:
            size = random.randint(20, 60)
            richting = random.choice([0, 1])
            if richting == 0:
                blocks.append([random.randint(SCREEN_WIDTH, SCREEN_WIDTH + 150), random.randint(0, SCREEN_HEIGHT - size), size, 0])
            else:
                blocks.append([random.randint(-150, -size), random.randint(0, SCREEN_HEIGHT - size), size, 1])

    def render_frame(self, surface, blocks, player_x, player_y, current_score, current_lives, immunity_timer):
        surface.blit(self.background_image, (0, 0))
        if self.bg_images:
            self.bg_scroll += self.bg_speed
        if self.bg_scroll >= SCREEN_HEIGHT:
            self.bg_scroll = 0
            self.current_bg_index = (self.current_bg_index + 1) % len(self.bg_images)
        next_bg_index = (self.current_bg_index + 1) % len(self.bg_images)
        surface.blit(self.bg_images[self.current_bg_index], (0, self.bg_scroll))
        surface.blit(self.bg_images[next_bg_index], (0, self.bg_scroll - SCREEN_HEIGHT))

        for block in blocks:
            x_pos, y_pos, size = block[0], block[1], block[2]
            img = self.meteor_small if size < 40 else (self.meteor_medium if size < 50 else self.meteor_large)
            scaled = pygame.transform.scale(img, (size, size))
            surface.blit(scaled, (x_pos, y_pos))
        if immunity_timer == 0 or (immunity_timer // 5) % 2 == 0:
            img_rect = self.player_img.get_rect(center=(int(player_x), int(player_y)))
            surface.blit(self.player_img, img_rect)    
        score_surface = FONT_SCORE.render("Score: " + str(current_score // 10), True, WHITE)
        surface.blit(score_surface, (SCREEN_WIDTH - 180, 20))
        for i in range(current_lives):
            surface.blit(self.heart_image, (20 + (i * 35), 20))
        pygame.display.flip()

    def run(self, screen) -> GameState:
        audio.play_music(audio_path.gameplay_music, 0.4)
        c = self.game.controls
        x, y = SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100
        x_velocity, y_velocity = 0, 0
        blocks = self.create_blocks()
        score, lives, immunity_timer = 0, 3, 0
        clock = pygame.time.Clock()
        while True:
            clock.tick(60)
            if immunity_timer > 0: immunity_timer -= 1
            for event in pygame.event.get():
                if event.type == pygame.QUIT: return GameState.QUIT
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE: return GameState.TITLE
                    if event.key == c.right: x_velocity = MOVEMENT_SPEED
                    if event.key == c.left: x_velocity = -MOVEMENT_SPEED
                    if event.key == c.up: y_velocity = -MOVEMENT_SPEED
                    if event.key == c.down: y_velocity = MOVEMENT_SPEED
                if event.type == pygame.KEYUP:
                    if event.key in [c.right, c.left]: x_velocity = 0
                    if event.key in [c.up, c.down]: y_velocity = 0
            x += x_velocity
            y += y_velocity
            score += 1
            fall_speed = min(self.game.active_start_speed + (score * self.game.active_speed_increase), MAX_SPEED)
            self.update_blocks(blocks, fall_speed, score)
            x = max(PLAYER_RADIUS, min(SCREEN_WIDTH - PLAYER_RADIUS, x))
            y = max(PLAYER_RADIUS, min(SCREEN_HEIGHT - PLAYER_RADIUS, y))
            player_rect = pygame.Rect(x - PLAYER_RADIUS, y - PLAYER_RADIUS, PLAYER_RADIUS * 2, PLAYER_RADIUS * 2)
            for block in blocks:
                block_rect = pygame.Rect(block[0], block[1], block[2], block[2])
                if player_rect.colliderect(block_rect) and immunity_timer == 0:                
                    lives -= 1
                    audio.play_sfx(audio_path.hit_sound, 0.5)
                    if lives <= 0:
                        self.game.last_score = score // 10
                        return GameState.GAMEOVER
                    immunity_timer = 90
                    break 
            self.render_frame(screen, blocks, x, y, score, lives, immunity_timer)

class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        global FONT_SCORE
        FONT_SCORE = pygame.font.SysFont("Arial", 30, bold=True)
        self.controls = Controls()
        self.last_score = 0
        self.current_playing_level = GameState.PLAYING_LVL1
        self.active_block_count = BLOCK_COUNT
        self.active_start_speed = START_SPEED
        self.active_speed_increase = SPEED_INCREASE
        self.active_max_blocks = MAX_BLOCKS
        self.screen = pygame.display.set_mode(SCREEN_SIZE)
        pygame.display.set_caption("Dodge Blocks")
        self._load_menu_background()
        self.title_screen = TitleScreen(self)
        self.options_screen = OptionsScreen(self)
        self.controls_screen = ControlsScreen(self)
        self.sound_screen = SoundScreen(self)
        self.game_over_screen = GameOverScreen(self)
        self.level_select_screen = LevelSelectScreen(self)
        

    def _load_menu_background(self):
        try:
            self.menu_background = pygame.image.load("images/background.png").convert()
            self.menu_background = pygame.transform.scale(self.menu_background, SCREEN_SIZE)
        except:
            self.menu_background = None

    def draw_menu_background(self, screen):
        if self.menu_background: screen.blit(self.menu_background, (0, 0))
        else: screen.fill(BLUE)

    def game_loop(self, screen, buttons: RenderUpdates) -> GameState:
        while True:
            mouse_up = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT: return GameState.QUIT
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1: mouse_up = True
            self.draw_menu_background(screen)
            for button in buttons:
                ui_action = button.update(pygame.mouse.get_pos(), mouse_up)
                if ui_action is not None: return ui_action
                button.draw(screen)
            pygame.display.flip()

    def run(self):
        game_state = GameState.TITLE
        while True:
            if game_state == GameState.TITLE:
                audio.play_music(audio_path.menu_music, 0.5)
                game_state = self.title_screen.run(self.screen)

            elif game_state == GameState.LEVEL_SELECT:
                game_state = self.level_select_screen.run(self.screen)

            elif game_state == GameState.PLAYING_LVL1:
                self.current_playing_level = GameState.PLAYING_LVL1
                game_state = LevelSession(self).run(self.screen)

            elif game_state == GameState.PLAYING_LVL2:
                self.current_playing_level = GameState.PLAYING_LVL2
                game_state = LevelSession2(self).run(self.screen)

            elif game_state == GameState.PLAYING_LVL3:
                self.current_playing_level = GameState.PLAYING_LVL3
                game_state = LevelSession3(self).run(self.screen)

            elif game_state == GameState.PLAYING_LVL4:
                self.current_playing_level = GameState.PLAYING_LVL4
                game_state = LevelSession(self, bg_color=(75, 0, 130), player_color=WHITE, block_color=YELLOW).run(self.screen)

            elif game_state == GameState.GAMEOVER:
                if self.current_playing_level == GameState.PLAYING_LVL1:
                    lvl_key = "level1"
                elif self.current_playing_level == GameState.PLAYING_LVL2:
                    lvl_key = "level2"
                elif self.current_playing_level == GameState.PLAYING_LVL3:
                    lvl_key = "level 3"
                elif self.current_playing_level == GameState.PLAYING_LVL4: 
                    lvl_key = "level 4"
                else:
                    lvl_key = "level 1"
                
                diff_key = self.level_select_screen.current_difficulty
                if diff_key: 
                    save_highscore(lvl_key, diff_key, self.last_score)
                
                audio.play_music(audio_path.gameover_music, 0.5, loop=0)
                game_state = self.game_over_screen.run(self.screen)


            elif game_state == GameState.OPTIONS:
                game_state = self.options_screen.run(self.screen)

            elif game_state == GameState.CONTROLS:
                game_state = self.controls_screen.run(self.screen)

            elif game_state == GameState.SOUND:
                game_state = self.sound_screen.run(self.screen)

            elif game_state == GameState.QUIT:
                pygame.quit()
                sys.exit()

if __name__ == "__main__":
    Game().run()