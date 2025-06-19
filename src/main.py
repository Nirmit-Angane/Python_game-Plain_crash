import pygame
import random
import pyttsx3
import sys
import asyncio

pygame.init()

collision_sound = pygame.mixer.Sound('C:/coding_files/PROJECT/Python_game-Plain_crash/assets/Explosion Sound Effect.mp3')
pygame.mixer.music.set_volume(50)

engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()

screen_width, screen_height = 1366, 768
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Plane 911 Game')

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_BLUE = (173, 216, 230)

plane_image = pygame.image.load('C:/coding_files/PROJECT/Python_game-Plain_crash/assets/plane2.png')
tower_image = pygame.image.load('C:/coding_files/PROJECT/Python_game-Plain_crash/assets/2tower.png')
cloud_image = pygame.image.load('C:/coding_files/PROJECT/Python_game-Plain_crash/assets/cloud_image.png')
blast_image = pygame.image.load('C:/coding_files/PROJECT/Python_game-Plain_crash/assets/blast.png')
background_image_1 = pygame.image.load('C:/coding_files/PROJECT/Python_game-Plain_crash/assets/background_image.jpg')
background_image_2 = pygame.image.load('C:/coding_files/PROJECT/Python_game-Plain_crash/assets/background2_image.jpg')

font = pygame.font.Font(None, 60)

