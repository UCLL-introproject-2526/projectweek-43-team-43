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
    global SCALE_W, SCALE_H, MIN_SCALE
    SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
    SCREEN_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)
    CENTER_X = SCREEN_WIDTH / 2
    CENTER_Y = SCREEN_HEIGHT / 2
    SCALE_W = SCREEN_WIDTH / REF_WIDTH
    SCALE_H = SCREEN_HEIGHT / REF_HEIGHT
    MIN_SCALE = min(SCALE_W, SCALE_H)

BLUE = (106, 159, 181)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
GAME_BLUE = (0, 100, 255)

FONT_SCORE = None

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
    def __init__(self, center_position, text, font_size, text_rgb, action=None):
        super().__init__()
        self.mouse_over = False
        self.action = action
        self.font_size = font_size
        self.text_rgb = text_rgb

        default_image = TextFactory.create_surface_with_text(text, font_size, text_rgb)
        highlighted_image = TextFactory.create_surface_with_text(text, int(font_size * 1.2), text_rgb)

        self.images = [default_image, highlighted_image]
        self.rects = [
            default_image.get_rect(center=center_position),
            highlighted_image.get_rect(center=center_position),
        ]

    def set_text(self, text, font_size, text_rgb):
        default_image = TextFactory.create_surface_with_text(text, font_size, text_rgb)
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
        return self.game.game_loop(screen, self.build_buttons())

class TitleScreen(MenuScreenBase):
    def build_buttons(self):
        start_btn = UIElement((CENTER_X, 250 * SCALE_H), "Start Game", 50, WHITE, GameState.PLAYING)
        options_btn = UIElement((CENTER_X, 400 * SCALE_H), "Options", 50, WHITE, GameState.OPTIONS)
        quit_btn = UIElement((CENTER_X, 550 * SCALE_H), "Afsluiten", 50, WHITE, GameState.QUIT)
        return RenderUpdates(start_btn, options_btn, quit_btn)

class OptionsScreen(MenuScreenBase):
    def build_buttons(self):
        title = UIElement((CENTER_X, 150 * SCALE_H), "SETTINGS", 70, WHITE)
        sound_btn = UIElement((CENTER_X, 300 * SCALE_H), "Sound", 40, WHITE, GameState.SOUND)
        controls_btn = UIElement((CENTER_X, 400 * SCALE_H), "CONTROLS", 40, WHITE, GameState.CONTROLS)
        video_btn = UIElement((CENTER_X, 500 * SCALE_H), "VIDEO", 40, WHITE, GameState.VIDEO)
        back_btn = UIElement((CENTER_X, 600 * SCALE_H), "Back", 40, WHITE, GameState.TITLE)
        return RenderUpdates(title, back_btn, controls_btn, sound_btn, video_btn)

class GameOverScreen(MenuScreenBase):
    def build_buttons(self):
        tekst_btn = UIElement((CENTER_X, 150 * SCALE_H), "GAME OVER", 60, RED)
        score_display = UIElement((CENTER_X, 250 * SCALE_H), f"Jouw Score: {self.game.last_score}", 40, YELLOW)
        restart_btn = UIElement((CENTER_X, 400 * SCALE_H), "Opnieuw spelen", 30, WHITE, GameState.PLAYING)
        menu_btn = UIElement((CENTER_X, 500 * SCALE_H), "Hoofdmenu", 30, WHITE, GameState.TITLE)
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
        c = self.game.controls
        title = UIElement((CENTER_X, 100 * SCALE_H), "CLICK TO CHANGE KEYS", 50, WHITE)
        btn_left = UIElement((CENTER_X, 200 * SCALE_H), f"move left: {pygame.key.name(c.left).upper()}", 25, WHITE, "CHANGE_LEFT")
        btn_right = UIElement((CENTER_X, 300 * SCALE_H), f"move right: {pygame.key.name(c.right).upper()}", 25, WHITE, "CHANGE_RIGHT")
        btn_down = UIElement((CENTER_X, 400 * SCALE_H), f"move down: {pygame.key.name(c.down).upper()}", 25, WHITE, "CHANGE_DOWN")
        btn_up = UIElement((CENTER_X, 500 * SCALE_H), f"move up: {pygame.key.name(c.up).upper()}", 25, WHITE, "CHANGE_UP")
        back_btn = UIElement((CENTER_X, 600 * SCALE_H), "Back to Options", 30, WHITE, GameState.OPTIONS)
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

        title = UIElement((CENTER_X, 100 * SCALE_H), "SOUNDS", 50, WHITE)
        music_btn = UIElement((CENTER_X, 300 * SCALE_H), music_text, 30, music_col, "TOGGLE_MUSIC")
        effects_btn = UIElement((CENTER_X, 400 * SCALE_H), effects_text, 30, effects_col, "TOGGLE_SFX")
        back_btn = UIElement((CENTER_X, 600 * SCALE_H), "Back to Options", 30, WHITE, GameState.OPTIONS)
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
                    new_music_text, new_music_col = self.get_music_info()
                    button.set_text(new_music_text, 30, new_music_col)
                    if audio.music_enabled:
                        audio.play_music(audio_path.menu_music, 0.5)

                elif ui_action == "TOGGLE_SFX":
                    audio.toggle_sfx()
                    new_effects_text, new_effects_col = self.get_sfx_info()
                    button.set_text(new_effects_text, 30, new_effects_col)
                    if audio.sfx_enabled:
                        audio.play_sfx(audio_path.hit_sound, 0.5)

                elif isinstance(ui_action, GameState):
                    return ui_action

                button.draw(screen)

            pygame.display.flip()

