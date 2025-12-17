import pygame
import random
import sys
import math
import json
import os
from enum import Enum

# ==============================================================================
# 1. CONFIGURATIE & CONSTANTEN
# ==============================================================================
SCHERM_BREEDTE = 1024
SCHERM_HOOGTE = 768
FPS = 60
TITEL = "Neon Void: Architect Edition"

# Kleurenpalet (Solarized / Neon style)
C_ACHTERGROND = (10, 15, 20)
C_WIT = (240, 240, 240)
C_ZWART = (0, 0, 0)
C_SPELER = (0, 255, 255)       # Cyan
C_VIJAND_BASIS = (255, 50, 50) # Rood
C_VIJAND_VOLG = (255, 165, 0)  # Oranje
C_VIJAND_SINE = (255, 0, 255)  # Paars
C_POWERUP_SCHILD = (50, 255, 50)
C_POWERUP_NUKE = (255, 255, 0)
C_UI_HOVER = (50, 50, 70)
C_UI_KNOP = (30, 30, 40)

# Bestandslocaties
INSTELLINGEN_BESTAND = "settings.json"

# Initialisatie
pygame.init()
pygame.font.init()

# Fonts inladen (fallback naar systeem font als bestand niet bestaat)
FONT_KLEIN = pygame.font.SysFont("Consolas", 14)
FONT_NORMAAL = pygame.font.SysFont("Verdana", 20)
FONT_GROOT = pygame.font.SysFont("Verdana", 60, bold=True)

SCHERM = pygame.display.set_mode((SCHERM_BREEDTE, SCHERM_HOOGTE))
pygame.display.set_caption(TITEL)
KLOK = pygame.time.Clock()

# ==============================================================================
# 2. HULP KLASSEN (DATA MANAGEMENT)
# ==============================================================================

