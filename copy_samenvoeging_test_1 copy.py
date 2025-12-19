import pygame
import pygame.freetype
import random
import sys
import math
import audio
import audio_path
from enum import Enum
from pygame.sprite import Sprite, RenderUpdates

pygame.init()

REF_WIDTH = 1024
REF_HEIGHT = 768

SCREEN_WIDTH = REF_WIDTH
SCREEN_HEIGHT = REF_HEIGHT
SCREEN_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)
CENTER_X = SCREEN_WIDTH / 2
CENTER_Y = SCREEN_HEIGHT / 2

SCALE_W = 1
SCALE_H = 1
MIN_SCALE = 1

def recalc_display_metrics(screen):
    global SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_SIZE, CENTER_X, CENTER_Y
    global SCALE_W, SCALE_H, MIN_SCALE, FONT_SCORE
    SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
    SCREEN_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)
    CENTER_X = SCREEN_WIDTH / 2
    CENTER_Y = SCREEN_HEIGHT / 2
    SCALE_W = SCREEN_WIDTH / REF_WIDTH
    SCALE_H = SCREEN_HEIGHT / REF_HEIGHT
    MIN_SCALE = min(SCALE_W, SCALE_H)

    FONT_SCORE = pygame.font.SysFont("Arial", max(1, int(30 * MIN_SCALE)), bold = True)

BLUE = (106, 159, 181)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
GAME_BLUE = (0, 100, 255)

FONT_SCORE = None

class PowerUpType(Enum):
    SHIELD = 1
    EXTRA_LIFE = 2