class VideoScreen:
    def __init__(self, game):
        self.game = game
        self.available_skins = ["spaceshipp.png", "spaceship.png"]
        self.skin_index = self.available_skins.index(self.game.current_skin) if self.game.current_skin in self.available_skins else 0

    def get_skin_text(self):
        name = self.available_skins[self.skin_index].split(".")[0].capitalize()
        return f"Skin: {name}"

    def run(self, screen) -> GameState:
        title = UIElement((CENTER_X, 100 * SCALE_H), "VIDEO", 50, WHITE)
        skin_btn = UIElement((CENTER_X, 300 * SCALE_H), self.get_skin_text(), 35, YELLOW, "CHANGE_SKIN")
        back_btn = UIElement((CENTER_X, 600 * SCALE_H), "Back to Options", 30, WHITE, GameState.OPTIONS)
        buttons = RenderUpdates(title, skin_btn, back_btn)

        while True:
            mouse_up = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return GameState.QUIT
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    mouse_up = True

            self.game.draw_menu_background(screen)

            try:
                preview_size = max(1, int(120 * MIN_SCALE))
                preview_path = f"images/{self.game.current_skin}"
                preview_img = pygame.image.load(preview_path).convert_alpha()
                preview_img = pygame.transform.scale(preview_img, (preview_size, preview_size))
                preview_rect = preview_img.get_rect(center=(int(CENTER_X), int(450 * SCALE_H)))
                screen.blit(preview_img, preview_rect)
            except:
                pygame.draw.circle(screen, YELLOW, (int(CENTER_X), int(450 * SCALE_H)), max(1, int(40 * MIN_SCALE)))

            for button in buttons:
                ui_action = button.update(pygame.mouse.get_pos(), mouse_up)

                if ui_action == "CHANGE_SKIN":
                    self.skin_index = (self.skin_index + 1) % len(self.available_skins)
                    self.game.current_skin = self.available_skins[self.skin_index]
                    button.set_text(self.get_skin_text(), 35, YELLOW)
                    audio.play_sfx(audio_path.hit_sound, 0.2)

                elif isinstance(ui_action, GameState):
                    return ui_action

                button.draw(screen)

            pygame.display.flip()

