import pygame
import sys
from ui.constants import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, load_fonts
from ui.menu import MainMenu

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT   ))
pygame.display.set_caption("A.C.E. - AI Casino Education")
clock = pygame.time.Clock()
fonts = load_fonts()

current_screen = "menu"
menu = MainMenu(screen, fonts)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if current_screen == "menu":
            result = menu.handle_event(event)
            if result == "play":
                current_screen = "game"   # switch to game screen later
            elif result == "quit":
                pygame.quit()
                sys.exit()

    if current_screen == "menu":
        menu.draw()

    pygame.display.flip()
    clock.tick(FPS)