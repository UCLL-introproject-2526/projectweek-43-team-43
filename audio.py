import pygame

current_music = None

def play_music(track, volume):
    global current_music
    if current_music != track:
        pygame.mixer.music.stop()
        pygame.mixer.music.load(track)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(-1)
        current_music = track


