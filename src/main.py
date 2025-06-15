import pygame
import random
import math
import json
import os
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional
import sys

# Initialize Pygame
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# Game Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 1366, 768
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 100, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
LIGHT_BLUE = (173, 216, 230)
DARK_BLUE = (0, 0, 139)
GOLD = (255, 215, 0)

class GameState(Enum):
    MENU = 1
    PLAYING = 2
    PAUSED = 3
    GAME_OVER = 4
    SETTINGS = 5
    ACHIEVEMENTS = 6

class GameMode(Enum):
    CLASSIC = 1
    ENDLESS = 2
    TIME_ATTACK = 3
    SURVIVAL = 4

class PowerUpType(Enum):
    SHIELD = 1
    SPEED_BOOST = 2
    SLOW_MOTION = 3
    DOUBLE_SCORE = 4
    INVINCIBILITY = 5

@dataclass
class Achievement:
    name: str
    description: str
    unlocked: bool = False
    progress: int = 0
    target: int = 1

class GameSettings:
    def __init__(self):
        self.sound_enabled = True
        self.music_enabled = True
        self.volume = 0.7
        self.difficulty = 1  # 1-3
        self.controls = {'jump': pygame.K_SPACE, 'pause': pygame.K_p}
        
    def save(self):
        data = {
            'sound_enabled': self.sound_enabled,
            'music_enabled': self.music_enabled,
            'volume': self.volume,
            'difficulty': self.difficulty
        }
        try:
            with open('settings.json', 'w') as f:
                json.dump(data, f)
        except:
            pass
    
    def load(self):
        try:
            with open('settings.json', 'r') as f:
                data = json.load(f)
                self.sound_enabled = data.get('sound_enabled', True)
                self.music_enabled = data.get('music_enabled', True)
                self.volume = data.get('volume', 0.7)
                self.difficulty = data.get('difficulty', 1)
        except:
            pass

class ParticleSystem:
    def __init__(self):
        self.particles = []
    
    def add_explosion(self, x: int, y: int, color: Tuple[int, int, int] = ORANGE):
        for _ in range(15):
            vel_x = random.uniform(-8, 8)
            vel_y = random.uniform(-8, 8)
            life = random.uniform(20, 40)
            self.particles.append({
                'x': x, 'y': y, 'vel_x': vel_x, 'vel_y': vel_y,
                'life': life, 'max_life': life, 'color': color
            })
    
    def add_trail(self, x: int, y: int, color: Tuple[int, int, int] = WHITE):
        for _ in range(3):
            vel_x = random.uniform(-2, 2)
            vel_y = random.uniform(-2, 2)
            life = random.uniform(10, 20)
            self.particles.append({
                'x': x, 'y': y, 'vel_x': vel_x, 'vel_y': vel_y,
                'life': life, 'max_life': life, 'color': color
            })
    
    def update(self):
        for particle in self.particles[:]:
            particle['x'] += particle['vel_x']
            particle['y'] += particle['vel_y']
            particle['life'] -= 1
            particle['vel_y'] += 0.2  # gravity
            
            if particle['life'] <= 0:
                self.particles.remove(particle)
    
    def draw(self, screen):
        for particle in self.particles:
            alpha = int(255 * (particle['life'] / particle['max_life']))
            size = max(1, int(4 * (particle['life'] / particle['max_life'])))
            color = (*particle['color'], alpha)
            
            # Create a surface with per-pixel alpha
            surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, color, (size, size), size)
            screen.blit(surf, (int(particle['x']) - size, int(particle['y']) - size))

