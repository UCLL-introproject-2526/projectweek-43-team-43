
import os
import random
import sys
from enum import Enum

import pygame
import pygame.freetype
from pygame.sprite import Sprite, RenderUpdates

# --- INITIALISATIE ---
pygame.init()
try:
    pygame.mixer.init()
    MIXER_AVAILABLE = True
except pygame.error:
    # Audio device not available (still allow the game to run without sound)
    MIXER_AVAILABLE = False


# --- CONSTANTEN & INSTELLINGEN ---
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

PLAYER_RADIUS = 20
MOVEMENT_SPEED = 5

# Gameplay
FPS = 60
START_LIVES = 3
MAX_LIVES = 5
IMMUNITY_FRAMES = int(1.5 * FPS)  # 1.5s invincibility after hit

# Default/fallback (levels override these)
BLOCK_SIZE_RANGE_DEFAULT = (20, 60)

# Controls (can be changed in Controls menu)
KEY_LEFT = pygame.K_LEFT
KEY_RIGHT = pygame.K_RIGHT
KEY_UP = pygame.K_UP
KEY_DOWN = pygame.K_DOWN

LAST_SCORE = 0
MENU_BACKGROUND = None

FONT_SCORE = pygame.font.SysFont("Arial", 30, bold=True)
FONT_SMALL = pygame.font.SysFont("Arial", 22, bold=True)
FONT_LEVEL = pygame.font.SysFont("Arial", 44, bold=True)


# --- AUDIO (self-contained: no external audio.py / audio_path.py needed) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()

MENU_MUSIC_FILE = "menu_music.mp3"
GAMEPLAY_MUSIC_FILE = "gameplay_music.mp3"
GAMEOVER_MUSIC_FILE = "gameover_music.mp3"
HIT_SFX_FILE = "hit_sound.mp3"
HEAL_SFX_FILE = "heal_sound.mp3"


class AudioManager:
    def __init__(self, base_dir: str, mixer_available: bool):
        self.base_dir = base_dir
        self.mixer_available = mixer_available

        self.music_enabled = True
        self.sfx_enabled = True

        self._desired_music = None  # filename (not full path)
        self._desired_music_volume = 0.5
        self._desired_music_loop = -1
        self._currently_loaded_music = None  # filename

        self._sfx = {}  # name -> pygame.mixer.Sound | None
        self._sfx_base_volume = 0.7

    def _resolve(self, filename: str) -> str:
        return os.path.join(self.base_dir, filename)

    def load_sfx(self, name: str, filename: str, volume: float = 1.0) -> None:
        if not self.mixer_available:
            self._sfx[name] = None
            return
        try:
            snd = pygame.mixer.Sound(self._resolve(filename))
            snd.set_volume(max(0.0, min(1.0, volume * self._sfx_base_volume)))
            self._sfx[name] = snd
        except Exception:
            self._sfx[name] = None

    def play_sfx(self, name: str) -> None:
        if not self.mixer_available or not self.sfx_enabled:
            return
        snd = self._sfx.get(name)
        if snd:
            snd.play()

    def play_music(self, filename: str, volume: float = 0.5, loop: int = -1) -> None:
        # Save as desired music so toggling music back ON can resume it.
        self._desired_music = filename
        self._desired_music_volume = volume
        self._desired_music_loop = loop

        if not self.mixer_available:
            return

        if not self.music_enabled:
            pygame.mixer.music.stop()
            return

        # Avoid reloading if the same track is already playing
        if self._currently_loaded_music == filename and pygame.mixer.music.get_busy():
            pygame.mixer.music.set_volume(volume)
            return

        try:
            pygame.mixer.music.load(self._resolve(filename))
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(loop)
            self._currently_loaded_music = filename
        except Exception:
            self._currently_loaded_music = None

    def apply_music_state(self) -> None:
        """Call after toggling music_enabled."""
        if not self.mixer_available:
            return
        if not self.music_enabled:
            pygame.mixer.music.stop()
            return
        if self._desired_music:
            self.play_music(self._desired_music, self._desired_music_volume, self._desired_music_loop)


AUDIO = AudioManager(BASE_DIR, MIXER_AVAILABLE)
AUDIO.load_sfx("hit", HIT_SFX_FILE, volume=1.0)
AUDIO.load_sfx("heal", HEAL_SFX_FILE, volume=0.9)