def show_loading_screen():
    loading_text = "Loading"
    dot_count = 0
    dot_max = 3
    dot_timer = 0
    dot_delay = 500  

    object_x, object_y = 5, 270
    loading_bar_x = -10
    loading_bar_y = 310
    loading_bar_width = 1385
    loading_bar_height = 150
    plane_speed = 5

    intro_timer = pygame.time.get_ticks()
    loading_duration = 5000  

    while pygame.time.get_ticks() - intro_timer < loading_duration:
        screen.fill(WHITE)  
        screen.blit(background_image_1, (0, 0))
        pygame.draw.rect(screen, BLACK, (loading_bar_x, loading_bar_y, loading_bar_width, loading_bar_height), 5, 15)
        fill_width = min(object_x, loading_bar_width - 10)
        pygame.draw.rect(screen, LIGHT_BLUE, (loading_bar_x + 5, loading_bar_y + 5, fill_width, loading_bar_height - 10), border_radius=15)

        object_x += plane_speed
        if object_x > loading_bar_width + loading_bar_x - 40:  
            object_x = loading_bar_width + loading_bar_x - 40

        screen.blit(plane_image, (object_x, object_y))

        dot_timer += fps_clock.get_time()
        if dot_timer >= dot_delay:
            dot_timer = 0
            dot_count = (dot_count + 1) % (dot_max + 1) 

        text = f"{loading_text}{'.' * dot_count}"
        text_surface = font.render(text, True, BLACK)
        text_rect = text_surface.get_rect(center=(screen_width // 2, screen_height // 2))
        screen.blit(text_surface, text_rect)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        fps_clock.tick(60)

def show_intro_screen():
    screen.blit(background_image_1, (0, 0))
    title_text = font.render("Plane Game", True, BLACK)
    instruction_text = font.render("Press SPACE or UP to Start", True, BLACK)
    screen.blit(title_text, (screen_width // 2 - title_text.get_width() // 2, screen_height // 2 - title_text.get_height()))
    screen.blit(instruction_text, (screen_width // 2 - instruction_text.get_width() // 2, screen_height // 2 + 20))

    pygame.display.flip()
    speak("Welcome to plane Crash game")
    speak("Press Space or up to start")

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                waiting = False

def show_outro_screen(score):
    screen.blit(background_image_1, (0, 0)) 
    game_over_text = font.render("Game Over", True, BLACK)
    score_text = font.render(f" Final Score: {score}", True, BLACK)
    restart_text = font.render("Press SPACE or UP to Restart or ESC to Quit", True, BLACK)
    screen.blit(game_over_text, (screen_width // 2 - game_over_text.get_width() // 2, screen_height // 2 - game_over_text.get_height()))
    screen.blit(score_text, (screen_width // 2 - score_text.get_width() // 2, screen_height // 2 + 20))
    screen.blit(restart_text, (screen_width // 2 - restart_text.get_width() // 2, screen_height // 2 + 80))

    pygame.display.flip()

    speak("Game Over")    
    speak(f"Final score is {score}")
    speak("Press SPACE or UP to Restart or escape to Quit")  

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    return True  
                if event.key == pygame.K_ESCAPE:
                    return False  

class Blast:
    def __init__(self, x, y):
        self.image = blast_image
        self.rect = self.image.get_rect(center=(x, y))
        self.lifetime = 50  
        self.current_time = 0

    def update(self):
        self.current_time += 1  

    def draw(self, screen):
        screen.blit(self.image, self.rect)
    
    def is_expired(self):
        return self.current_time >= self.lifetime

class Plane:
    def __init__(self):
        self.image = plane_image
        self.rect = self.image.get_rect()
        self.rect.x = 50
        self.rect.y = screen_height - self.rect.height - 40
        self.jump_speed = 35
        self.gravity = 1
        self.is_jumping = False
        self.velocity = 1

    def jump(self):
        if not self.is_jumping:
            self.is_jumping = True
            self.velocity = -self.jump_speed

    def update(self):
        if self.is_jumping:
            self.velocity += self.gravity
            self.rect.y += self.velocity

            if self.rect.y >= screen_height - self.rect.height - 20:
                self.rect.y = screen_height - self.rect.height - 20
                self.is_jumping = False

    def draw(self, screen):
        screen.blit(self.image, self.rect)

class Cloud:
    def __init__(self):
        self.image = cloud_image
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(screen_width, screen_width + 300)
        self.rect.y = random.randint(50, 200)
        self.speed = random.randint(1, 5)

    def update(self):
        self.rect.x -= self.speed

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def is_off_screen(self):
        return self.rect.x < -self.rect.width

class Tower:
    def __init__(self):
        self.image = tower_image
        self.rect = self.image.get_rect()
        self.rect.x = screen_width
        self.rect.y = screen_height - self.rect.height - 1
        self.speed = 10

    def update(self):
        self.rect.x -= self.speed

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def is_off_screen(self):
        return self.rect.x < -self.rect.width

def main():
    global fps_clock
    fps_clock = pygame.time.Clock()
    show_loading_screen()

    while True:
        show_intro_screen()
        plane = Plane()
        towers = []
        clouds = []
        blasts = []
        score = 0
        game_over = False

        while not game_over:
            if score >= 2:
                screen.blit(background_image_2, (0, 0))
                score_color = WHITE
            else:
                screen.blit(background_image_1, (0, 0))
                score_color = WHITE

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                        plane.jump()

            if len(clouds) == 0 or clouds[-1].rect.x < screen_width - 300:
                clouds.append(Cloud())

            for cloud in clouds[:]:
                cloud.update()
                cloud.draw(screen)
                if cloud.is_off_screen():
                    clouds.remove(cloud)

            plane.update()
            plane.draw(screen)

            if len(towers) == 0 or towers[-1].rect.x < screen_width - 900:
                towers.append(Tower())

            for tower in towers[:]:
                tower.update()
                tower.draw(screen)
                if tower.rect.colliderect(plane.rect):
                    blasts.append(Blast(tower.rect.centerx, tower.rect.centery))
                    collision_sound.play()
                    game_over = True

                if tower.is_off_screen():
                    towers.remove(tower)
                    score += 1

            for blast in blasts[:]:
                blast.update()
                blast.draw(screen)
                if blast.is_expired():
                    blasts.remove(blast)

            score_text = font.render(f"Score: {score}", True, score_color)
            screen.blit(score_text, (10, 10))

            pygame.display.flip()
            fps_clock.tick(60)

            if game_over:
                pygame.time.delay(1000)
                break

        if not show_outro_screen(score):
            break

    pygame.quit()

if __name__ == "__main__":
    main() 