class PowerUp:
    def __init__(self, x: int, y: int, power_type: PowerUpType):
        self.x = x
        self.y = y
        self.type = power_type
        self.width = 40
        self.height = 40
        self.speed = 5
        self.color = self._get_color()
        self.bounce_offset = 0
        
    def _get_color(self) -> Tuple[int, int, int]:
        colors = {
            PowerUpType.SHIELD: BLUE,
            PowerUpType.SPEED_BOOST: GREEN,
            PowerUpType.SLOW_MOTION: PURPLE,
            PowerUpType.DOUBLE_SCORE: GOLD,
            PowerUpType.INVINCIBILITY: RED
        }
        return colors.get(self.type, WHITE)
    
    def update(self):
        self.x -= self.speed
        self.bounce_offset += 0.2
    
    def draw(self, screen):
        bounce_y = self.y + math.sin(self.bounce_offset) * 5
        pygame.draw.circle(screen, self.color, (int(self.x), int(bounce_y)), self.width // 2)
        pygame.draw.circle(screen, WHITE, (int(self.x), int(bounce_y)), self.width // 2, 3)
        
        # Draw icon based on type
        if self.type == PowerUpType.SHIELD:
            pygame.draw.polygon(screen, WHITE, [
                (self.x - 10, bounce_y + 5),
                (self.x, bounce_y - 10),
                (self.x + 10, bounce_y + 5),
                (self.x, bounce_y + 10)
            ])
    
    def get_rect(self):
        return pygame.Rect(self.x - self.width//2, self.y - self.height//2, self.width, self.height)
    
    def is_off_screen(self) -> bool:
        return self.x < -self.width

class Plane:
    def __init__(self):
        self.x = 100
        self.y = SCREEN_HEIGHT - 100
        self.width = 60
        self.height = 30
        self.velocity_y = 0
        self.jump_power = -15
        self.gravity = 0.8
        self.max_fall_speed = 10
        self.is_jumping = False
        self.trail_timer = 0
        
        # Power-up effects
        self.shield_time = 0
        self.speed_boost_time = 0
        self.slow_motion_time = 0
        self.double_score_time = 0
        self.invincibility_time = 0
        
        # Animation
        self.rotation = 0
        self.base_color = BLUE
        
    def jump(self):
        if not self.is_jumping or self.velocity_y > -5:
            self.velocity_y = self.jump_power
            self.is_jumping = True
    
    def update(self, particle_system: ParticleSystem):
        # Apply gravity
        self.velocity_y += self.gravity
        self.velocity_y = min(self.velocity_y, self.max_fall_speed)
        
        # Update position
        self.y += self.velocity_y
        
        # Ground collision
        if self.y >= SCREEN_HEIGHT - 100:
            self.y = SCREEN_HEIGHT - 100
            self.is_jumping = False
            self.velocity_y = 0
        
        # Ceiling collision
        if self.y <= 0:
            self.y = 0
            self.velocity_y = 0
        
        # Update rotation based on velocity
        self.rotation = max(-30, min(30, self.velocity_y * 2))
        
        # Update power-up timers
        self.shield_time = max(0, self.shield_time - 1)
        self.speed_boost_time = max(0, self.speed_boost_time - 1)
        self.slow_motion_time = max(0, self.slow_motion_time - 1)
        self.double_score_time = max(0, self.double_score_time - 1)
        self.invincibility_time = max(0, self.invincibility_time - 1)
        
        # Add trail effect
        self.trail_timer += 1
        if self.trail_timer % 5 == 0:
            particle_system.add_trail(self.x - 20, self.y, self.base_color)
    
    def draw(self, screen):
        # Create plane surface for rotation
        plane_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Determine color based on power-ups
        color = self.base_color
        if self.invincibility_time > 0:
            color = RED if (self.invincibility_time // 5) % 2 == 0 else YELLOW
        elif self.shield_time > 0:
            color = LIGHT_BLUE
        
        # Draw plane body
        pygame.draw.ellipse(plane_surf, color, (0, 5, self.width-10, self.height-10))
        # Draw wings
        pygame.draw.polygon(plane_surf, color, [(10, 0), (30, 15), (10, 30)])
        pygame.draw.polygon(plane_surf, color, [(40, 10), (60, 15), (40, 20)])
        
        # Rotate the plane
        rotated_surf = pygame.transform.rotate(plane_surf, self.rotation)
        rotated_rect = rotated_surf.get_rect(center=(self.x, self.y))
        screen.blit(rotated_surf, rotated_rect)
        
        # Draw shield effect
        if self.shield_time > 0:
            pygame.draw.circle(screen, LIGHT_BLUE, (int(self.x), int(self.y)), 40, 3)
    
    def get_rect(self):
        return pygame.Rect(self.x - self.width//2, self.y - self.height//2, self.width, self.height)
    
    def apply_powerup(self, power_type: PowerUpType):
        if power_type == PowerUpType.SHIELD:
            self.shield_time = 300
        elif power_type == PowerUpType.SPEED_BOOST:
            self.speed_boost_time = 300
        elif power_type == PowerUpType.SLOW_MOTION:
            self.slow_motion_time = 300
        elif power_type == PowerUpType.DOUBLE_SCORE:
            self.double_score_time = 300
        elif power_type == PowerUpType.INVINCIBILITY:
            self.invincibility_time = 180
    
    def is_invulnerable(self) -> bool:
        return self.shield_time > 0 or self.invincibility_time > 0

class Obstacle:
    def __init__(self, x: int, y: int, width: int, height: int, obstacle_type: str = "tower"):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.speed = 8
        self.type = obstacle_type
        self.color = RED if obstacle_type == "tower" else DARK_BLUE
    
    def update(self, speed_modifier: float = 1.0):
        self.x -= self.speed * speed_modifier
    
    def draw(self, screen):
        if self.type == "tower":
            # Draw tower with windows
            pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
            pygame.draw.rect(screen, BLACK, (self.x, self.y, self.width, self.height), 2)
            
            # Add windows
            for i in range(0, self.height, 40):
                for j in range(10, self.width, 25):
                    if i + 20 < self.height:
                        pygame.draw.rect(screen, YELLOW, (self.x + j, self.y + i + 10, 10, 15))
        else:
            # Draw missile
            pygame.draw.ellipse(screen, self.color, (self.x, self.y, self.width, self.height))
            pygame.draw.polygon(screen, RED, [
                (self.x + self.width, self.y + self.height//2),
                (self.x + self.width - 10, self.y + self.height//2 - 5),
                (self.x + self.width - 10, self.y + self.height//2 + 5)
            ])
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def is_off_screen(self) -> bool:
        return self.x < -self.width

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('Advanced Plane Adventure')
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Game state
        self.state = GameState.MENU
        self.mode = GameMode.CLASSIC
        self.settings = GameSettings()
        self.settings.load()
        
        # Game objects
        self.plane = Plane()
        self.obstacles = []
        self.powerups = []
        self.particle_system = ParticleSystem()
        
        # Game statistics
        self.score = 0
        self.high_scores = self.load_high_scores()
        self.lives = 3
        self.level = 1
        self.time_left = 60  # for time attack mode
        
        # Timers
        self.obstacle_timer = 0
        self.powerup_timer = 0
        self.level_timer = 0
        
        # Achievements
        self.achievements = self.init_achievements()
        
        # Fonts
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 36)
        
        # Menu selection
        self.menu_selection = 0
        self.menu_options = ["Play Classic", "Play Endless", "Time Attack", "Survival", "Settings", "Achievements", "Quit"]
    
    def init_achievements(self) -> List[Achievement]:
        return [
            Achievement("First Flight", "Play your first game", target=1),
            Achievement("Score Master", "Reach score of 100", target=100),
            Achievement("Survivor", "Survive for 5 minutes", target=300),
            Achievement("Power Collector", "Collect 10 power-ups", target=10),
            Achievement("Untouchable", "Avoid 50 obstacles", target=50),
        ]
    
    def load_high_scores(self) -> dict:
        try:
            with open('high_scores.json', 'r') as f:
                return json.load(f)
        except:
            return {"classic": 0, "endless": 0, "time_attack": 0, "survival": 0}
    
    def save_high_scores(self):
        try:
            with open('high_scores.json', 'w') as f:
                json.dump(self.high_scores, f)
        except:
            pass
    
    def update_achievement(self, name: str, progress: int = 1):
        for achievement in self.achievements:
            if achievement.name == name and not achievement.unlocked:
                achievement.progress += progress
                if achievement.progress >= achievement.target:
                    achievement.unlocked = True
                    # Achievement unlocked notification could be added here
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                if self.state == GameState.MENU:
                    self.handle_menu_input(event.key)
                elif self.state == GameState.PLAYING:
                    self.handle_game_input(event.key)
                elif self.state == GameState.PAUSED:
                    if event.key == pygame.K_p:
                        self.state = GameState.PLAYING
                elif self.state == GameState.GAME_OVER:
                    if event.key == pygame.K_SPACE:
                        self.restart_game()
                    elif event.key == pygame.K_ESCAPE:
                        self.state = GameState.MENU
    
    def handle_menu_input(self, key):
        if key == pygame.K_UP:
            self.menu_selection = (self.menu_selection - 1) % len(self.menu_options)
        elif key == pygame.K_DOWN:
            self.menu_selection = (self.menu_selection + 1) % len(self.menu_options)
        elif key == pygame.K_RETURN or key == pygame.K_SPACE:
            option = self.menu_options[self.menu_selection]
            if option == "Play Classic":
                self.mode = GameMode.CLASSIC
                self.start_game()
            elif option == "Play Endless":
                self.mode = GameMode.ENDLESS
                self.start_game()
            elif option == "Time Attack":
                self.mode = GameMode.TIME_ATTACK
                self.start_game()
            elif option == "Survival":
                self.mode = GameMode.SURVIVAL
                self.start_game()
            elif option == "Settings":
                self.state = GameState.SETTINGS
            elif option == "Achievements":
                self.state = GameState.ACHIEVEMENTS
            elif option == "Quit":
                self.running = False
    
    def handle_game_input(self, key):
        if key == self.settings.controls['jump']:
            self.plane.jump()
        elif key == self.settings.controls['pause']:
            self.state = GameState.PAUSED
    
    def start_game(self):
        self.state = GameState.PLAYING
        self.plane = Plane()
        self.obstacles = []
        self.powerups = []
        self.particle_system = ParticleSystem()
        self.score = 0
        self.level = 1
        self.lives = 3 if self.mode == GameMode.SURVIVAL else 1
        self.time_left = 60 if self.mode == GameMode.TIME_ATTACK else 0
        self.obstacle_timer = 0
        self.powerup_timer = 0
        self.level_timer = 0
        
        self.update_achievement("First Flight")
    
    def restart_game(self):
        self.start_game()
    
    def update_game(self):
        if self.state != GameState.PLAYING:
            return
        
        # Time-based updates
        if self.mode == GameMode.TIME_ATTACK:
            self.time_left -= 1/FPS
            if self.time_left <= 0:
                self.end_game()
        
        # Speed modifier for slow motion
        speed_modifier = 0.5 if self.plane.slow_motion_time > 0 else 1.0
        
        # Update plane
        self.plane.update(self.particle_system)
        
        # Update particle system
        self.particle_system.update()
        
        # Spawn obstacles
        self.obstacle_timer += 1
        spawn_rate = max(60 - self.level * 5, 30)  # Increase difficulty with level
        if self.obstacle_timer >= spawn_rate:
            self.spawn_obstacle()
            self.obstacle_timer = 0
        
        # Spawn power-ups
        self.powerup_timer += 1
        if self.powerup_timer >= 600:  # Every 10 seconds
            self.spawn_powerup()
            self.powerup_timer = 0
        
        # Update obstacles
        for obstacle in self.obstacles[:]:
            obstacle.update(speed_modifier)
            if obstacle.is_off_screen():
                self.obstacles.remove(obstacle)
                self.score += 2 if self.plane.double_score_time > 0 else 1
                self.update_achievement("Untouchable")
        
        # Update power-ups
        for powerup in self.powerups[:]:
            powerup.update()
            if powerup.is_off_screen():
                self.powerups.remove(powerup)
        
        # Check collisions
        self.check_collisions()
        
        # Level progression
        self.level_timer += 1
        if self.level_timer >= 1800:  # Every 30 seconds
            self.level += 1
            self.level_timer = 0
        
        # Check score achievements
        if self.score >= 100:
            self.update_achievement("Score Master")
    
    def spawn_obstacle(self):
        obstacle_type = random.choice(["tower", "missile"])
        if obstacle_type == "tower":
            height = random.randint(100, 300)
            obstacle = Obstacle(SCREEN_WIDTH, SCREEN_HEIGHT - height, 80, height, "tower")
        else:
            y = random.randint(50, SCREEN_HEIGHT - 100)
            obstacle = Obstacle(SCREEN_WIDTH, y, 60, 20, "missile")
        
        self.obstacles.append(obstacle)
    
    def spawn_powerup(self):
        x = SCREEN_WIDTH + 50
        y = random.randint(100, SCREEN_HEIGHT - 200)
        power_type = random.choice(list(PowerUpType))
        self.powerups.append(PowerUp(x, y, power_type))
    
    def check_collisions(self):
        plane_rect = self.plane.get_rect()
        
        # Check obstacle collisions
        for obstacle in self.obstacles[:]:
            if plane_rect.colliderect(obstacle.get_rect()):
                if not self.plane.is_invulnerable():
                    self.particle_system.add_explosion(obstacle.x, obstacle.y)
                    self.lives -= 1
                    if self.lives <= 0:
                        self.end_game()
                    else:
                        # Temporary invincibility after hit
                        self.plane.invincibility_time = 120
                self.obstacles.remove(obstacle)
                break
        
        # Check power-up collisions
        for powerup in self.powerups[:]:
            if plane_rect.colliderect(powerup.get_rect()):
                self.plane.apply_powerup(powerup.type)
                self.particle_system.add_explosion(powerup.x, powerup.y, powerup.color)
                self.powerups.remove(powerup)
                self.update_achievement("Power Collector")
                break
    
    def end_game(self):
        self.state = GameState.GAME_OVER
        
        # Update high scores
        mode_key = self.mode.name.lower()
        if self.score > self.high_scores.get(mode_key, 0):
            self.high_scores[mode_key] = self.score
            self.save_high_scores()
    
    def draw_game(self):
        # Clear screen with gradient background
        for y in range(SCREEN_HEIGHT):
            color_ratio = y / SCREEN_HEIGHT
            r = int(135 * (1 - color_ratio) + 25 * color_ratio)
            g = int(206 * (1 - color_ratio) + 25 * color_ratio)
            b = int(235 * (1 - color_ratio) + 112 * color_ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        
        # Draw game objects
        self.particle_system.draw(self.screen)
        
        for obstacle in self.obstacles:
            obstacle.draw(self.screen)
        
        for powerup in self.powerups:
            powerup.draw(self.screen)
        
        self.plane.draw(self.screen)
        
        # Draw UI
        self.draw_ui()
    
    def draw_ui(self):
        # Score
        score_text = self.font_medium.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (20, 20))
        
        # Level
        level_text = self.font_small.render(f"Level: {self.level}", True, WHITE)
        self.screen.blit(level_text, (20, 70))
        
        # Lives (for survival mode)
        if self.mode == GameMode.SURVIVAL:
            lives_text = self.font_small.render(f"Lives: {self.lives}", True, WHITE)
            self.screen.blit(lives_text, (20, 110))
        
        # Time (for time attack mode)
        if self.mode == GameMode.TIME_ATTACK:
            time_text = self.font_small.render(f"Time: {int(self.time_left)}", True, WHITE)
            self.screen.blit(time_text, (20, 110))
        
        # Power-up indicators
        y_offset = 150
        if self.plane.shield_time > 0:
            shield_text = self.font_small.render(f"Shield: {self.plane.shield_time//60 + 1}s", True, LIGHT_BLUE)
            self.screen.blit(shield_text, (20, y_offset))
            y_offset += 30
        
        if self.plane.double_score_time > 0:
            double_text = self.font_small.render(f"2x Score: {self.plane.double_score_time//60 + 1}s", True, GOLD)
            self.screen.blit(double_text, (20, y_offset))
            y_offset += 30
        
        if self.plane.slow_motion_time > 0:
            slow_text = self.font_small.render(f"Slow Mo: {self.plane.slow_motion_time//60 + 1}s", True, PURPLE)
            self.screen.blit(slow_text, (20, y_offset))
    
    def draw_menu(self):
        self.screen.fill(BLACK)
        
        # Title
        title_text = self.font_large.render("PLANE ADVENTURE", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 150))
        self.screen.blit(title_text, title_rect)
        
        # Menu options
        for i, option in enumerate(self.menu_options):
            color = YELLOW if i == self.menu_selection else WHITE
            option_text = self.font_medium.render(option, True, color)
            option_rect = option_text.get_rect(center=(SCREEN_WIDTH//2, 300 + i * 50))
            self.screen.blit(option_text, option_rect)
        
        # High scores
        high_score_text = self.font_small.render(f"High Score (Classic): {self.high_scores.get('classic', 0)}", True, WHITE)
        self.screen.blit(high_score_text, (50, SCREEN_HEIGHT - 100))
    
    def draw_game_over(self):
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Game over text
        game_over_text = self.font_large.render("GAME OVER", True, WHITE)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 100))
        self.screen.blit(game_over_text, game_over_rect)
        
        # Final score
        score_text = self.font_medium.render(f"Final Score: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 30))
        self.screen.blit(score_text, score_rect)
        
        # Instructions
        restart_text = self.font_small.render("Press SPACE to restart or ESC for menu", True, WHITE)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
        self.screen.blit(restart_text, restart_rect)
    
    def draw_paused(self):
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Paused text
        paused_text = self.font_large.render("PAUSED", True, WHITE)
        paused_rect = paused_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        self.screen.blit(paused_text, paused_rect)
        
        # Instructions
        continue_text = self.font_small.render("Press P to continue", True, WHITE)
        continue_rect = continue_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
        self.screen.blit(continue_text, continue_rect)
    
    def run(self):
        while self.running:
            self.handle_events()
            
            if self.state == GameState.PLAYING:
                self.update_game()
                self.draw_game()
            elif self.state == GameState.MENU:
                self.draw_menu()
            elif self.state == GameState.GAME_OVER:
                self.draw_game_over()
            elif self.state == GameState.PAUSED:
                self.draw_paused()
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

class CloudBackground:
    def __init__(self):
        self.clouds = []
        for _ in range(8):
            self.clouds.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(50, 300),
                'size': random.randint(30, 80),
                'speed': random.uniform(0.5, 2.0)
            })
    
    def update(self):
        for cloud in self.clouds:
            cloud['x'] -= cloud['speed']
            if cloud['x'] < -cloud['size']:
                cloud['x'] = SCREEN_WIDTH + cloud['size']
                cloud['y'] = random.randint(50, 300)
    
    def draw(self, screen):
        for cloud in self.clouds:
            # Draw cloud as multiple overlapping circles
            cloud_color = (255, 255, 255, 100)  # Semi-transparent white
            cloud_surf = pygame.Surface((cloud['size'] * 2, cloud['size']), pygame.SRCALPHA)
            
            # Draw multiple circles to create cloud shape
            for i in range(3):
                offset_x = i * cloud['size'] // 3
                pygame.draw.circle(cloud_surf, cloud_color, 
                                 (cloud['size'] // 2 + offset_x, cloud['size'] // 2), 
                                 cloud['size'] // 3)
            
            screen.blit(cloud_surf, (cloud['x'], cloud['y']))

class SoundManager:
    def __init__(self, settings: GameSettings):
        self.settings = settings
        self.sounds = {}
        self.load_sounds()
    
    def load_sounds(self):
        # Create simple sound effects using pygame
        try:
            # Jump sound
            jump_sound = pygame.mixer.Sound(buffer=self.create_jump_sound())
            self.sounds['jump'] = jump_sound
            
            # Explosion sound
            explosion_sound = pygame.mixer.Sound(buffer=self.create_explosion_sound())
            self.sounds['explosion'] = explosion_sound
            
            # Power-up sound
            powerup_sound = pygame.mixer.Sound(buffer=self.create_powerup_sound())
            self.sounds['powerup'] = powerup_sound
            
        except:
            # If sound creation fails, create dummy sounds
            self.sounds = {
                'jump': None,
                'explosion': None,
                'powerup': None
            }
    
    def create_jump_sound(self):
        # Create a simple jump sound effect
        duration = 0.1
        sample_rate = 22050
        frames = int(duration * sample_rate)
        arr = []
        for i in range(frames):
            frequency = 440 + (i / frames) * 200
            value = int(32767 * 0.3 * math.sin(2 * math.pi * frequency * i / sample_rate))
            arr.append([value, value])
        return pygame.sndarray.make_sound(pygame.array.array('h', arr))
    
    def create_explosion_sound(self):
        # Create explosion sound effect
        duration = 0.3
        sample_rate = 22050
        frames = int(duration * sample_rate)
        arr = []
        for i in range(frames):
            # Mix multiple frequencies for explosion effect
            noise = random.randint(-1000, 1000)
            decay = (frames - i) / frames
            value = int(noise * decay * 0.5)
            arr.append([value, value])
        return pygame.sndarray.make_sound(pygame.array.array('h', arr))
    
    def create_powerup_sound(self):
        # Create power-up sound effect
        duration = 0.2
        sample_rate = 22050
        frames = int(duration * sample_rate)
        arr = []
        for i in range(frames):
            frequency = 523 + (i / frames) * 400  # Rising tone
            value = int(32767 * 0.2 * math.sin(2 * math.pi * frequency * i / sample_rate))
            arr.append([value, value])
        return pygame.sndarray.make_sound(pygame.array.array('h', arr))
    
    def play_sound(self, sound_name: str):
        if self.settings.sound_enabled and sound_name in self.sounds and self.sounds[sound_name]:
            try:
                sound = self.sounds[sound_name]
                sound.set_volume(self.settings.volume)
                sound.play()
            except:
                pass

class AdvancedGame(Game):
    def __init__(self):
        super().__init__()
        self.cloud_background = CloudBackground()
        self.sound_manager = SoundManager(self.settings)
        self.combo_counter = 0
        self.combo_timer = 0
        self.screen_shake = 0
        self.boss_mode = False
        self.boss = None
        
        # Enhanced UI elements
        self.notifications = []
        self.transition_alpha = 0
        self.transition_direction = 0
    
    def add_notification(self, text: str, duration: int = 120):
        self.notifications.append({
            'text': text,
            'duration': duration,
            'alpha': 255
        })
    
    def update_notifications(self):
        for notification in self.notifications[:]:
            notification['duration'] -= 1
            if notification['duration'] < 30:
                notification['alpha'] = max(0, notification['alpha'] - 8)
            if notification['duration'] <= 0:
                self.notifications.remove(notification)
    
    def handle_game_input(self, key):
        super().handle_game_input(key)
        if key == self.settings.controls['jump']:
            self.sound_manager.play_sound('jump')
    
    def check_collisions(self):
        plane_rect = self.plane.get_rect()
        
        # Check obstacle collisions
        for obstacle in self.obstacles[:]:
            if plane_rect.colliderect(obstacle.get_rect()):
                if not self.plane.is_invulnerable():
                    self.particle_system.add_explosion(obstacle.x, obstacle.y)
                    self.sound_manager.play_sound('explosion')
                    self.screen_shake = 20
                    self.combo_counter = 0
                    self.lives -= 1
                    if self.lives <= 0:
                        self.end_game()
                    else:
                        self.plane.invincibility_time = 120
                        self.add_notification("Hit! Temporary invincibility!")
                self.obstacles.remove(obstacle)
                break
        
        # Check power-up collisions
        for powerup in self.powerups[:]:
            if plane_rect.colliderect(powerup.get_rect()):
                self.plane.apply_powerup(powerup.type)
                self.particle_system.add_explosion(powerup.x, powerup.y, powerup.color)
                self.sound_manager.play_sound('powerup')
                self.powerups.remove(powerup)
                self.update_achievement("Power Collector")
                
                # Add notification for power-up
                power_names = {
                    PowerUpType.SHIELD: "Shield Active!",
                    PowerUpType.SPEED_BOOST: "Speed Boost!",
                    PowerUpType.SLOW_MOTION: "Slow Motion!",
                    PowerUpType.DOUBLE_SCORE: "Double Score!",
                    PowerUpType.INVINCIBILITY: "Invincible!"
                }
                self.add_notification(power_names.get(powerup.type, "Power-up!"))
                break
    
    def update_game(self):
        super().update_game()
        
        if self.state != GameState.PLAYING:
            return
        
        # Update background
        self.cloud_background.update()
        
        # Update notifications
        self.update_notifications()
        
        # Update screen shake
        if self.screen_shake > 0:
            self.screen_shake -= 1
        
        # Update combo system
        self.combo_timer += 1
        if self.combo_timer >= 300:  # Reset combo after 5 seconds
            self.combo_counter = 0
        
        # Check for boss mode activation
        if self.score > 0 and self.score % 200 == 0 and not self.boss_mode:
            self.activate_boss_mode()
    
    def activate_boss_mode(self):
        self.boss_mode = True
        self.boss = BossEnemy(SCREEN_WIDTH, SCREEN_HEIGHT // 2)
        self.add_notification("BOSS INCOMING!", 180)
    
    def spawn_obstacle(self):
        if self.boss_mode and self.boss:
            return  # Don't spawn regular obstacles during boss fight
        
        # Increase obstacle variety based on level
        if self.level >= 3:
            obstacle_types = ["tower", "missile", "laser"]
        else:
            obstacle_types = ["tower", "missile"]
        
        obstacle_type = random.choice(obstacle_types)
        
        if obstacle_type == "tower":
            height = random.randint(100, 300)
            obstacle = Obstacle(SCREEN_WIDTH, SCREEN_HEIGHT - height, 80, height, "tower")
        elif obstacle_type == "missile":
            y = random.randint(50, SCREEN_HEIGHT - 100)
            obstacle = Obstacle(SCREEN_WIDTH, y, 60, 20, "missile")
        else:  # laser
            y = random.randint(100, SCREEN_HEIGHT - 200)
            obstacle = LaserObstacle(SCREEN_WIDTH, y)
        
        self.obstacles.append(obstacle)
    
    def draw_game(self):
        # Apply screen shake
        shake_x = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
        shake_y = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
        
        # Clear screen with animated gradient background
        time_factor = pygame.time.get_ticks() * 0.001
        for y in range(SCREEN_HEIGHT):
            color_ratio = y / SCREEN_HEIGHT
            # Animated color shift
            r = int(135 * (1 - color_ratio) + 25 * color_ratio + 30 * math.sin(time_factor))
            g = int(206 * (1 - color_ratio) + 25 * color_ratio + 20 * math.cos(time_factor * 1.2))
            b = int(235 * (1 - color_ratio) + 112 * color_ratio + 40 * math.sin(time_factor * 0.8))
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            pygame.draw.line(self.screen, (r, g, b), (shake_x, y + shake_y), (SCREEN_WIDTH + shake_x, y + shake_y))
        
        # Draw background elements
        self.cloud_background.draw(self.screen)
        
        # Create a surface for game objects to apply shake effect
        game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        
        # Draw game objects on the game surface
        self.particle_system.draw(game_surface)
        
        for obstacle in self.obstacles:
            obstacle.draw(game_surface)
        
        for powerup in self.powerups:
            powerup.draw(game_surface)
        
        if self.boss_mode and self.boss:
            self.boss.draw(game_surface)
        
        self.plane.draw(game_surface)
        
        # Blit game surface with shake effect
        self.screen.blit(game_surface, (shake_x, shake_y))
        
        # Draw UI (not affected by shake)
        self.draw_enhanced_ui()
        
        # Draw notifications
        self.draw_notifications()
    
    def draw_enhanced_ui(self):
        # Enhanced score display with glow effect
        score_text = self.font_medium.render(f"Score: {self.score}", True, WHITE)
        # Create glow effect
        glow_surface = pygame.Surface((score_text.get_width() + 10, score_text.get_height() + 10), pygame.SRCALPHA)
        for i in range(3):
            glow_text = self.font_medium.render(f"Score: {self.score}", True, (100, 100, 255, 50))
            glow_surface.blit(glow_text, (5 - i, 5 - i))
        glow_surface.blit(score_text, (5, 5))
        self.screen.blit(glow_surface, (15, 15))
        
        # Combo counter
        if self.combo_counter > 1:
            combo_text = self.font_small.render(f"Combo x{self.combo_counter}", True, YELLOW)
            self.screen.blit(combo_text, (SCREEN_WIDTH - 200, 20))
        
        # Level with progress bar
        level_text = self.font_small.render(f"Level: {self.level}", True, WHITE)
        self.screen.blit(level_text, (20, 70))
        
        # Level progress bar
        progress = (self.level_timer / 1800) * 200
        pygame.draw.rect(self.screen, DARK_BLUE, (20, 100, 200, 10))
        pygame.draw.rect(self.screen, LIGHT_BLUE, (20, 100, progress, 10))
        
        # Enhanced power-up display
        y_offset = 120
        power_up_icons = {
            'shield': LIGHT_BLUE,
            'double_score': GOLD,
            'slow_motion': PURPLE,
            'invincibility': RED
        }
        
        if self.plane.shield_time > 0:
            time_left = self.plane.shield_time // 60 + 1
            pygame.draw.circle(self.screen, LIGHT_BLUE, (30, y_offset + 15), 15)
            pygame.draw.circle(self.screen, WHITE, (30, y_offset + 15), 15, 2)
            shield_text = self.font_small.render(f"Shield: {time_left}s", True, LIGHT_BLUE)
            self.screen.blit(shield_text, (50, y_offset))
            y_offset += 35
        
        # Health bar for survival mode
        if self.mode == GameMode.SURVIVAL and self.lives > 1:
            health_width = 200
            health_height = 20
            health_x = SCREEN_WIDTH - health_width - 20
            health_y = 20
            
            # Background
            pygame.draw.rect(self.screen, RED, (health_x, health_y, health_width, health_height))
            # Current health
            current_width = (self.lives / 3) * health_width
            pygame.draw.rect(self.screen, GREEN, (health_x, health_y, current_width, health_height))
            # Border
            pygame.draw.rect(self.screen, WHITE, (health_x, health_y, health_width, health_height), 2)
            
            lives_text = self.font_small.render(f"Lives: {self.lives}", True, WHITE)
            self.screen.blit(lives_text, (health_x, health_y + 25))
    
    def draw_notifications(self):
        y_offset = SCREEN_HEIGHT - 100
        for notification in self.notifications:
            text_surface = self.font_small.render(notification['text'], True, WHITE)
            text_surface.set_alpha(notification['alpha'])
            text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
            
            # Background for notification
            bg_rect = pygame.Rect(text_rect.x - 10, text_rect.y - 5, text_rect.width + 20, text_rect.height + 10)
            bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            bg_surface.fill((0, 0, 0, 128))
            self.screen.blit(bg_surface, bg_rect)
            
            self.screen.blit(text_surface, text_rect)
            y_offset -= 40

class LaserObstacle(Obstacle):
    def __init__(self, x: int, y: int):
        super().__init__(x, y, 200, 10, "laser")
        self.charge_time = 120
        self.fire_time = 60
        self.warning_time = 60
        self.state = "warning"  # warning -> charging -> firing
        self.laser_width = 5
    
    def update(self, speed_modifier: float = 1.0):
        if self.state == "warning":
            self.warning_time -= 1
            if self.warning_time <= 0:
                self.state = "charging"
        elif self.state == "charging":
            self.charge_time -= 1
            if self.charge_time <= 0:
                self.state = "firing"
        elif self.state == "firing":
            self.fire_time -= 1
            if self.fire_time <= 0:
                self.x -= self.speed * speed_modifier
    
    def draw(self, screen):
        if self.state == "warning":
            # Blinking warning line
            if (self.warning_time // 10) % 2 == 0:
                pygame.draw.line(screen, YELLOW, (self.x, self.y), (self.x + self.width, self.y), 3)
        elif self.state == "charging":
            # Growing charge effect
            charge_progress = (120 - self.charge_time) / 120
            color_intensity = int(255 * charge_progress)
            pygame.draw.line(screen, (color_intensity, 0, 0), (self.x, self.y), (self.x + self.width, self.y), 5)
        elif self.state == "firing":
            # Full laser beam
            pygame.draw.line(screen, RED, (self.x, self.y), (self.x + self.width, self.y), 8)
            # Add glow effect
            pygame.draw.line(screen, (255, 100, 100), (self.x, self.y), (self.x + self.width, self.y), 4)

class BossEnemy:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.width = 120
        self.height = 80
        self.health = 100
        self.max_health = 100
        self.speed = 2
        self.attack_timer = 0
        self.move_timer = 0
        self.move_direction = 1
        self.projectiles = []
    
    def update(self):
        # Movement pattern
        self.move_timer += 1
        if self.move_timer >= 120:
            self.move_direction *= -1
            self.move_timer = 0
        
        self.y += self.move_direction * self.speed
        self.y = max(50, min(SCREEN_HEIGHT - 150, self.y))
        
        # Attack pattern
        self.attack_timer += 1
        if self.attack_timer >= 90:
            self.fire_projectile()
            self.attack_timer = 0
        
        # Update projectiles
        for projectile in self.projectiles[:]:
            projectile['x'] -= projectile['speed']
            if projectile['x'] < -20:
                self.projectiles.remove(projectile)
    
    def fire_projectile(self):
        self.projectiles.append({
            'x': self.x,
            'y': self.y + self.height // 2,
            'speed': 8,
            'width': 15,
            'height': 8
        })
    
    def draw(self, screen):
        # Draw boss body
        pygame.draw.rect(screen, (150, 0, 0), (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, RED, (self.x, self.y, self.width, self.height), 3)
        
        # Draw health bar
        health_bar_width = 200
        health_bar_height = 20
        health_x = SCREEN_WIDTH // 2 - health_bar_width // 2
        health_y = 50
        
        # Background
        pygame.draw.rect(screen, RED, (health_x, health_y, health_bar_width, health_bar_height))
        # Current health
        current_width = (self.health / self.max_health) * health_bar_width
        pygame.draw.rect(screen, GREEN, (health_x, health_y, current_width, health_bar_height))
        # Border
        pygame.draw.rect(screen, WHITE, (health_x, health_y, health_bar_width, health_bar_height), 2)
        
        # Draw projectiles
        for projectile in self.projectiles:
            pygame.draw.ellipse(screen, ORANGE, 
                              (projectile['x'], projectile['y'], projectile['width'], projectile['height']))
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def get_projectile_rects(self):
        return [pygame.Rect(p['x'], p['y'], p['width'], p['height']) for p in self.projectiles]
    
    def take_damage(self, damage: int):
        self.health -= damage
        return self.health <= 0

def main():
    try:
        game = AdvancedGame()
        game.run()
    except Exception as e:
        print(f"Game error: {e}")
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()