# --- GAME STATE ---
class GameState(Enum):
    QUIT = -1
    TITLE = 0
    PLAYING = 1
    GAMEOVER = 2
    OPTIONS = 3
    VIDEO_SETTINGS = 4
    SOUND = 5
    CONTROLS = 6


# --- LEVELS ---
# Score in UI = current_score // 10, so "min_score" is in visible score points.
LEVELS = [
    {
        "name": "LEVEL 1",
        "min_score": 0,
        "base_blocks": 10,
        "max_blocks": 14,
        "extra_every": 120,  # add 1 block every X visible score points (within this level)
        "size_range": (20, 60),
        "start_speed": 3.0,
        "speed_increase": 0.0020,
        "max_speed": 8.0,
        "vx_range": (0.0, 0.0),  # no drift
        "fast_chance": 0.00,
        "fast_mul": 1.0,
        "heal_timer_range": (8 * FPS, 14 * FPS),
    },
    {
        "name": "LEVEL 2",
        "min_score": 150,
        "base_blocks": 12,
        "max_blocks": 16,
        "extra_every": 110,
        "size_range": (22, 62),
        "start_speed": 3.6,
        "speed_increase": 0.0023,
        "max_speed": 9.5,
        "vx_range": (0.0, 0.0),
        "fast_chance": 0.15,  # some meteors are faster
        "fast_mul": 1.6,
        "heal_timer_range": (8 * FPS, 13 * FPS),
    },
    {
        "name": "LEVEL 3",
        "min_score": 350,
        "base_blocks": 14,
        "max_blocks": 18,
        "extra_every": 95,
        "size_range": (22, 65),
        "start_speed": 4.2,
        "speed_increase": 0.0027,
        "max_speed": 11.0,
        "vx_range": (-1.0, 1.0),  # horizontal drift
        "fast_chance": 0.25,
        "fast_mul": 1.7,
        "heal_timer_range": (7 * FPS, 12 * FPS),
    },
    {
        "name": "LEVEL 4",
        "min_score": 600,
        "base_blocks": 16,
        "max_blocks": 22,
        "extra_every": 80,
        "size_range": (24, 70),
        "start_speed": 5.0,
        "speed_increase": 0.0031,
        "max_speed": 12.0,
        "vx_range": (-1.7, 1.7),
        "fast_chance": 0.35,
        "fast_mul": 1.9,
        "heal_timer_range": (7 * FPS, 11 * FPS),
    },
]


# --- HULPFUNCTIES ---
def create_surface_with_text(text, font_size, text_rgb):
    font = pygame.freetype.SysFont("Courier", font_size, bold=True)
    surface, _ = font.render(text=text, fgcolor=text_rgb, bgcolor=None)
    return surface.convert_alpha()


def key_is_taken(new_key):
    return new_key in [KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN]


def get_level_for_visible_score(visible_score: int):
    idx = 0
    for i, cfg in enumerate(LEVELS):
        if visible_score >= cfg["min_score"]:
            idx = i
    return idx, LEVELS[idx]


def spawn_block(level_cfg):
    size_min, size_max = level_cfg.get("size_range", BLOCK_SIZE_RANGE_DEFAULT)
    size = random.randint(size_min, size_max)
    x = random.randint(0, SCREEN_WIDTH - size)
    y = random.randint(-SCREEN_HEIGHT, 0)

    vx_min, vx_max = level_cfg.get("vx_range", (0.0, 0.0))
    vx = random.uniform(vx_min, vx_max)
    # avoid tiny drift that looks like jitter
    if abs(vx) < 0.20:
        vx = 0.0

    fast_chance = float(level_cfg.get("fast_chance", 0.0))
    fast_mul = float(level_cfg.get("fast_mul", 1.0))
    speed_mul = fast_mul if random.random() < fast_chance else 1.0

    # block = [x, y, size, vx, speed_mul]
    return [float(x), float(y), int(size), float(vx), float(speed_mul)]


def apply_level_to_existing_blocks(blocks, level_cfg):
    """When level changes, refresh vx + fast/slow assignment so the new mechanics are visible immediately."""
    for b in blocks:
        vx_min, vx_max = level_cfg.get("vx_range", (0.0, 0.0))
        vx = random.uniform(vx_min, vx_max)
        if abs(vx) < 0.20:
            vx = 0.0
        b[3] = float(vx)

        fast_chance = float(level_cfg.get("fast_chance", 0.0))
        fast_mul = float(level_cfg.get("fast_mul", 1.0))
        b[4] = float(fast_mul if random.random() < fast_chance else 1.0)