class DataManager:
    """Beheert het opslaan en laden van data (Highscores/Settings)"""
    @staticmethod
    def laad_data():
        standaard_data = {"highscore": 0, "volume": 0.5, "particles_aan": True}
        if not os.path.exists(INSTELLINGEN_BESTAND):
            return standaard_data
        try:
            with open(INSTELLINGEN_BESTAND, 'r') as f:
                return json.load(f)
        except:
            return standaard_data

    @staticmethod
    def sla_op(data):
        try:
            with open(INSTELLINGEN_BESTAND, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Fout bij opslaan: {e}")

class Vector2:
    """Simpele Vector klasse voor fijnere bewegingsberekeningen"""
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def afstand_tot(self, andere):
        return math.sqrt((self.x - andere.x)**2 + (self.y - andere.y)**2)
    
    def normaliseer(self):
        m = math.sqrt(self.x**2 + self.y**2)
        if m == 0: return Vector2(0, 0)
        return Vector2(self.x / m, self.y / m)

# ==============================================================================
# 3. UI SYSTEEM
# ==============================================================================

class Knop:
    def __init__(self, tekst, x, y, breedte, hoogte, actie_callback):
        self.rect = pygame.Rect(x, y, breedte, hoogte)
        self.tekst = tekst
        self.actie = actie_callback
        self.is_hovered = False

    def update(self, muis_pos):
        self.is_hovered = self.rect.collidepoint(muis_pos)

    def verwerk_klik(self, muis_pos):
        if self.rect.collidepoint(muis_pos) and self.actie:
            self.actie()

    def teken(self, oppervlak):
        kleur = C_UI_HOVER if self.is_hovered else C_UI_KNOP
        pygame.draw.rect(oppervlak, kleur, self.rect, border_radius=8)
        pygame.draw.rect(oppervlak, C_WIT, self.rect, 2, border_radius=8)
        
        tekst_surf = FONT_NORMAAL.render(self.tekst, True, C_WIT)
        tekst_rect = tekst_surf.get_rect(center=self.rect.center)
        oppervlak.blit(tekst_surf, tekst_rect)

# ==============================================================================
# 4. PARTICLE ENGINE
# ==============================================================================

class Deeltje:
    def __init__(self, x, y, kleur, snelheid, hoek, levensduur, zwaartekracht=0):
        self.x = x
        self.y = y
        self.kleur = list(kleur)
        self.hoek = math.radians(hoek)
        self.snelheid = snelheid
        self.vx = math.cos(self.hoek) * snelheid
        self.vy = math.sin(self.hoek) * snelheid
        self.levensduur = levensduur
        self.start_levensduur = levensduur
        self.zwaartekracht = zwaartekracht
        self.grootte = random.randint(2, 5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.zwaartekracht # Zwaartekracht effect
        self.levensduur -= 1
        self.grootte = max(0, self.grootte - 0.05) # Krimp effect

    def teken(self, oppervlak):
        if self.levensduur > 0:
            # Fade out effect (alpha simulatie door kleur donkerder te maken)
            factor = self.levensduur / self.start_levensduur
            huidige_kleur = (
                int(self.kleur[0] * factor),
                int(self.kleur[1] * factor),
                int(self.kleur[2] * factor)
            )
            pygame.draw.circle(oppervlak, huidige_kleur, (int(self.x), int(self.y)), int(self.grootte))

class ParticleSystem:
    def __init__(self):
        self.deeltjes = []

    def explosie(self, x, y, kleur, aantal=20):
        for _ in range(aantal):
            snelheid = random.uniform(2, 6)
            hoek = random.uniform(0, 360)
            levensduur = random.randint(30, 60)
            self.deeltjes.append(Deeltje(x, y, kleur, snelheid, hoek, levensduur, 0.1))

    def spoor(self, x, y, kleur):
        self.deeltjes.append(Deeltje(x, y, kleur, random.uniform(0.5, 2), random.uniform(80, 100), 20, 0.05))

    def update_en_teken(self, oppervlak):
        for p in self.deeltjes[:]:
            p.update()
            if p.levensduur <= 0:
                self.deeltjes.remove(p)
            else:
                p.teken(oppervlak)

# ==============================================================================
# 5. SPEL OBJECTEN (ENTITIES)
# ==============================================================================

class Speler:
    def __init__(self):
        self.breedte = 30
        self.hoogte = 30
        self.pos = Vector2(SCHERM_BREEDTE // 2, SCHERM_HOOGTE - 100)
        self.snelheid = 6
        self.kleur = C_SPELER
        self.rect = pygame.Rect(self.pos.x, self.pos.y, self.breedte, self.hoogte)
        self.levens = 3
        self.schild_actief = False
        self.schild_tijd = 0
        self.score = 0

    def beweeg(self, toetsen):
        dx, dy = 0, 0
        if toetsen[pygame.K_LEFT] or toetsen[pygame.K_a]: dx = -self.snelheid
        if toetsen[pygame.K_RIGHT] or toetsen[pygame.K_d]: dx = self.snelheid
        if toetsen[pygame.K_UP] or toetsen[pygame.K_w]: dy = -self.snelheid
        if toetsen[pygame.K_DOWN] or toetsen[pygame.K_s]: dy = self.snelheid

        # Speed boost check
        if self.snelheid > 6:
            self.snelheid -= 0.05 # Langzaam terug naar normaal

        self.pos.x = max(0, min(SCHERM_BREEDTE - self.breedte, self.pos.x + dx))
        self.pos.y = max(0, min(SCHERM_HOOGTE - self.hoogte, self.pos.y + dy))
        self.rect.topleft = (self.pos.x, self.pos.y)

        # Schild timer
        if self.schild_actief:
            self.schild_tijd -= 1
            if self.schild_tijd <= 0:
                self.schild_actief = False

    def teken(self, oppervlak):
        if self.schild_actief:
            pygame.draw.circle(oppervlak, C_POWERUP_SCHILD, self.rect.center, 25, 2)
        pygame.draw.rect(oppervlak, self.kleur, self.rect)
        # Oogjes
        pygame.draw.rect(oppervlak, C_ZWART, (self.pos.x + 5, self.pos.y + 5, 5, 5))
        pygame.draw.rect(oppervlak, C_ZWART, (self.pos.x + 20, self.pos.y + 5, 5, 5))

class VijandBasis:
    """Parent klasse voor alle vijanden"""
    def __init__(self):
        self.grootte = random.randint(20, 40)
        self.pos = Vector2(random.randint(0, SCHERM_BREEDTE - self.grootte), -50)
        self.rect = pygame.Rect(self.pos.x, self.pos.y, self.grootte, self.grootte)
        self.kleur = C_VIJAND_BASIS
        self.verwijder_mij = False
    
    def update(self, speler_pos):
        self.rect.topleft = (self.pos.x, self.pos.y)
        if self.pos.y > SCHERM_HOOGTE:
            self.verwijder_mij = True

    def teken(self, oppervlak):
        pygame.draw.rect(oppervlak, self.kleur, self.rect)

class VijandRecht(VijandBasis):
    """Valt gewoon naar beneden"""
    def update(self, speler_pos):
        self.pos.y += 5
        super().update(speler_pos)

class VijandVolger(VijandBasis):
    """Beweegt langzaam richting de speler"""
    def __init__(self):
        super().__init__()
        self.kleur = C_VIJAND_VOLG
        self.snelheid = 3

    def update(self, speler_pos):
        richting = Vector2(speler_pos.x - self.pos.x, speler_pos.y - self.pos.y).normaliseer()
        self.pos.x += richting.x * self.snelheid
        self.pos.y += 3 # Valt altijd naar beneden
        super().update(speler_pos)

class VijandSine(VijandBasis):
    """Beweegt in een sinusgolf"""
    def __init__(self):
        super().__init__()
        self.kleur = C_VIJAND_SINE
        self.start_x = self.pos.x
        self.hoek = 0

    def update(self, speler_pos):
        self.pos.y += 4
        self.hoek += 0.1
        self.pos.x = self.start_x + math.sin(self.hoek) * 100
        super().update(speler_pos)

class PowerUp:
    def __init__(self):
        self.type = random.choice(["SCHILD", "NUKE", "SPEED"])
        self.pos = Vector2(random.randint(50, SCHERM_BREEDTE - 50), -30)
        self.rect = pygame.Rect(self.pos.x, self.pos.y, 20, 20)
        self.verwijder_mij = False
    
    def update(self):
        self.pos.y += 3
        self.rect.topleft = (self.pos.x, self.pos.y)
        if self.pos.y > SCHERM_HOOGTE:
            self.verwijder_mij = True

    def teken(self, oppervlak):
        kleur = C_WIT
        if self.type == "SCHILD": kleur = C_POWERUP_SCHILD
        elif self.type == "NUKE": kleur = C_POWERUP_NUKE
        elif self.type == "SPEED": kleur = C_SPELER
        
        pygame.draw.circle(oppervlak, kleur, self.rect.center, 10)
        label = FONT_KLEIN.render(self.type[0], True, C_ZWART)
        oppervlak.blit(label, (self.rect.centerx - 4, self.rect.centery - 8))

# ==============================================================================
# 6. GAME STATES (STATE MACHINE)
# ==============================================================================

class GameState(Enum):
    MENU = 1
    SPELEN = 2
    PAUZE = 3
    GAMEOVER = 4

class GameEngine:
    def __init__(self):
        self.state = GameState.MENU
        self.data = DataManager.laad_data()
        self.particles = ParticleSystem()
        self.reset_game()
        self.maak_ui()

    def maak_ui(self):
        cx = SCHERM_BREEDTE // 2
        cy = SCHERM_HOOGTE // 2
        
        # Menu Knoppen
        self.btn_start = Knop("START SPEL", cx - 100, cy - 20, 200, 50, self.start_spel)
        self.btn_quit = Knop("AFSLUITEN", cx - 100, cy + 50, 200, 50, self.stop_spel)
        
        # Game Over Knoppen
        self.btn_restart = Knop("OPNIEUW", cx - 100, cy + 50, 200, 50, self.start_spel)
        self.btn_menu = Knop("HOOFDMENU", cx - 100, cy + 120, 200, 50, self.naar_menu)

    def reset_game(self):
        self.speler = Speler()
        self.vijanden = []
        self.powerups = []
        self.spawn_timer = 0
        self.powerup_timer = 0
        self.moeilijkheid = 1.0

    # --- State Transities ---
    def start_spel(self):
        self.reset_game()
        self.state = GameState.SPELEN

    def stop_spel(self):
        pygame.quit()
        sys.exit()

    def naar_menu(self):
        self.state = GameState.MENU

    # --- Logica per frame ---
    def verwerk_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.stop_spel()
            
            muis_pos = pygame.mouse.get_pos()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.state == GameState.MENU:
                    self.btn_start.verwerk_klik(muis_pos)
                    self.btn_quit.verwerk_klik(muis_pos)
                elif self.state == GameState.GAMEOVER:
                    self.btn_restart.verwerk_klik(muis_pos)
                    self.btn_menu.verwerk_klik(muis_pos)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p and self.state == GameState.SPELEN:
                    self.state = GameState.PAUZE
                elif event.key == pygame.K_p and self.state == GameState.PAUZE:
                    self.state = GameState.SPELEN
                elif event.key == pygame.K_ESCAPE and self.state == GameState.SPELEN:
                    self.state = GameState.MENU

    def update(self):
        muis_pos = pygame.mouse.get_pos()

        if self.state == GameState.MENU:
            self.btn_start.update(muis_pos)
            self.btn_quit.update(muis_pos)
            self.particles.update_en_teken(SCHERM) # Menu particles

        elif self.state == GameState.SPELEN:
            toetsen = pygame.key.get_pressed()
            self.speler.beweeg(toetsen)
            
            # Speler trail
            if random.random() < 0.3:
                self.particles.spoor(self.speler.pos.x + 15, self.speler.pos.y + 30, (0, 200, 200))

            # Spawnen
            self.spawn_mechaniek()

            # Updates entiteiten
            self.update_vijanden()
            self.update_powerups()
            
            # Score check
            self.speler.score += 1
            if self.speler.score % 500 == 0:
                self.moeilijkheid += 0.2

            if self.speler.levens <= 0:
                self.game_over_logic()

        elif self.state == GameState.GAMEOVER:
            self.btn_restart.update(muis_pos)
            self.btn_menu.update(muis_pos)

    def spawn_mechaniek(self):
        # Vijanden
        self.spawn_timer += 1
        drempel = max(20, 60 - int(self.moeilijkheid * 2))
        if self.spawn_timer > drempel:
            keuze = random.random()
            if keuze < 0.6: self.vijanden.append(VijandRecht())
            elif keuze < 0.8: self.vijanden.append(VijandVolger())
            else: self.vijanden.append(VijandSine())
            self.spawn_timer = 0
        
        # Powerups
        self.powerup_timer += 1
        if self.powerup_timer > 600: # Elke ~10 sec
            self.powerups.append(PowerUp())
            self.powerup_timer = 0

    def update_vijanden(self):
        speler_rect = self.speler.rect
        speler_pos = Vector2(self.speler.rect.x, self.speler.rect.y)
        
        for v in self.vijanden[:]:
            v.update(speler_pos)
            
            # Botsing
            if v.rect.colliderect(speler_rect):
                self.particles.explosie(v.pos.x, v.pos.y, v.kleur)
                self.vijanden.remove(v)
                
                if self.speler.schild_actief:
                    self.speler.schild_actief = False # Schild breekt
                    self.particles.explosie(self.speler.pos.x, self.speler.pos.y, C_POWERUP_SCHILD, 30)
                else:
                    self.speler.levens -= 1
                    self.particles.explosie(self.speler.pos.x, self.speler.pos.y, C_SPELER)
            
            elif v.verwijder_mij:
                self.vijanden.remove(v)

    def update_powerups(self):
        for p in self.powerups[:]:
            p.update()
            if p.rect.colliderect(self.speler.rect):
                if p.type == "SCHILD": 
                    self.speler.schild_actief = True
                    self.speler.schild_tijd = 600
                elif p.type == "SPEED": 
                    self.speler.snelheid = 12
                elif p.type == "NUKE":
                    for v in self.vijanden:
                        self.particles.explosie(v.pos.x, v.pos.y, v.kleur)
                    self.vijanden.clear()
                    self.speler.score += 500
                
                self.powerups.remove(p)
            elif p.verwijder_mij:
                self.powerups.remove(p)

    def game_over_logic(self):
        self.state = GameState.GAMEOVER
        if self.speler.score > self.data['highscore']:
            self.data['highscore'] = self.speler.score
            DataManager.sla_op(self.data)

    # --- Render ---
    def teken(self):
        SCHERM.fill(C_ACHTERGROND)
        
        # Achtergrond grid (Retro effect)
        for x in range(0, SCHERM_BREEDTE, 50):
            pygame.draw.line(SCHERM, (20, 25, 30), (x, 0), (x, SCHERM_HOOGTE))
        for y in range(0, SCHERM_HOOGTE, 50):
            pygame.draw.line(SCHERM, (20, 25, 30), (0, y), (SCHERM_BREEDTE, y))

        if self.state == GameState.MENU:
            # Titel animatie
            offset = math.sin(pygame.time.get_ticks() / 500) * 10
            titel = FONT_GROOT.render("NEON VOID", True, C_SPELER)
            subtitel = FONT_NORMAAL.render(f"Highscore: {self.data['highscore']}", True, C_WIT)
            
            SCHERM.blit(titel, (SCHERM_BREEDTE//2 - titel.get_width()//2, 150 + offset))
            SCHERM.blit(subtitel, (SCHERM_BREEDTE//2 - subtitel.get_width()//2, 230))
            
            self.btn_start.teken(SCHERM)
            self.btn_quit.teken(SCHERM)

        elif self.state == GameState.SPELEN:
            for p in self.powerups: p.teken(SCHERM)
            for v in self.vijanden: v.teken(SCHERM)
            self.speler.teken(SCHERM)
            self.particles.update_en_teken(SCHERM)
            
            # HUD
            score_txt = FONT_NORMAAL.render(f"Score: {self.speler.score}", True, C_WIT)
            levens_txt = FONT_NORMAAL.render(f"Levens: {self.speler.levens}", True, C_VIJAND_BASIS)
            SCHERM.blit(score_txt, (10, 10))
            SCHERM.blit(levens_txt, (10, 40))

        elif self.state == GameState.PAUZE:
            pauze_txt = FONT_GROOT.render("PAUZE", True, C_WIT)
            SCHERM.blit(pauze_txt, (SCHERM_BREEDTE//2 - pauze_txt.get_width()//2, SCHERM_HOOGTE//2 - 50))

        elif self.state == GameState.GAMEOVER:
            # We blijven de game tekenen op de achtergrond, maar donkerder
            overlay = pygame.Surface((SCHERM_BREEDTE, SCHERM_HOOGTE))
            overlay.set_alpha(180)
            overlay.fill((0,0,0))
            SCHERM.blit(overlay, (0,0))
            
            txt = FONT_GROOT.render("GAME OVER", True, C_VIJAND_BASIS)
            score = FONT_NORMAAL.render(f"Eindscore: {self.speler.score}", True, C_WIT)
            SCHERM.blit(txt, (SCHERM_BREEDTE//2 - txt.get_width()//2, 150))
            SCHERM.blit(score, (SCHERM_BREEDTE//2 - score.get_width()//2, 220))
            
            self.btn_restart.teken(SCHERM)
            self.btn_menu.teken(SCHERM)

        pygame.display.flip()

# ==============================================================================
# 7. MAIN LOOP
# ==============================================================================

if __name__ == "__main__":
    game = GameEngine()
    
    while True:
        KLOK.tick(FPS)
        game.verwerk_input()
        game.update()
        game.teken()