class LevelSession:
    def __init__(self, game):
        self.game = game
        self.player_image = None
        self.background_image = None
        self.meteor_small = None
        self.meteor_medium = None
        self.meteor_large = None
        self.heart_image = None
        self.portal_image = None

        self.block_count = 4
        self.player_radius = max(1, int(20 * MIN_SCALE))
        self.player_max_speed = 11 * MIN_SCALE
        self.player_accel = 1.8 * MIN_SCALE
        self.player_friction = 0.82

        self.start_speed = 3.5 * SCALE_H
        self.speed_increase = 0.0007 * SCALE_H
        self.max_fall_speed = 14 * SCALE_H

        self.splitter_chance = 0.22
        self.split_trigger_margin = 40 * MIN_SCALE
        self.split_child_spread = 3.8 * MIN_SCALE
        self.split_max_extra = 8

        self.bg_scroll = 0
        self.bg_speed = 2
        self.current_bg_index = 0

    def load_assets(self):
        try:
            self.player_image = pygame.image.load(f"images/{self.game.current_skin}").convert_alpha()
            self.player_image = pygame.transform.scale(self.player_image, (self.player_radius * 2, self.player_radius * 2))
        except:
            self.player_image = None

        self.bg_images = []
        for i in range(1, 5):
            try:
                img = pygame.image.load(f"images/bgob{i}.png").convert()
                img = pygame.transform.scale(img, SCREEN_SIZE)
                self.bg_images.append(img)
            except Exception as e:
                print(f"Kon afbeelding images/bgob{i}.png niet laden: {e}")

        try:
            self.meteor_small = pygame.image.load("images/neptunus.png").convert_alpha()
            self.meteor_medium = pygame.image.load("images/mars.png").convert_alpha()
            self.meteor_large = pygame.image.load("images/jupiter.png").convert_alpha()
        except:
            self.meteor_small = None
            self.meteor_medium = None
            self.meteor_large = None

        try:
            self.heart_image = pygame.image.load("images/lives.png").convert_alpha()
            heart_size = max(1, int(30 * MIN_SCALE))
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

    def make_block(self, level_mode="down"):
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

        is_splitter = (random.random() < self.splitter_chance)
        drift_strength = 1.2 * MIN_SCALE
        return {
            "x": float(x),
            "y": float(y),
            "size": size,
            "splitter": is_splitter,
            "split_done": False,
            "vx": random.uniform(-drift_strength, drift_strength),
            "vy": random.uniform(-0.5 * MIN_SCALE, 0.5 * MIN_SCALE),
        }

    def create_blocks(self, level_mode="down"):
        return [self.make_block(level_mode) for _ in range(self.block_count)]

    def respawn_block(self, block, level_mode):
        block.update(self.make_block(level_mode))

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

        block["split_done"] = True
        parent_size = block["size"]
        child_size = max(int(18 * MIN_SCALE), parent_size // 2)
        cx, cy = block["x"] + parent_size / 4, block["y"] + parent_size / 4

        if level_mode == "side":
            c1 = {"x": cx, "y": cy, "size": child_size, "splitter": False, "split_done": True, "vx": block["vx"], "vy": -self.split_child_spread}
            c2 = {"x": cx, "y": cy, "size": child_size, "splitter": False, "split_done": True, "vx": block["vx"], "vy": +self.split_child_spread}
        else:
            c1 = {"x": cx, "y": cy, "size": child_size, "splitter": False, "split_done": True, "vx": -self.split_child_spread, "vy": block["vy"]}
            c2 = {"x": cx, "y": cy, "size": child_size, "splitter": False, "split_done": True, "vx": +self.split_child_spread, "vy": block["vy"]}

        blocks.extend([c1, c2])

    def update_blocks(self, blocks, fall_speed, current_score, level_mode):
        extra_planeten = (current_score // 800)
        max_allowed = self.block_count + extra_planeten + self.split_max_extra

        for block in blocks:
            s = block["size"]
            if level_mode == "side":
                block["x"] += fall_speed
                block["y"] += block["vy"]
                block["x"] += block["vx"]
                self.maybe_split(blocks, block, level_mode, max_allowed)
                if block["x"] < -s:
                    self.respawn_block(block, level_mode)
            else:
                block["y"] += fall_speed
                block["x"] += block["vx"]
                block["y"] += block["vy"]
                self.maybe_split(blocks, block, level_mode, max_allowed)
                if fall_speed > 0 and block["y"] > SCREEN_HEIGHT:
                    self.respawn_block(block, "down")
                elif fall_speed < 0 and block["y"] < -s:
                    self.respawn_block(block, "up")

        if len(blocks) < self.block_count + extra_planeten:
            blocks.append(self.make_block(level_mode))

    def render_frame(self, surface, blocks, px, py, score, lives, immunity, portal_rect, portal_active):
        surface.fill(BLACK)
        if self.bg_images:
            self.bg_scroll += self.bg_speed
        
        if self.bg_scroll >= SCREEN_HEIGHT:
            self.bg_scroll = 0
            self.current_bg_index = (self.current_bg_index + 1) % len(self.bg_images)
        
        next_bg_index = (self.current_bg_index + 1) % len(self.bg_images)
        
        surface.blit(self.bg_images[self.current_bg_index], (0, self.bg_scroll))
        surface.blit(self.bg_images[next_bg_index], (0, self.bg_scroll - SCREEN_HEIGHT))

        if portal_rect and self.portal_image:
            surface.blit(self.portal_image, portal_rect)

        for b in blocks:
            size = b["size"]
            bx = int(b["x"])
            by = int(b["y"])

            if self.meteor_small and self.meteor_medium and self.meteor_large:
                boundary_small = 40 * MIN_SCALE
                boundary_medium = 50 * MIN_SCALE

                if size < boundary_small:
                    img = self.meteor_small
                elif size < boundary_medium:
                    img = self.meteor_medium
                else:
                    img = self.meteor_large
                surface.blit(pygame.transform.scale(img, (size, size)), (bx, by))
            else:
                pygame.draw.rect(surface, WHITE, (bx, by, size, size))

            if b["splitter"] and not b["split_done"]:
                radius = int((size // 2) + (8 * MIN_SCALE))
                pygame.draw.circle(surface, YELLOW, (bx + size // 2, by + size // 2), max(1, radius), 3)

        if immunity == 0 or (immunity // 5) % 2 == 0:
            if self.player_image:
                surface.blit(self.player_image, self.player_image.get_rect(center=(int(px), int(py))))
            else:
                pygame.draw.circle(surface, GAME_BLUE, (int(px), int(py)), self.player_radius)

        score_x = SCREEN_WIDTH - max(1, int(200 * MIN_SCALE))
        score_y = max(0, int(20 * MIN_SCALE))
        surface.blit(FONT_SCORE.render(f"Score: {score // 10}", True, WHITE), (score_x, score_y))

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
        level_side = False

        while True:
            clock.tick(60)

            if immunity_timer > 0:
                immunity_timer -= 1

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return GameState.QUIT
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return GameState.TITLE

            portal1 = ((score // 10) >= 250 and not level_flipped)
            portal2 = ((score // 10) >= 500 and level_flipped and not level_side)
            portal_active = portal1 or portal2

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
                player_vx += input_x * self.player_accel
            else:
                player_vx *= self.player_friction

            if input_y != 0:
                player_vy += input_y * self.player_accel
            else:
                player_vy *= self.player_friction

            speed = math.sqrt(player_vx * player_vx + player_vy * player_vy)
            if speed > self.player_max_speed:
                scale = self.player_max_speed / speed
                player_vx *= scale
                player_vy *= scale

            if abs(player_vx) < 0.1:
                player_vx = 0.0
            if abs(player_vy) < 0.1:
                player_vy = 0.0

            x += player_vx
            y += player_vy

            score += 1

            if not level_flipped:
                fall_speed = min(self.start_speed + (score * self.speed_increase), self.max_fall_speed)
                level_mode = "down"
            elif level_flipped and not level_side:
                fall_speed = max(-self.start_speed - (score * self.speed_increase), -self.max_fall_speed)
                level_mode = "up"
            else:
                fall_speed = max(-self.start_speed - (score * self.speed_increase), -self.max_fall_speed)
                level_mode = "side"

            self.update_blocks(blocks, fall_speed, score, level_mode)

            x = max(self.player_radius, min(SCREEN_WIDTH - self.player_radius, x))
            y = max(self.player_radius, min(SCREEN_HEIGHT - self.player_radius, y))

            player_rect = pygame.Rect(int(x) - self.player_radius, int(y) - self.player_radius, self.player_radius * 2, self.player_radius * 2)

            portal_rect = None
            p_w = max(1, int(200 * MIN_SCALE))
            p_h = max(1, int(40 * MIN_SCALE))

            if portal1:
                portal_rect = pygame.Rect(int(CENTER_X - (p_w // 2)), int(20 * MIN_SCALE), p_w, p_h)
            elif portal2:
                portal_rect = pygame.Rect(int(CENTER_X - (p_w // 2)), SCREEN_HEIGHT - int(40 * MIN_SCALE), p_w, p_h)

            if portal_rect:
                dx, dy = portal_rect.centerx - x, portal_rect.centery - y
                x += dx * 0.05
                y += dy * 0.05
                player_rect.center = (int(x), int(y))

                if player_rect.colliderect(portal_rect):
                    if not level_flipped:
                        level_flipped = True
                        x, y = CENTER_X, int(100 * MIN_SCALE)
                        blocks = self.create_blocks("up")
                    else:
                        level_side = True
                        x, y = int(100 * MIN_SCALE), CENTER_Y
                        blocks = self.create_blocks("side")
                    player_vx, player_vy = 0.0, 0.0
                    continue

            for block in blocks:
                b_rect = pygame.Rect(int(block["x"]), int(block["y"]), block["size"], block["size"])
                hitbox_margin = int(6 * MIN_SCALE)
                hitbox = b_rect.inflate(-hitbox_margin, -hitbox_margin)

                if player_rect.colliderect(hitbox) and immunity_timer == 0 and not portal_active:
                    lives -= 1
                    if lives > 0:
                        audio.play_sfx(audio_path.hit_sound, 0.5)
                        self.render_frame(screen, blocks, x, y, score, lives, 1, portal_rect, portal_active)
                        pygame.time.delay(300)
                        immunity_timer = 90
                    else:
                        self.game.last_score = score // 10
                        return GameState.GAMEOVER
                    break

            self.render_frame(screen, blocks, x, y, score, lives, immunity_timer, portal_rect, portal_active)

class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()

        self.controls = Controls()
        self.last_score = 0
        self.menu_background = None
        self.current_skin = "spaceshipp.png"

        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
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
        while True:
            if not pygame.mixer.music.get_busy():
                audio.play_music(audio_path.menu_music, 0.5)

            mouse_up = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return GameState.QUIT
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