def update_blocks(blocks, fall_speed, level_cfg, visible_score):
    # movement + respawn
    for b in blocks:
        b[1] += fall_speed * b[4]
        b[0] += b[3]

        # bounce from sides if drifting
        if b[0] < 0:
            b[0] = 0.0
            b[3] = abs(b[3])
        elif b[0] > SCREEN_WIDTH - b[2]:
            b[0] = float(SCREEN_WIDTH - b[2])
            b[3] = -abs(b[3])

        if b[1] > SCREEN_HEIGHT:
            nb = spawn_block(level_cfg)
            # keep some spacing
            nb[1] = float(random.randint(-180, -30))
            b[:] = nb

    # target amount of blocks grows within the level
    progress = max(0, visible_score - int(level_cfg["min_score"]))
    extra_every = int(level_cfg.get("extra_every", 999999))
    base_blocks = int(level_cfg.get("base_blocks", 10))
    max_blocks = int(level_cfg.get("max_blocks", base_blocks))

    target = base_blocks
    if extra_every > 0:
        target += progress // extra_every
    target = min(target, max_blocks)

    while len(blocks) < target:
        nb = spawn_block(level_cfg)
        nb[1] = float(random.randint(-220, -40))
        blocks.append(nb)

    # (optional) trim if ever needed
    if len(blocks) > max_blocks:
        del blocks[max_blocks:]


def spawn_heal_pickup():
    # pickup = [x, y, size]
    size = 26
    x = random.randint(0, SCREEN_WIDTH - size)
    y = random.randint(-260, -60)
    return [float(x), float(y), int(size)]


def update_heal_pickups(heals, fall_speed):
    for h in heals:
        h[1] += fall_speed * 0.85 + 1.3
    heals[:] = [h for h in heals if h[1] <= SCREEN_HEIGHT + 40]


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
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                return event.key


def game_loop(screen, buttons):
    clock = pygame.time.Clock()
    while True:
        clock.tick(FPS)

        # Wanneer een one-shot track afloopt (bv. gameover), terug naar menu-muziek
        if MIXER_AVAILABLE and AUDIO.music_enabled and not pygame.mixer.music.get_busy():
            AUDIO.play_music(MENU_MUSIC_FILE, 0.5, loop=-1)

        mouse_up = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return GameState.QUIT
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                mouse_up = True

        if MENU_BACKGROUND:
            screen.blit(MENU_BACKGROUND, (0, 0))
        else:
            screen.fill(BLUE)

        for button in buttons:
            ui_action = button.update(pygame.mouse.get_pos(), mouse_up)
            if ui_action is not None:
                return ui_action
            button.draw(screen)

        pygame.display.flip()


# --- GAMEPLAY FUNCTIES ---
def render_frame(
    surface,
    blocks,
    heals,
    player_x,
    player_y,
    current_score,
    heart_img,
    pickup_img,
    current_lives,
    max_lives,
    immunity_timer,
    background_img,
    img_small,
    img_medium,
    img_large,
    player_image,
    level_idx,
    level_banner_timer,
):
    surface.fill(BLACK)
    if background_img:
        surface.blit(background_img, (0, 0))

    # Blocks / Meteors
    for b in blocks:
        x_pos, y_pos, size = int(b[0]), int(b[1]), int(b[2])
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

    # Heal pickups
    for h in heals:
        hx, hy, hs = int(h[0]), int(h[1]), int(h[2])
        if pickup_img:
            surface.blit(pickup_img, (hx, hy))
        else:
            pygame.draw.rect(surface, GREEN, (hx, hy, hs, hs), border_radius=6)

    # Player (blink if immune)
    if immunity_timer == 0 or (immunity_timer // 5) % 2 == 0:
        if player_image:
            img_rect = player_image.get_rect(center=(int(player_x), int(player_y)))
            surface.blit(player_image, img_rect)
        else:
            pygame.draw.circle(surface, GAME_BLUE, (int(player_x), int(player_y)), PLAYER_RADIUS)

    # HUD: score + level
    score_display = "Score: " + str(current_score // 10)
    score_surface = FONT_SCORE.render(score_display, True, WHITE)
    surface.blit(score_surface, (SCREEN_WIDTH - 220, 16))

    level_surface = FONT_SMALL.render(f"Level: {level_idx + 1}", True, WHITE)
    surface.blit(level_surface, (SCREEN_WIDTH - 220, 50))

    # HUD: lives
    if heart_img:
        for i in range(current_lives):
            surface.blit(heart_img, (20 + (i * 35), 20))
        # optional: show max capacity as outlines (simple text)
        if current_lives < max_lives:
            txt = FONT_SMALL.render(f"/ {max_lives}", True, WHITE)
            surface.blit(txt, (20 + (max_lives * 35), 24))
    else:
        lives_surface = FONT_SCORE.render(f"Lives: {current_lives}/{max_lives}", True, RED)
        surface.blit(lives_surface, (20, 20))

    # Level banner
    if level_banner_timer > 0:
        name = LEVELS[level_idx]["name"]
        banner = FONT_LEVEL.render(name, True, YELLOW)
        rect = banner.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 10))
        surface.blit(banner, rect)

    pygame.display.flip()


