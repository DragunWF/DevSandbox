import pygame
import json
import random
from sys import exit

pygame.init()
window = pygame.display.set_mode((700, 650))
clock = pygame.time.Clock()
background = pygame.image.load(
    "projects/save-file-system/assets/background.png")

buttons = pygame.sprite.Group()
button_delay = pygame.USEREVENT + 1


class Button(pygame.sprite.Sprite):
    def __init__(self, event_type, x_pos, y_pos):
        self.event = event_type
        frame_1 = pygame.image.load(
            "projects/save-file-system/assets/blue_button.png")
        frame_2 = pygame.image.load(
            "projects/save-file-system/assets/red_button.png")
        frame_3 = pygame.image.load(
            "projects/save-file-system/assets/red_button_pushed.png")
        self.frames = [frame_1, frame_2, frame_3]
        self.frames = list(
            map(lambda frame: pygame.transform.scale2x(frame), self.frames))
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=(x_pos, y_pos))

    def increase_gold():
        return random.randint(25, 100)

    def decrease_gold():
        return -random.randint(25, 100)

    def save_file():
        pass

    def load_file():
        pass

    def on_pressed(self):
        events = {"increase": self.increase_gold, "decrease": self.decrease_gold,
                  "save": self.save_file, "load": self.load_file}
        return events[self.event]()

    def check_hover(self, pos, pressed):
        if self.rect.collidepoint(pos):
            self.image = self.frames[1]
            if pressed:
                self.on_pressed()
        else:
            self.image = self.frames[0]

    def update(self, mouse_pos, mouse_pressed):
        self.check_hover(mouse_pos, mouse_pressed)


class PlayerCurrency:
    def __init__(self):
        self.gold = 0
        self.increase_pressed_amount = 0
        self.decrease_pressed_amount = 0
        self.saved_amount = 0


def check_collisions(mouse_pos, mouse_pressed):
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
