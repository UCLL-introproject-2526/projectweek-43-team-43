import pygame

current_music = None

def play_music(track, volume, loop):
    global current_music
    if current_music != track:
        pygame.mixer.music.stop()
        pygame.mixer.music.load(track)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(loop)
        current_music = track

def music_is_playing():
    return pygame.mixer.music.get_busy()

