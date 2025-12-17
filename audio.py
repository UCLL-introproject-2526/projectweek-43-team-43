import pygame

current_music = None
music_enabled = True
sfx_enabled = True

def play_music(track, volume, loop=-1):
    global current_music
    if not music_enabled: return
    if current_music != track:
        pygame.mixer.music.stop()
        pygame.mixer.music.load(track)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(loop)
        current_music = track

def toggle_music():
    global music_enabled, current_music
    music_enabled = not music_enabled
    if not music_enabled:
        pygame.mixer.music.stop()
        current_music = None
    return music_enabled

def play_sfx(track, volume):
    if sfx_enabled:
        sound = pygame.mixer.Sound(track)
        sound.set_volume(volume)
        sound.play()

def toggle_sfx():
    global sfx_enabled
    sfx_enabled = not sfx_enabled
    return sfx_enabled