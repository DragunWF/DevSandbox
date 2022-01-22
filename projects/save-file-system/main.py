import pygame
from sys import exit

pygame.init()
window = pygame.display.set_mode((700, 650))
clock = pygame.time.Clock()
background = pygame.image.load(
    "projects/save-file-system/assets/background.png")

buttons = pygame.sprite.Group()
button_delay = pygame.USEREVENT + 1


class Button(pygame.sprite.Sprite):
    def __init__(self, event_type):
        self.event = event_type
        frame_1 = pygame.image.load(
            "projects/save-file-system/assets/blue_button.png")
        frame_2 = pygame.image.load(
            "projects/save-file-system/assets/red_button.png")
        frame_3 = pygame.image.load(
            "projects/save-file-system/assets/red_button_pushed.png")
        self.frames = [frame_1, frame_2, frame_3]
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=(400, 200))

    def on_pressed(self):
        events = ("increase", "decrease", "save", "load")

    def check_hover(self, pos, pressed):
        if self.rect.collidepoint(pos):
            self.image = self.frames[1]

    def update(self, mouse_pos, mouse_pressed):
        self.check_hover(mouse_pos, mouse_pressed)


def check_collisions():
    pass


def show_main_ui():
    pass


def show_save_ui():
    pass


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

    window.blit(background, (0, 0))

    buttons.update()
    buttons.draw(window)

    pygame.display.update()
    clock.tick(60)
