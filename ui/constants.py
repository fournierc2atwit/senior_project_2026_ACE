import pygame
# Screen

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# Colors
FELT_GREEN = (35,101,56)
FELT_DARK_GREEN = (20, 75, 40)
GOLD = (212, 175, 55)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
CARD_WHITE = (245, 245, 240)
RED = (180, 30, 30)
DARK_GREY = (40, 40, 40)
CHIP_BLUE = (30, 80, 180)
CHIP_RED = (180, 40, 40)
CHIP_GREEN = (40, 150, 80)
TEXT_LIGHT = (230, 220, 200)

# Fonts
def load_fonts():
    return {
        "title": pygame.font.SysFont("Georgia", 52, bold=True),
        "large": pygame.font.SysFont("Georgia", 36),
        "medium": pygame.font.SysFont("Arial", 24),
        "small": pygame.font.SysFont("Arial", 18)
    }