import pygame
from ui.constants import *


class Button:
    def __init__(self, x, y, width, height, text, font):
        self.rect    = pygame.Rect(x, y, width, height)
        self.text    = text
        self.font    = font
        self.hovered = False

    def draw(self, surface):
        color      = GOLD      if self.hovered else DARK_GREY
        text_color = BLACK     if self.hovered else WHITE
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, GOLD, self.rect, 2, border_radius=8)
        label      = self.font.render(self.text, True, text_color)
        label_rect = label.get_rect(center=self.rect.center)
        surface.blit(label, label_rect)

    def check_hover(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, event):
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )


class MainMenu:
    def __init__(self, screen, fonts):
        self.screen = screen
        self.fonts  = fonts
        cx = SCREEN_WIDTH // 2

        self.buttons = {
            "play":     Button(cx - 150, 320, 300, 60, "Play",     fonts["large"]),
            "tutorial": Button(cx - 150, 400, 300, 60, "Tutorial", fonts["large"]),
            "stats":    Button(cx - 150, 480, 300, 60, "Stats",    fonts["large"]),
            "quit":     Button(cx - 150, 560, 300, 60, "Quit",     fonts["large"]),
        }

    def handle_event(self, event):
        for name, btn in self.buttons.items():
            if btn.is_clicked(event):
                return name  # returns "play", "tutorial", "stats", or "quit"
        return None

    def draw(self):
        self.screen.fill(FELT_DARK_GREEN)

        # Title
        title    = self.fonts["title"].render("A.C.E.", True, GOLD)
        subtitle = self.fonts["medium"].render("AI Casino Education", True, TEXT_LIGHT)
        self.screen.blit(title,    title.get_rect(center=(SCREEN_WIDTH // 2, 180)))
        self.screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_WIDTH // 2, 250)))

        # Buttons
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.buttons.values():   # .values() to get Button objects, not keys
            btn.check_hover(mouse_pos)
            btn.draw(self.screen)