def play_level(screen):
    global LAST_SCORE

    AUDIO.play_music(GAMEPLAY_MUSIC_FILE, 0.4, loop=-1)

    # Try to load images; fallback to shapes if missing
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
        pickup_image = pygame.transform.scale(heart_image, (24, 24))
    except Exception:
        background_image = meteor_small = meteor_medium = meteor_large = heart_image = player_image = pickup_image = None

    # Player
    x, y = SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100
    x_velocity = y_velocity = 0

    # Level init
    score = 0
    visible_score = 0
    level_idx, level_cfg = get_level_for_visible_score(visible_score)
    level_banner_timer = int(1.2 * FPS)

    # Blocks
    blocks = [spawn_block(level_cfg) for _ in range(int(level_cfg["base_blocks"]))]

    # Difficulty
    fall_speed = float(level_cfg["start_speed"])

    # Lives / hit / immunity
    lives = START_LIVES
    immunity_timer = 0

    # Heal pickups
    heals = []
    heal_timer = random.randint(*level_cfg["heal_timer_range"])

    clock = pygame.time.Clock()

    while True:
        clock.tick(FPS)
        if immunity_timer > 0:
            immunity_timer -= 1
        if level_banner_timer > 0:
            level_banner_timer -= 1

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

        # Update movement
        x += x_velocity
        y += y_velocity

        # Score / level
        score += 1
        visible_score = score // 10
        new_level_idx, new_level_cfg = get_level_for_visible_score(visible_score)
        if new_level_idx != level_idx:
            level_idx, level_cfg = new_level_idx, new_level_cfg
            level_banner_timer = int(1.2 * FPS)

            # Make sure level mechanics apply immediately
            apply_level_to_existing_blocks(blocks, level_cfg)

            # Don’t drop speed when leveling up
            fall_speed = max(fall_speed, float(level_cfg["start_speed"]))

            # Reset heal timer for new level pacing
            heal_timer = min(heal_timer, random.randint(*level_cfg["heal_timer_range"]))

        # Difficulty curve within level
        fall_speed = max(fall_speed, float(level_cfg["start_speed"]))
        fall_speed = min(fall_speed + float(level_cfg["speed_increase"]), float(level_cfg["max_speed"]))

        # Update blocks + pickups
        update_blocks(blocks, fall_speed, level_cfg, visible_score)

        # Heal spawn logic (only if you are not already at max lives)
        if lives < MAX_LIVES:
            heal_timer -= 1
            if heal_timer <= 0 and len(heals) < 2:
                heals.append(spawn_heal_pickup())
                heal_timer = random.randint(*level_cfg["heal_timer_range"])
        else:
            # postpone while full
            heal_timer = min(heal_timer, 2 * FPS)

        update_heal_pickups(heals, fall_speed)

        # Clamp player
        x = max(PLAYER_RADIUS, min(x, SCREEN_WIDTH - PLAYER_RADIUS))
        y = max(PLAYER_RADIUS, min(y, SCREEN_HEIGHT - PLAYER_RADIUS))

        player_rect = pygame.Rect(int(x - PLAYER_RADIUS), int(y - PLAYER_RADIUS), PLAYER_RADIUS * 2, PLAYER_RADIUS * 2)

        # Collisions with blocks
        if immunity_timer == 0:
            for b in blocks:
                block_rect = pygame.Rect(int(b[0]), int(b[1]), int(b[2]), int(b[2]))
                if player_rect.colliderect(block_rect):
                    lives -= 1
                    AUDIO.play_sfx("hit")
                    render_frame(
                        screen,
                        blocks,
                        heals,
                        x,
                        y,
                        score,
                        heart_image,
                        pickup_image,
                        lives,
                        MAX_LIVES,
                        1,
                        background_image,
                        meteor_small,
                        meteor_medium,
                        meteor_large,
                        player_image,
                        level_idx,
                        level_banner_timer,
                    )
                    pygame.time.delay(300)
                    immunity_timer = IMMUNITY_FRAMES

                    if lives <= 0:
                        LAST_SCORE = score // 10
                        return GameState.GAMEOVER
                    break

        # Collisions with heals
        if heals:
            for h in heals[:]:
                heal_rect = pygame.Rect(int(h[0]), int(h[1]), int(h[2]), int(h[2]))
                if player_rect.colliderect(heal_rect):
                    heals.remove(h)
                    if lives < MAX_LIVES:
                        lives += 1
                        AUDIO.play_sfx("heal")
                    break

        render_frame(
            screen,
            blocks,
            heals,
            x,
            y,
            score,
            heart_image,
            pickup_image,
            lives,
            MAX_LIVES,
            immunity_timer,
            background_image,
            meteor_small,
            meteor_medium,
            meteor_large,
            player_image,
            level_idx,
            level_banner_timer,
        )


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
    clock = pygame.time.Clock()

    while True:
        clock.tick(FPS)
        mouse_up = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return GameState.QUIT
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                mouse_up = True

        if MENU_BACKGROUND:
            screen.blit(MENU_BACKGROUND, (0, 0))
        else:
            screen.fill(BLUE)

        for button in buttons:
            ui_action = button.update(pygame.mouse.get_pos(), mouse_up)
            if ui_action is not None:
                if isinstance(ui_action, GameState):
                    return ui_action

                button.set_text("PRESS KEY...", 25, YELLOW)
                button.draw(screen)
                pygame.display.flip()
                new = wait_for_key()
                if new is None:
                    return GameState.QUIT

                if not key_is_taken(new):
                    if ui_action == "CHANGE_LEFT":
                        KEY_LEFT = new
                    elif ui_action == "CHANGE_RIGHT":
                        KEY_RIGHT = new
                    elif ui_action == "CHANGE_DOWN":
                        KEY_DOWN = new
                    elif ui_action == "CHANGE_UP":
                        KEY_UP = new
                else:
                    show_taken_error(button, screen)

                # Update texts
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
        return "Music: ON" if AUDIO.music_enabled else "Music: OFF"

    def get_sfx_text():
        return "Effects: ON" if AUDIO.sfx_enabled else "Effects: OFF"

    # Ensure desired track is menu music while in menu screens
    AUDIO.play_music(MENU_MUSIC_FILE, 0.5, loop=-1)

    TITLE = UIElement((CENTER_X, 100), "SOUNDS", 50, WHITE)
    music_btn = UIElement((CENTER_X, 300), get_music_text(), 30, WHITE, "TOGGLE_MUSIC")
    effects_btn = UIElement((CENTER_X, 400), get_sfx_text(), 30, WHITE, "TOGGLE_SFX")
    back_btn = UIElement((CENTER_X, 600), "Back to Options", 30, WHITE, GameState.OPTIONS)

    buttons = RenderUpdates(TITLE, music_btn, effects_btn, back_btn)
    clock = pygame.time.Clock()

    while True:
        clock.tick(FPS)
        mouse_up = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return GameState.QUIT
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                mouse_up = True

        if MENU_BACKGROUND:
            screen.blit(MENU_BACKGROUND, (0, 0))
        else:
            screen.fill(BLUE)

        for button in buttons:
            ui_action = button.update(pygame.mouse.get_pos(), mouse_up)

            if ui_action == "TOGGLE_MUSIC":
                AUDIO.music_enabled = not AUDIO.music_enabled
                AUDIO.apply_music_state()
                music_btn.set_text(get_music_text(), 30, WHITE)

            elif ui_action == "TOGGLE_SFX":
                AUDIO.sfx_enabled = not AUDIO.sfx_enabled
                effects_btn.set_text(get_sfx_text(), 30, WHITE)

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
    except Exception:
        MENU_BACKGROUND = None

    game_state = GameState.TITLE

    while True:
        if game_state == GameState.TITLE:
            AUDIO.play_music(MENU_MUSIC_FILE, 0.5, loop=-1)
            game_state = title_screen(screen)

        elif game_state == GameState.PLAYING:
            game_state = play_level(screen)

        elif game_state == GameState.GAMEOVER:
            # Speel de clip 1 keer af, daarna schakelt menu-loop terug naar menu-muziek
            AUDIO.play_music(GAMEOVER_MUSIC_FILE, 0.5, loop=0)
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