class PowerUp:
    def __init__(self, pu_type, x, y, size, image):
        self.type = pu_type
        self.x = x
        self.y = y
        self.size = size
        self.image = image
        self.collected = False

    def update(self, fall_speed, dt_factor):
        self.y += fall_speed * dt_factor

    def draw(self, surface):
        if self.image:
            surface.blit(self.image, (int(self.x), int(self.y)))
        else:
            color = GREEN if self.type == PowerUpType.SHIELD else YELLOW
            pygame.draw.circle(surface, color, (int(self.x + self.size/2), int(self.y + self.size/2)), self.size//2)


class GameState(Enum):
    QUIT = -1
    TITLE = 0
    PLAYING = 1
    GAMEOVER = 2
    OPTIONS = 3
    VIDEO = 4
    SOUND = 5
    CONTROLS = 6

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
        scaled_size = max(1, int(font_size * MIN_SCALE))
        font = pygame.freetype.SysFont("Courier", scaled_size, bold=True)
        surface, _ = font.render(text=text, fgcolor=text_rgb, bgcolor=None)
        return surface.convert_alpha()

class UIElement(Sprite):
    def __init__(self, ratio_position, text, font_size, text_rgb, action=None):
        super().__init__()
        self.ratio_position = ratio_position
        self.text = text
        self.font_size = font_size
        self.text_rgb = text_rgb
        self.action = action
        self.mouse_over = False
        self.refresh_scaling()

    def refresh_scaling(self):
        new_x = self.ratio_position[0] * SCREEN_WIDTH
        new_y = self.ratio_position[1] * SCREEN_HEIGHT

        default_image = TextFactory.create_surface_with_text(self.text, self.font_size, self.text_rgb)

        if self.action is None:
            highlighted_image = default_image
        else:
            highlighted_image = TextFactory.create_surface_with_text(self.text, int(self.font_size * 1.2), self.text_rgb)

        self.images = [default_image, highlighted_image]
        self.rects = [
            default_image.get_rect(center=(new_x, new_y)),
            highlighted_image.get_rect(center=(new_x, new_y)),
        ]  

    def set_text(self, text, font_size, text_rgb):
        self.text = text
        self.font_size = font_size
        self.text_rgb = text_rgb
        default_image = TextFactory.create_surface_with_text(text, font_size, text_rgb)
        if self.action is None:
            highlighted_image = default_image
        else:
            highlighted_image = TextFactory.create_surface_with_text(text, int(font_size * 1.2), text_rgb)
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
                if audio.sfx_enabled:
                    audio.play_sfx(audio_path.button_sound, 0.5)
                return self.action
        else:
            self.mouse_over = False
        return None

    def draw(self, surface):
        surface.blit(self.image, self.rect)

class MenuScreenBase:
    def __init__(self, game):
        self.game = game

    def build_buttons(self) -> RenderUpdates:
        raise NotImplementedError

    def run(self, screen) -> GameState:
        self.game._load_menu_background()
        return self.game.game_loop(screen, self.build_buttons())
    
class TitleScreen(MenuScreenBase):
    def build_buttons(self):
        start_btn = UIElement((0.5, 0.20), "Start Game", 50, WHITE, GameState.PLAYING)
        options_btn = UIElement((0.5, 0.50), "Options", 50, WHITE, GameState.OPTIONS)
        quit_btn = UIElement((0.5, 0.80), "Afsluiten", 50, WHITE, GameState.QUIT)
        return RenderUpdates(start_btn, options_btn, quit_btn)

class OptionsScreen(MenuScreenBase):
    def build_buttons(self):
        title = UIElement((0.5, 0.2), "SETTINGS", 70, WHITE)
        sound_btn = UIElement((0.5, 0.35), "Sound", 40, WHITE, GameState.SOUND)
        controls_btn = UIElement((0.5, 0.5), "CONTROLS", 40, WHITE, GameState.CONTROLS)
        video_btn = UIElement((0.5, 0.65), "VIDEO", 40, WHITE, GameState.VIDEO)
        back_btn = UIElement((0.5, 0.8), "Back", 40, WHITE, GameState.TITLE)
        return RenderUpdates(title, back_btn, controls_btn, sound_btn, video_btn)

class GameOverScreen(MenuScreenBase):
    def build_buttons(self):
        tekst_btn = UIElement((0.5, 0.2), "GAME OVER", 60, RED)
        score_display = UIElement((0.5, 0.35), f"Jouw Score: {int(self.game.last_score)}", 40, YELLOW)
        restart_btn = UIElement((0.5, 0.5), "Opnieuw spelen", 30, WHITE, GameState.PLAYING)
        menu_btn = UIElement((0.5, 0.65), "Hoofdmenu", 30, WHITE, GameState.TITLE)
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
        font_size = max(1, int(25 * MIN_SCALE))
        font = pygame.freetype.SysFont("Arial", font_size, bold=True)
        text_surf, text_rect = font.render("KEY ALREADY TAKEN!", fgcolor=RED, bgcolor=None)
        x = button.rect.right + int(20 * MIN_SCALE)
        y = int(button.rect.centery - (text_rect.height / 2))
        screen.blit(text_surf, (x, y))
        pygame.display.flip()
        pygame.time.delay(1000)

    def run(self, screen) -> GameState:
        self.game._load_menu_background()
        c = self.game.controls
        title = UIElement((0.5, 0.2), "CLICK TO CHANGE KEYS", 50, WHITE)
        btn_left = UIElement((0.5, 0.35), f"move left: {pygame.key.name(c.left).upper()}", 25, WHITE, "CHANGE_LEFT")
        btn_right = UIElement((0.5, 0.45), f"move right: {pygame.key.name(c.right).upper()}", 25, WHITE, "CHANGE_RIGHT")
        btn_down = UIElement((0.5, 0.55), f"move down: {pygame.key.name(c.down).upper()}", 25, WHITE, "CHANGE_DOWN")
        btn_up = UIElement((0.5, 0.65), f"move up: {pygame.key.name(c.up).upper()}", 25, WHITE, "CHANGE_UP")
        back_btn = UIElement((0.5, 0.8), "Back to Options", 30, WHITE, GameState.OPTIONS)
        buttons = RenderUpdates(title, btn_left, btn_right, btn_down, btn_up, back_btn)

        while True:
            mouse_up = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return GameState.QUIT
                if event.type == pygame.VIDEORESIZE:
                    self.game.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                    screen = self.game.screen
                    recalc_display_metrics(screen)
                    self.game._load_menu_background()
                    for button in buttons:
                        button.refresh_scaling()
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    mouse_up = True

            self.game.draw_menu_background(screen)

            for button in buttons:
                ui_action = button.update(pygame.mouse.get_pos(), mouse_up)

                if ui_action is not None:
                    if isinstance(ui_action, GameState):
                        return ui_action

                    button.set_text("PRESS KEY...", 25, YELLOW)
                    buttons.draw(screen)
                    pygame.display.flip()

                    new = self.wait_for_key()
                    if new is None:
                        return GameState.QUIT

                    if not c.key_is_taken(new):
                        if ui_action == "CHANGE_LEFT":
                            c.left = new
                        elif ui_action == "CHANGE_RIGHT":
                            c.right = new
                        elif ui_action == "CHANGE_DOWN":
                            c.down = new
                        elif ui_action == "CHANGE_UP":
                            c.up = new
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
    def get_music_info():
        if audio.music_enabled:
            return "Music: ON", GREEN
        return "Music: OFF", RED

    @staticmethod
    def get_sfx_info():
        if audio.sfx_enabled:
            return "Effects: ON", GREEN
        return "Effects: OFF", RED

    def run(self, screen) -> GameState:
        music_text, music_col = self.get_music_info()
        effects_text, effects_col = self.get_sfx_info()

        title = UIElement((0.5, 0.2), "SOUNDS", 50, WHITE)
        music_btn = UIElement((0.5, 0.4), music_text, 30, music_col, "TOGGLE_MUSIC")
        effects_btn = UIElement((0.5, 0.6), effects_text, 30, effects_col, "TOGGLE_SFX")
        back_btn = UIElement((0.5, 0.8), "Back to Options", 30, WHITE, GameState.OPTIONS)
        buttons = RenderUpdates(title, music_btn, effects_btn, back_btn)

        while True:
            mouse_up = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return GameState.QUIT
                
                if event.type == pygame.VIDEORESIZE:
                    self.game.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                    recalc_display_metrics(self.game.screen)
                    self.game._load_menu_background()
                    for button in buttons:
                        button.refresh_scaling()

                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    mouse_up = True

            self.game.draw_menu_background(screen)

            for button in buttons:
                ui_action = button.update(pygame.mouse.get_pos(), mouse_up)

                if ui_action == "TOGGLE_MUSIC":
                    audio.toggle_music()
                    new_music_text, new_music_col = self.get_music_info()
                    button.set_text(new_music_text, 30, new_music_col)
                    if audio.music_enabled:
                        audio.play_music(audio_path.menu_music, 0.5)

                elif ui_action == "TOGGLE_SFX":
                    audio.toggle_sfx()
                    if audio.sfx_enabled:
                        audio.play_sfx(audio_path.button_sound, 0.5)
                    new_effects_text, new_effects_col = self.get_sfx_info()
                    button.set_text(new_effects_text, 30, new_effects_col)

                elif isinstance(ui_action, GameState):
                    return ui_action

                button.draw(screen)

            pygame.display.flip()

class VideoScreen:
    def __init__(self, game):
        self.game = game
        self.available_skins = ["spaceshipp.png", "spaceship.png", "spaceship3.png"]
        self.skin_index = self.available_skins.index(self.game.current_skin) if self.game.current_skin in self.available_skins else 0

    def get_skin_text(self):
        name = self.available_skins[self.skin_index].split(".")[0].capitalize()
        return f"Skin: {name}"

    def run(self, screen) -> GameState:
        title = UIElement((0.5, 0.2), "VIDEO", 50, WHITE)
        skin_btn = UIElement((0.5, 0.4), self.get_skin_text(), 35, YELLOW, "CHANGE_SKIN")
        back_btn = UIElement((0.5, 0.8), "Back to Options", 30, WHITE, GameState.OPTIONS)
        buttons = RenderUpdates(title, skin_btn, back_btn)

        while True:
            mouse_up = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return GameState.QUIT
                
                if event.type == pygame.VIDEORESIZE:
                    self.game.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                    recalc_display_metrics(self.game.screen)
                    self.game._load_menu_background()
                    for button in buttons:
                        button.refresh_scaling()

                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    mouse_up = True

            self.game.draw_menu_background(screen)

            try:
                preview_base_size = 150
                skin_corrections = {
                    "spaceshipp.png" : 1.0,
                    "spaceship.png" : 1.5,
                    "spaceship3.png" : 1.5
                }
                multiplier = skin_corrections.get(self.game.current_skin, 1.0)
                preview_size = int(preview_base_size * multiplier * MIN_SCALE)

                preview_path = f"images/{self.game.current_skin}"
                preview_img = pygame.image.load(preview_path).convert_alpha()
                preview_img = pygame.transform.scale(preview_img, (preview_size, preview_size))
                
                preview_rect = preview_img.get_rect(center=(int(SCREEN_WIDTH * 0.5), int(SCREEN_HEIGHT * 0.55)))
                screen.blit(preview_img, preview_rect)
            except:
                pygame.draw.circle(screen, YELLOW, (int(SCREEN_WIDTH * 0.5), int(SCREEN_HEIGHT * 0.55)), int(40 * MIN_SCALE))
            for button in buttons:
                ui_action = button.update(pygame.mouse.get_pos(), mouse_up)

                if ui_action == "CHANGE_SKIN":
                    self.skin_index = (self.skin_index + 1) % len(self.available_skins)
                    self.game.current_skin = self.available_skins[self.skin_index]
                    button.set_text(self.get_skin_text(), 35, YELLOW)

                elif isinstance(ui_action, GameState):
                    return ui_action

                button.draw(screen)

            pygame.display.flip()

class LevelSession:
    def __init__(self, game):
        self.game = game
        self.player_image = None
        self.player_image_flipped = None
        self.background_image = None
        self.meteor_small = None
        self.meteor_medium = None
        self.meteor_large = None
        self.heart_image = None
        self.portal_image = None
        self.last_rendered_score = -1
        self.score_surface = None

        self.bg_scroll = 0
        self.bg_scroll2 = 0
        
       
        self.bg_speed = 1    
        self.bg_speed2 = 4
       

        self.bg_images = []
        self.bg_images2 = []
        self.current_bg_index = 0

        self.block_count = 4
        self.player_radius = 0
        self.player_max_speed = 0
        self.player_accel = 0
        self.player_friction = 0.82
        self.start_speed = 0
        self.speed_increase = 0
        self.max_fall_speed = 0
        self.splitter_chance = 0.10
        self.split_trigger_margin = 0
        self.split_child_spread = 0
        self.split_max_extra = 8
        self.apply_scaling()
        self.shake_intensity = 0

        self.powerups = []
        self.powerup_spawn_chance = 0.003
        self.shield_active = False
        self.shield_timer = 0
        self.pu_shield_img = None
        self.pu_life_img = None

        self.canvas = pygame.Surface(SCREEN_SIZE)

    def apply_scaling(self):
        self.player_radius = max(1, int(20 * MIN_SCALE))
        self.player_max_speed = 11 * MIN_SCALE
        self.player_accel = 1.8 * MIN_SCALE
        self.start_speed = 3.5 * SCALE_H
        self.speed_increase = 0.0007 * SCALE_H
        self.max_fall_speed = 14 * SCALE_H
        self.split_trigger_margin = 40 * MIN_SCALE
        self.split_child_spread = 3.8 * MIN_SCALE

    def load_assets(self):
        base_size = 45
        skin_data = {
            "spaceshipp.png" : {"visual": 1.0, "hitbox": 0.9},
            "spaceship.png" : {"visual": 1.5, "hitbox": 0.6},
            "spaceship3.png" : {"visual": 1.6, "hitbox": 0.85}
        }

        data = skin_data.get(self.game.current_skin, {"visual": 1.0, "hitbox": 0.8})

        final_pixel_size = int(base_size * data["visual"] * MIN_SCALE)

        self.player_radius = int((final_pixel_size // 2) * data["hitbox"])
        try:
            self.player_image = pygame.image.load(f"images/{self.game.current_skin}").convert_alpha()
            self.player_image = pygame.transform.scale(self.player_image, (final_pixel_size, final_pixel_size))
           
            self.player_image_flipped = pygame.transform.flip(self.player_image, False, True)
            
        except:
            self.player_image = None
            self.player_image_flipped = None

        self.bg_images = []
        self.bg_images2 = []
        for i in range(1, 5):
            try:
                img = pygame.image.load(f"images/bgob{i}.png").convert()
                img = pygame.transform.scale(img, SCREEN_SIZE)
                self.bg_images.append(img)

                img_stars = pygame.image.load("images/stars.png").convert_alpha()
                img_stars = pygame.transform.scale(img_stars, SCREEN_SIZE)
                self.bg_images2.append(img_stars)
            except:
                pass
        self.bg_scroll = 0
        self.current_bg_index = 0

        try:
            self.background_image = pygame.image.load("images/galaxy.png").convert()
            self.background_image = pygame.transform.scale(self.background_image, SCREEN_SIZE)
        except:
            self.background_image = None

        try:
            self.meteor_small = pygame.image.load("images/neptunus.png").convert_alpha()
            self.meteor_medium = pygame.image.load("images/mars.png").convert_alpha()
            self.meteor_large = pygame.image.load("images/jupiter.png").convert_alpha()
        except:
            self.meteor_small = None
            self.meteor_medium = None
            self.meteor_large = None

        try:
            heart_size = int(30 * MIN_SCALE)
            self.heart_image = pygame.image.load("images/lives.png").convert_alpha()
            self.heart_image = pygame.transform.scale(self.heart_image, (heart_size, heart_size))
        except:
            self.heart_image = None

        try:
            self.portal_image = pygame.image.load("images/portal.png").convert_alpha()
            portal_w = max(1, int(200 * MIN_SCALE))
            portal_h = max(1, int(40 * MIN_SCALE))
            self.portal_image = pygame.transform.scale(self.portal_image, (portal_w, portal_h))
        except:
            self.portal_image = None

        try:
            pu_size = int(40 * MIN_SCALE)
            self.pu_shield_img = pygame.image.load("images/shield.png").convert_alpha()
            self.pu_shield_img = pygame.transform.scale(self.pu_shield_img, (pu_size, pu_size))
            self.pu_life_img = pygame.image.load("images/lives.png").convert_alpha()
            self.pu_life_img = pygame.transform.scale(self.pu_life_img, (pu_size, pu_size))
        except:
            self.pu_shield_img = None
            self.pu_life_img = None

    def make_block(self, current_score, level_mode="down"):
        base_size = random.randint(20, 65)
        size = max(1, int(base_size * MIN_SCALE))
        offset = max(1, int(500 * MIN_SCALE))

        if level_mode == "side":
            x = random.randint(SCREEN_WIDTH, SCREEN_WIDTH + offset)
            y = random.randint(0, max(1, SCREEN_HEIGHT - size))
        elif level_mode == "up":
            x = random.randint(0, max(1, SCREEN_WIDTH - size))
            y = random.randint(SCREEN_HEIGHT, SCREEN_HEIGHT + offset)
        else:
            x = random.randint(0, max(1, SCREEN_WIDTH - size))
            y = random.randint(-offset, 0)

        is_splitter = False
        is_tracker = False
        is_zigzag = False

        if random.random() < 0.10:
            is_splitter = True
        elif (current_score // 10) >= 500 and random.random() < 0.30:
            is_tracker = True
        elif current_score > 2500 and random.random() < 0.3:
            is_zigzag = True

        drift_strength = 1.2 * MIN_SCALE
        
        block_img = None
        if self.meteor_small and self.meteor_medium and self.meteor_large:
            boundary_small = 40 * MIN_SCALE
            boundary_medium = 50 * MIN_SCALE
            
            if size < boundary_small:
                base_img = self.meteor_small
            elif size < boundary_medium:
                base_img = self.meteor_medium
            else:
                base_img = self.meteor_large
            
            block_img = pygame.transform.scale(base_img, (size, size))
        
        return {
            "x": float(x),
            "y": float(y),
            "size": size,
            "image": block_img,
            "splitter": is_splitter,
            "split_done": False,
            "vx": random.uniform(-drift_strength, drift_strength),
            "vy": random.uniform(-0.5 * MIN_SCALE, 0.5 * MIN_SCALE),
            "zigzag": is_zigzag,
            "zigzag_offset": random.randint(0, 10000),
            "tracker": is_tracker
        }

    def create_blocks(self, level_mode="down"):
        return [self.make_block(0, level_mode) for _ in range(self.block_count)]

    def respawn_block(self, block,current_score, level_mode):
        block.update(self.make_block(current_score, level_mode))

    def maybe_split(self, blocks, block, level_mode, max_allowed_blocks):
        if not block["splitter"] or block["split_done"]:
            return
        if len(blocks) >= max_allowed_blocks:
            return

        if level_mode == "side":
            if abs(block["x"] - CENTER_X) > self.split_trigger_margin:
                return
        else:
            if abs(block["y"] - CENTER_Y) > self.split_trigger_margin:
                return
            
        if audio.sfx_enabled:
            audio.play_sfx(audio_path.split_sound, 0.2)

        block["split_done"] = True
        parent_size = block["size"]
        child_size = max(int(18 * MIN_SCALE), parent_size // 2)
        cx, cy = block["x"] + parent_size / 4, block["y"] + parent_size / 4

        base_props = {"splitter": False, "split_done": True, "tracker": False, "zigzag": False, "zigzag_offset": 0}

        if level_mode == "side":
            c1 = {"x": cx, "y": cy, "size": child_size, "vx": block["vx"], "vy": -self.split_child_spread, **base_props}
            c2 = {"x": cx, "y": cy, "size": child_size, "vx": block["vx"], "vy": +self.split_child_spread, **base_props}
        else:
            c1 = {"x": cx, "y": cy, "size": child_size, "vx": -self.split_child_spread, "vy": block["vy"], **base_props}
            c2 = {"x": cx, "y": cy, "size": child_size, "vx": +self.split_child_spread, "vy": block["vy"], **base_props}

        for child in [c1, c2]:
            if self.meteor_small and self.meteor_medium and self.meteor_large:
                boundary_small = 40 * MIN_SCALE
                boundary_medium = 50 * MIN_SCALE
                if child["size"] < boundary_small: base = self.meteor_small
                elif child["size"] < boundary_medium: base = self.meteor_medium
                else: base = self.meteor_large
                child["image"] = pygame.transform.scale(base, (child["size"], child["size"]))
            else: child["image"] = None

        blocks.extend([c1, c2])

    def update_blocks(self, blocks, fall_speed, current_score, level_mode, dt_factor, player_x, player_y):
        extra_planeten = (current_score // 800)
        max_allowed = self.block_count + extra_planeten + self.split_max_extra

        tracking_strength = 1.5 * MIN_SCALE * dt_factor 

        for block in blocks:
            if block.get("zigzag") == True:
                tijd = pygame.time.get_ticks() + block["zigzag_offset"]
                golf = math.sin(tijd * 0.005) * (4 * MIN_SCALE) * dt_factor
                
                if level_mode == "side":
                    block["y"] += golf
                else:
                    block["x"] += golf

            if block.get("tracker") == True:
                block_center_x = block["x"] + block["size"] / 2
                block_center_y = block["y"] + block["size"] / 2
                
                if level_mode == "side":
                    if block_center_y < player_y:
                        block["y"] += tracking_strength
                    elif block_center_y > player_y:
                        block["y"] -= tracking_strength
                else:
                    if block_center_x < player_x:
                        block["x"] += tracking_strength
                    elif block_center_x > player_x:
                        block["x"] -= tracking_strength

            adjusted_fall_speed = fall_speed * dt_factor
            adjusted_vx = block["vx"] * dt_factor
            adjusted_vy = block["vy"] * dt_factor
            
            s = block["size"]

            if level_mode == "side":
                block["x"] += fall_speed
                block["y"] += block["vy"]
                block["x"] += block["vx"]
                self.maybe_split(blocks, block, level_mode, max_allowed)
                if block["x"] < -s:
                    self.respawn_block(block, current_score, level_mode)
            else:
                block["y"] += fall_speed
                block["x"] += block["vx"]
                block["y"] += block["vy"]
                self.maybe_split(blocks, block, level_mode, max_allowed)
                if fall_speed > 0 and block["y"] > SCREEN_HEIGHT:
                    self.respawn_block(block, current_score, "down")
                elif fall_speed < 0 and block["y"] < -s:
                    self.respawn_block(block, current_score, "up")

        if len(blocks) < self.block_count + extra_planeten:
            blocks.append(self.make_block(current_score, level_mode))

    def render_frame(self, surface, blocks, px, py, score, lives, immunity, portal_rect, portal_active, player_vx, level_flipped):
        
        offset_x = 0
        offset_y = 0
        if self.shake_intensity > 0:
            offset_x = random.randint(-self.shake_intensity, self.shake_intensity)
            offset_y = random.randint(-self.shake_intensity, self.shake_intensity)
            self.shake_intensity = max(0, self.shake_intensity - 1)
        
        self.canvas.fill(BLACK) 

        if self.bg_images:
            curr_img = self.bg_images[self.current_bg_index]
            self.canvas.blit(curr_img, (0, self.bg_scroll))
            
            if self.bg_scroll > 0:
                nxt_idx = (self.current_bg_index + 1) % len(self.bg_images)
                self.canvas.blit(self.bg_images[nxt_idx], (0, self.bg_scroll - SCREEN_HEIGHT))
            elif self.bg_scroll < 0:
                prev_idx = (self.current_bg_index - 1) % len(self.bg_images)
                self.canvas.blit(self.bg_images[prev_idx], (0, self.bg_scroll + SCREEN_HEIGHT))

        if self.bg_images2:
            curr_stars = self.bg_images2[0]
            self.canvas.blit(curr_stars, (0, self.bg_scroll2))
            
            if self.bg_scroll2 > 0:
                self.canvas.blit(curr_stars, (0, self.bg_scroll2 - SCREEN_HEIGHT))
            elif self.bg_scroll2 < 0:
                self.canvas.blit(curr_stars, (0, self.bg_scroll2 + SCREEN_HEIGHT))
        
        elif self.background_image:
            self.canvas.blit(self.background_image, (0, 0))

        if portal_rect and self.portal_image:
            self.canvas.blit(self.portal_image, portal_rect)

        for pu in self.powerups:
            img = self.pu_shield_img if pu["type"] == "SHIELD" else self.pu_life_img
            if img:
                self.canvas.blit(img, (int(pu["x"]), int(pu["y"])))
            else:
                color = (0, 255, 255) if pu["type"] == "SHIELD" else (255, 50, 50)
                center_pos = (int(pu["x"] + pu["size"]/2), int(pu["y"] + pu["size"]/2))
                pygame.draw.circle(self.canvas, color, center_pos, pu["size"]//2)

        for b in blocks:
            bx = int(b["x"])
            by = int(b["y"])
            if b.get("image") is None:
                if self.meteor_small and self.meteor_medium and self.meteor_large:
                    boundary_small = 40 * MIN_SCALE
                    boundary_medium = 50 * MIN_SCALE
                    if b["size"] < boundary_small: base_img = self.meteor_small
                    elif b["size"] < boundary_medium: base_img = self.meteor_medium
                    else: base_img = self.meteor_large
                    b["image"] = pygame.transform.scale(base_img, (b["size"], b["size"]))
                else: b["image"] = None

            if b.get("image"):
                self.canvas.blit(b["image"], (bx, by))
            else:
                pygame.draw.rect(surface, WHITE, (int(b["x"]), int(b["y"]), b["size"], b["size"]))

            if b.get("tracker") == True:
                center = (int(b["x"] + b["size"] // 2), int(b["y"] + b["size"] // 2))
                radius = int(b["size"] // 2 + (5 * MIN_SCALE))
                pygame.draw.circle(self.canvas, (255, 50, 50), center, radius, 2)

            if b["splitter"] and not b["split_done"]:
                radius = int((b["size"] // 2) + (8 * MIN_SCALE))
                pygame.draw.circle(self.canvas, YELLOW, (int(b["x"] + b["size"] // 2), int(b["y"] + b["size"] // 2)), max(1, radius), 3)

        if immunity <= 0 or (int(immunity) // 5) % 2 == 0:
            if self.player_image:
                if level_flipped and self.player_image_flipped:
                    img_to_draw = self.player_image_flipped
                    tilt_angle = -(player_vx * -2.5) 
                else:
                    img_to_draw = self.player_image
                    tilt_angle = player_vx * -2.5

                rotated_player = pygame.transform.rotozoom(img_to_draw, tilt_angle, 1.0)
                
                player_rect = rotated_player.get_rect(center=(int(px), int(py)))
                self.canvas.blit(rotated_player, player_rect)
            else:
                pygame.draw.circle(surface, GAME_BLUE, (int(px), int(py)), self.player_radius)
            
            if self.shield_active:
                pygame.draw.circle(self.canvas, (0, 200, 255), (int(px), int(py)), self.player_radius + 10, 3)
            
        surface.blit(self.canvas, (offset_x, offset_y))

        current_display_score = int(score // 10)
        
        if current_display_score != self.last_rendered_score:
            self.score_surface = FONT_SCORE.render(f"Score: {current_display_score}", True, WHITE)
            self.last_rendered_score = current_display_score
        
        score_x = SCREEN_WIDTH - max(1, int(200 * MIN_SCALE))
        score_y = max(0, int(20 * MIN_SCALE))
        
        if self.score_surface:
            surface.blit(self.score_surface, (score_x, score_y))

        if self.heart_image:
            start_x = max(0, int(20 * MIN_SCALE))
            y_pos = max(0, int(20 * MIN_SCALE))
            spacing = max(1, int(35 * MIN_SCALE))
            for i in range(lives):
                surface.blit(self.heart_image, (start_x + (i * spacing), y_pos))
        else:
            surface.blit(FONT_SCORE.render(f"Lives: {lives}", True, RED), (20, 20))

        pygame.display.flip()

    def run(self, screen) -> GameState:
        audio.play_music(audio_path.gameplay_music, 0.4)
        self.load_assets()

        c = self.game.controls
        clock = pygame.time.Clock()

        x, y = CENTER_X, SCREEN_HEIGHT - int(100 * MIN_SCALE)
        player_vx = 0.0
        player_vy = 0.0

        blocks = self.create_blocks("down")
        score = 0
        lives = 3
        immunity_timer = 0
        
        level_flipped = False  
        next_portal_score = 250

        while True:
            dt_ms = clock.tick(60) 
            dt = dt_ms / 1000.0 
            
            if dt > 0.1: dt = 0.1 
            
            dt_factor = dt * 60

            if immunity_timer > 0:
                immunity_timer -= 1 * dt_factor
            
            if self.shield_active:
                self.shield_timer -= 1 * dt_factor
                if self.shield_timer <= 0:
                    self.shield_active = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return GameState.QUIT
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return GameState.TITLE

                if event.type == pygame.VIDEORESIZE:
                    old_w, old_h = SCREEN_WIDTH, SCREEN_HEIGHT
                    rx = x / old_w if old_w else 0.5
                    ry = y / old_h if old_h else 0.5

                    self.game.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                    screen = self.game.screen
                    recalc_display_metrics(screen)
                    
                    self.canvas = pygame.Surface(SCREEN_SIZE)
                    
                    self.game._load_menu_background()
                    self.apply_scaling()
                    self.load_assets()
                    self.bg_scroll = 0
                    self.current_bg_index = 0

                    x = rx * SCREEN_WIDTH
                    y = ry * SCREEN_HEIGHT

                    for block in blocks:
                        block["image"] = None

                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            return GameState.TITLE

            current_score_int = int(score // 10)
            portal_active = (current_score_int >= next_portal_score)

            keys = pygame.key.get_pressed()
            input_x = 0
            input_y = 0

            if not portal_active:
                if keys[c.left]:
                    input_x -= 1
                if keys[c.right]:
                    input_x += 1
                if keys[c.up]:
                    input_y -= 1
                if keys[c.down]:
                    input_y += 1

            if input_x != 0:
                player_vx += input_x * self.player_accel * dt_factor
            else:
                player_vx *= math.pow(self.player_friction, dt_factor)
            if input_y != 0:
                player_vy += input_y * self.player_accel * dt_factor
            else:
                player_vy *= math.pow(self.player_friction, dt_factor)

            speed = math.sqrt(player_vx * player_vx + player_vy * player_vy)
            if speed > self.player_max_speed:
                scale = self.player_max_speed / speed
                player_vx *= scale
                player_vy *= scale

            if abs(player_vx) < 0.1:
                player_vx = 0.0
            if abs(player_vy) < 0.1:
                player_vy = 0.0

            x += player_vx * dt_factor
            y += player_vy * dt_factor

            if self.bg_images:
                scroll_delta = self.bg_speed * dt_factor
                if not level_flipped:
                    self.bg_scroll += scroll_delta
                    if self.bg_scroll >= SCREEN_HEIGHT:
                        self.bg_scroll = 0
                        self.current_bg_index = (self.current_bg_index + 1) % len(self.bg_images)
                else:
                    self.bg_scroll -= scroll_delta
                    if self.bg_scroll <= -SCREEN_HEIGHT:
                        self.bg_scroll = 0
                        self.current_bg_index = (self.current_bg_index - 1) % len(self.bg_images)

            if self.bg_images2:
                scroll_delta2 = self.bg_speed2 * dt_factor
                if not level_flipped:
                    self.bg_scroll2 += scroll_delta2
                    if self.bg_scroll2 >= SCREEN_HEIGHT:
                        self.bg_scroll2 = 0
                else:
                    self.bg_scroll2 -= scroll_delta2
                    if self.bg_scroll2 <= -SCREEN_HEIGHT:
                        self.bg_scroll2 = 0

            score += 1 * dt_factor

            if not level_flipped:
                fall_speed = min(self.start_speed + (score * self.speed_increase), self.max_fall_speed)
                level_mode = "down"
            else:
                fall_speed = max(-self.start_speed - (score * self.speed_increase), -self.max_fall_speed)
                level_mode = "up"

            self.update_blocks(blocks, fall_speed, score, level_mode, dt_factor, x, y)

            x = max(self.player_radius, min(SCREEN_WIDTH - self.player_radius, x))
            y = max(self.player_radius, min(SCREEN_HEIGHT - self.player_radius, y))

            player_rect = pygame.Rect(int(x) - self.player_radius, int(y) - self.player_radius, self.player_radius * 2, self.player_radius * 2)

            if random.random() < self.powerup_spawn_chance and not portal_active:
                pu_type = "SHIELD" if random.random() > 0.4 else "LIFE"
                
                if level_flipped:
                    start_y = SCREEN_HEIGHT + 50
                else:
                    start_y = -50
                    
                self.powerups.append({"x": random.randint(50, SCREEN_WIDTH-50), "y": start_y, "type": pu_type, "size": int(40*MIN_SCALE)})

            for pu in self.powerups[:]:
                pu["y"] += fall_speed * dt_factor
                pu_r = pygame.Rect(pu["x"], pu["y"], pu["size"], pu["size"])
                if player_rect.colliderect(pu_r):
                    if pu["type"] == "SHIELD": 
                        self.shield_active = True
                        self.shield_timer = 300 
                    else: 
                        lives = min(lives + 1, 4)
                    
                    if audio.sfx_enabled: audio.play_sfx(audio_path.heal_sound, 0.6)
                    self.powerups.remove(pu)
                elif pu["y"] > SCREEN_HEIGHT + 100 or pu["y"] < -200:
                    self.powerups.remove(pu)

            portal_rect = None
            p_w = max(1, int(200 * MIN_SCALE))
            p_h = max(1, int(40 * MIN_SCALE))

            if portal_active:
                if not level_flipped:
                    portal_rect = pygame.Rect(int(CENTER_X - (p_w // 2)), int(20 * MIN_SCALE), p_w, p_h)
                else:
                    portal_rect = pygame.Rect(int(CENTER_X - (p_w // 2)), SCREEN_HEIGHT - int(40 * MIN_SCALE), p_w, p_h)

            if portal_rect:
                dx, dy = portal_rect.centerx - x, portal_rect.centery - y
                x += dx * 0.05 * dt_factor
                y += dy * 0.05 * dt_factor
                player_rect.center = (int(x), int(y))

                if player_rect.colliderect(portal_rect):
                    level_flipped = not level_flipped 
                    next_portal_score += 250         

                    if level_flipped:
                        x, y = CENTER_X, int(100 * MIN_SCALE)
                        blocks = self.create_blocks("up")
                    else:
                        x, y = CENTER_X, SCREEN_HEIGHT - int(100 * MIN_SCALE)
                        blocks = self.create_blocks("down")
                    
                    player_vx, player_vy = 0.0, 0.0
                    continue

            for block in blocks:
                planet_radius = block["size"] / 2
                hitbox_radius = planet_radius - (6 * MIN_SCALE) 
                
                planet_center_x = block["x"] + planet_radius
                planet_center_y = block["y"] + planet_radius

                distance = math.hypot(x - planet_center_x, y - planet_center_y)

                if distance < (self.player_radius + hitbox_radius) and immunity_timer <= 0 and not portal_active:
                    if self.shield_active:
                        self.shield_active = False
                        self.shield_timer = 0
                        immunity_timer = 60
                        if audio.sfx_enabled:
                            audio.play_sfx(audio_path.hit_sound, 0.3)
                    else:
                        lives -= 1
                        self.shake_intensity = 15
                        if lives > 0:
                            audio.play_sfx(audio_path.hit_sound, 0.5)
                            immunity_timer = 90 
                        else:
                            self.game.last_score = score // 10
                            pygame.mouse.set_visible(True)
                            return GameState.GAMEOVER
                    break

            self.render_frame(screen, blocks, x, y, score, lives, immunity_timer, portal_rect, portal_active, player_vx, level_flipped)

class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()

        self.controls = Controls()
        self.last_score = 0
        self.menu_background = None
        self.current_skin = "spaceshipp.png"

        self.screen = pygame.display.set_mode((REF_WIDTH, REF_HEIGHT), pygame.RESIZABLE)
        recalc_display_metrics(self.screen)

        global FONT_SCORE
        FONT_SCORE = pygame.font.SysFont("Arial", max(1, int(30 * MIN_SCALE)), bold=True)

        pygame.display.set_caption("Space Dodger")

        self._load_menu_background()

        self.title_screen = TitleScreen(self)
        self.options_screen = OptionsScreen(self)
        self.controls_screen = ControlsScreen(self)
        self.sound_screen = SoundScreen(self)
        self.game_over_screen = GameOverScreen(self)
        self.video_screen = VideoScreen(self)

    def _load_menu_background(self):
        try:
            self.menu_background = pygame.image.load("images/background.png").convert()
            self.menu_background = pygame.transform.scale(self.menu_background, SCREEN_SIZE)
        except:
            self.menu_background = None

    def draw_menu_background(self, screen):
        if self.menu_background:
            screen.blit(self.menu_background, (0, 0))
        else:
            screen.fill(BLUE)

    def game_loop(self, screen, buttons: RenderUpdates) -> GameState:
        screen = self.screen
        self._load_menu_background()
        for btn in buttons:
            if hasattr(btn, "refresh_scaling"):
                btn.refresh_scaling()

        while True:
            if not pygame.mixer.music.get_busy():
                audio.play_music(audio_path.menu_music, 0.5)

            mouse_up = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return GameState.QUIT
                if event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                    screen = self.screen
                    recalc_display_metrics(self.screen)
                    self._load_menu_background()
                    for btn in buttons:
                        if hasattr(btn, "refresh_scaling"):
                            btn.refresh_scaling()


                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    mouse_up = True
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return GameState.QUIT

            self.draw_menu_background(screen)

            for button in buttons:
                ui_action = button.update(pygame.mouse.get_pos(), mouse_up)
                if ui_action is not None:
                    return ui_action
                button.draw(screen)

            pygame.display.flip()

    def run(self):
        game_state = GameState.TITLE

        while True:
            if game_state == GameState.TITLE:
                audio.play_music(audio_path.menu_music, 0.5)
                game_state = self.title_screen.run(self.screen)
            elif game_state == GameState.PLAYING:
                game_state = LevelSession(self).run(self.screen)
            elif game_state == GameState.GAMEOVER:
                self._load_menu_background()
                audio.play_music(audio_path.gameover_music, 0.5, loop=0)
                game_state = self.game_over_screen.run(self.screen)
            elif game_state == GameState.OPTIONS:
                game_state = self.options_screen.run(self.screen)
            elif game_state == GameState.CONTROLS:
                game_state = self.controls_screen.run(self.screen)
            elif game_state == GameState.SOUND:
                game_state = self.sound_screen.run(self.screen)
            elif game_state == GameState.VIDEO:
                game_state = self.video_screen.run(self.screen)
            elif game_state == GameState.QUIT:
                pygame.quit()
                sys.exit()

def main():
    Game().run()

if __name__ == "__main__":
    main()



