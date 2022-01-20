import pygame
from sys import exit

pygame.init()
window = pygame.display.set_mode((800, 400))
clock = pygame.time.Clock()

buttons = pygame.sprite.Group()
button_delay = pygame.USEREVENT + 1


class Button(pygame.sprite.Sprite):
    def __init__(self):
        self.image = pygame.image.load("")
        self.rect = self.image.get_rect(center=(400, 200))

    def check_hover(self, pos, pressed):
        if self.rect.collidepoint(pos):
            pass

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

    buttons.update()
    buttons.draw(window)

    pygame.display.update()
    clock.tick(60)
