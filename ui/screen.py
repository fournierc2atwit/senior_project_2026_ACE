import pygame
import sys
from ui.constants import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, load_fonts
from ui.menu import MainMenu
from ui.table import Table
from ui.tutorial import Tutorial


class Screen:
    """
    Master controller for the game window and screen switching.
    Owns the main game loop and delegates drawing/input to
    whichever screen is currently active.

    Screens:
        "menu"     -- main menu
        "game"     -- live blackjack table
        "tutorial" -- guided tutorial mode
        "stats"    -- player stats (placeholder for now)
    """

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("A.C.E. - AI Casino Education")

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock  = pygame.time.Clock()
        self.fonts  = load_fonts()

        # Initialize all screens
        self.screens = {
            "menu":     MainMenu(self.screen, self.fonts),
            "game":     Table(self.screen, self.fonts),
            "tutorial": Tutorial(self.screen, self.fonts),
        }

        self.current = "menu"

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self):
        while True:
            self._handle_events()
            self._draw()
            pygame.display.flip()
            self.clock.tick(FPS)

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def _handle_events(self):
        for event in pygame.event.get():

            # Window close button
            if event.type == pygame.QUIT:
                self._quit()

            # Global escape key — always returns to menu
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._switch("menu")

            # Delegate the event to the active screen
            result = self.screens[self.current].handle_event(event)

            # Screens return a string to request a screen switch,
            # or None if no switch is needed.
            if result:
                self._handle_result(result)

    def _handle_result(self, result):
        """
        Processes navigation results returned by screens.
        Screens return a plain string like "menu", "game", "quit", etc.
        """
        if result == "quit":
            self._quit()
        elif result in self.screens:
            self._switch(result)
        else:
            print(f"[screen.py] Unknown screen result: '{result}'")

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _draw(self):
        self.screens[self.current].draw()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _switch(self, screen_name):
        """
        Switch the active screen. Calls on_enter() on the incoming
        screen if the method exists, so screens can reset their state.
        """
        if screen_name not in self.screens:
            print(f"[screen.py] Tried to switch to unknown screen: '{screen_name}'")
            return

        self.current = screen_name

        # Let the screen reset/prepare itself when entered
        incoming = self.screens[self.current]
        if hasattr(incoming, "on_enter"):
            incoming.on_enter()

    def _quit(self):
        pygame.quit()
        sys.exit()