import pygame
from ui.constants import *
from ui.menu import Button


# ---------------------------------------------------------------------------
# Card rendering helper
# ---------------------------------------------------------------------------

SUIT_SYMBOLS = {
    "Hearts":   "♥",
    "Diamonds": "♦",
    "Clubs":    "♣",
    "Spades":   "♠",
}

RED_SUITS  = {"Hearts", "Diamonds"}
CARD_W     = 80
CARD_H     = 110
CARD_RADIUS = 8


def draw_card(surface, card_str, x, y, fonts, face_down=False):
    """
    Draws a single card at (x, y).

    card_str format: "A♠", "10♦", "K♥", etc.
    If face_down=True, draws the card back instead.
    """
    rect = pygame.Rect(x, y, CARD_W, CARD_H)

    if face_down:
        pygame.draw.rect(surface, (30, 50, 120), rect, border_radius=CARD_RADIUS)
        pygame.draw.rect(surface, GOLD, rect, 2, border_radius=CARD_RADIUS)
        # Simple pattern on card back
        inner = pygame.Rect(x + 6, y + 6, CARD_W - 12, CARD_H - 12)
        pygame.draw.rect(surface, (40, 65, 150), inner, border_radius=4)
        return

    # Card face
    pygame.draw.rect(surface, CARD_WHITE, rect, border_radius=CARD_RADIUS)
    pygame.draw.rect(surface, (180, 180, 175), rect, 2, border_radius=CARD_RADIUS)

    # Determine color from last character (the suit symbol)
    suit_char = card_str[-1] if card_str else "?"
    is_red    = suit_char in ("♥", "♦")
    color     = RED if is_red else BLACK

    # Rank text top-left and bottom-right
    small_font = fonts["small"]
    rank_label = small_font.render(card_str, True, color)
    surface.blit(rank_label, (x + 6, y + 6))

    # Large suit symbol in center
    center_font = fonts["large"]
    center_sym  = small_font.render(suit_char, True, color)
    cx_sym      = center_sym.get_rect(center=(x + CARD_W // 2, y + CARD_H // 2))
    surface.blit(center_sym, cx_sym)


def draw_hand(surface, cards, start_x, y, fonts, hide_second=False):
    """
    Draws a list of card strings in a row.
    hide_second=True is used for the dealer's hole card.
    """
    gap = CARD_W + 12
    for i, card in enumerate(cards):
        face_down = (hide_second and i == 1)
        draw_card(surface, card, start_x + i * gap, y, fonts, face_down)


# ---------------------------------------------------------------------------
# Table screen
# ---------------------------------------------------------------------------

class Table:
    """
    Main Blackjack game screen.

    States:
        "betting"  -- player sets their bet before the deal
        "playing"  -- player's turn (hit / stand / double down)
        "dealer"   -- dealer plays out their hand automatically
        "result"   -- round over, outcome displayed
    """

    # Placeholder data — swap these out when game logic is connected
    PLACEHOLDER = {
        "player_chips": 1000,
        "player_bet":   0,
        "player_hand":  [],
        "dealer_hand":  [],
        "player_total": 0,
        "dealer_total": 0,
        "hint":         "",
        "message":      "",   # win / lose / push message
    }

    BET_AMOUNTS = [10, 25, 50, 100]

    def __init__(self, screen, fonts):
        self.screen = screen
        self.fonts  = fonts
        self.state  = "betting"

        # Game data (placeholder until game logic is wired in)
        self.chips       = 1000
        self.bet         = 0
        self.player_hand = []
        self.dealer_hand = []
        self.hint        = ""
        self.message     = ""

        self._build_buttons()

    # ------------------------------------------------------------------
    # Build / rebuild UI buttons
    # ------------------------------------------------------------------

    def _build_buttons(self):
        cx = SCREEN_WIDTH // 2

        # Action buttons — shown during player's turn
        self.btn_hit    = Button(cx - 210, 600, 120, 50, "Hit",         self.fonts["medium"])
        self.btn_stand  = Button(cx - 65,  600, 130, 50, "Stand",       self.fonts["medium"])
        self.btn_double = Button(cx + 85,  600, 180, 50, "Double Down", self.fonts["medium"])

        # Bet chip buttons — shown during betting phase
        self.bet_buttons = [
            Button(cx - 240 + i * 125, 560, 110, 50, f"+${amt}", self.fonts["medium"])
            for i, amt in enumerate(self.BET_AMOUNTS)
        ]
        self.btn_deal     = Button(cx - 75,  630, 150, 55, "Deal",       self.fonts["large"])
        self.btn_clear    = Button(cx + 90,  630, 150, 55, "Clear Bet",  self.fonts["medium"])

        # Next round button — shown on result screen
        self.btn_next     = Button(cx - 100, 620, 200, 55, "Next Round", self.fonts["large"])

        # Back to menu button — always visible
        self.btn_menu     = Button(20, 20, 130, 40, "← Menu", self.fonts["small"])

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_enter(self):
        """Called by screen.py every time the table becomes active."""
        self.state       = "betting"
        self.bet         = 0
        self.player_hand = []
        self.dealer_hand = []
        self.hint        = ""
        self.message     = ""

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def handle_event(self, event):
        # Always available
        if self.btn_menu.is_clicked(event):
            return "menu"

        if self.state == "betting":
            return self._handle_betting(event)
        elif self.state == "playing":
            return self._handle_playing(event)
        elif self.state == "result":
            return self._handle_result(event)

        return None

    def _handle_betting(self, event):
        # Chip buttons
        for btn, amt in zip(self.bet_buttons, self.BET_AMOUNTS):
            if btn.is_clicked(event):
                if self.bet + amt <= self.chips:
                    self.bet += amt

        # Clear bet
        if self.btn_clear.is_clicked(event):
            self.bet = 0

        # Deal — only if a bet has been placed
        if self.btn_deal.is_clicked(event) and self.bet > 0:
            self._start_round()

        return None

    def _handle_playing(self, event):
        if self.btn_hit.is_clicked(event):
            print("[table] Hit")          # replace with game logic call

        if self.btn_stand.is_clicked(event):
            print("[table] Stand")        # replace with game logic call
            self.state = "dealer"

        if self.btn_double.is_clicked(event):
            print("[table] Double Down")  # replace with game logic call

        return None

    def _handle_result(self, event):
        if self.btn_next.is_clicked(event):
            self.state       = "betting"
            self.bet         = 0
            self.player_hand = []
            self.dealer_hand = []
            self.hint        = ""
            self.message     = ""
        return None

    # ------------------------------------------------------------------
    # Placeholder round start
    # ------------------------------------------------------------------

    def _start_round(self):
        """
        Temporary placeholder — deals fake cards so the layout renders.
        Replace the hand assignments here with real Deck.deal() calls
        once game logic is connected.
        """
        self.chips       -= self.bet
        self.player_hand  = ["A♠", "9♥"]
        self.dealer_hand  = ["K♦", "?"]   # second card hidden
        self.hint         = "Recommended: Stand"
        self.state        = "playing"

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(self):
        self._draw_table()
        self._draw_dealer_zone()
        self._draw_player_zone()
        self._draw_hud()

        if self.state == "betting":
            self._draw_betting_ui()
        elif self.state == "playing":
            self._draw_action_buttons()
            self._draw_hint()
        elif self.state == "dealer":
            self._draw_hint()
        elif self.state == "result":
            self._draw_result()

        # Menu button always visible
        mouse_pos = pygame.mouse.get_pos()
        self.btn_menu.check_hover(mouse_pos)
        self.btn_menu.draw(self.screen)

    # ------------------------------------------------------------------
    # Draw helpers
    # ------------------------------------------------------------------

    def _draw_table(self):
        """Felt background and decorative table arc."""
        self.screen.fill(FELT_DARK_GREEN)

        # Table oval / arc
        table_rect = pygame.Rect(80, 60, SCREEN_WIDTH - 160, SCREEN_HEIGHT - 100)
        pygame.draw.ellipse(self.screen, FELT_GREEN, table_rect)
        pygame.draw.ellipse(self.screen, GOLD, table_rect, 3)

        # Title watermark
        wm = self.fonts["small"].render("A.C.E. — AI Casino Education", True, (50, 110, 65))
        self.screen.blit(wm, wm.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))

    def _draw_dealer_zone(self):
        """Dealer label, cards, and total."""
        label = self.fonts["medium"].render("DEALER", True, GOLD)
        self.screen.blit(label, label.get_rect(center=(SCREEN_WIDTH // 2, 105)))

        if self.dealer_hand:
            total_cards = len(self.dealer_hand)
            start_x     = SCREEN_WIDTH // 2 - (total_cards * (CARD_W + 12)) // 2
            hide        = (self.state == "playing")   # hide hole card during player turn
            draw_hand(self.screen, self.dealer_hand, start_x, 125, self.fonts, hide_second=hide)

            # Show total only when hole card is revealed
            if not hide:
                total_label = self.fonts["small"].render(
                    f"Total: {self._hand_total(self.dealer_hand)}", True, TEXT_LIGHT
                )
                self.screen.blit(total_label, total_label.get_rect(
                    center=(SCREEN_WIDTH // 2, 125 + CARD_H + 18)
                ))

    def _draw_player_zone(self):
        """Player label, cards, and total."""
        label = self.fonts["medium"].render("YOUR HAND", True, GOLD)
        self.screen.blit(label, label.get_rect(center=(SCREEN_WIDTH // 2, 370)))

        if self.player_hand:
            total_cards = len(self.player_hand)
            start_x     = SCREEN_WIDTH // 2 - (total_cards * (CARD_W + 12)) // 2
            draw_hand(self.screen, self.player_hand, start_x, 390, self.fonts)

            total_label = self.fonts["small"].render(
                f"Total: {self._hand_total(self.player_hand)}", True, TEXT_LIGHT
            )
            self.screen.blit(total_label, total_label.get_rect(
                center=(SCREEN_WIDTH // 2, 390 + CARD_H + 18)
            ))

    def _draw_hud(self):
        """Chip count and current bet — always visible."""
        chips_label = self.fonts["medium"].render(f"Chips:  ${self.chips}", True, TEXT_LIGHT)
        bet_label   = self.fonts["medium"].render(f"Bet:      ${self.bet}",  True, GOLD)
        self.screen.blit(chips_label, (SCREEN_WIDTH - 220, 30))
        self.screen.blit(bet_label,   (SCREEN_WIDTH - 220, 60))

    def _draw_betting_ui(self):
        """Chip add buttons, clear, and deal button."""
        prompt = self.fonts["medium"].render("Place your bet:", True, TEXT_LIGHT)
        self.screen.blit(prompt, prompt.get_rect(center=(SCREEN_WIDTH // 2, 530)))

        mouse_pos = pygame.mouse.get_pos()
        for btn in self.bet_buttons:
            btn.check_hover(mouse_pos)
            btn.draw(self.screen)

        self.btn_clear.check_hover(mouse_pos)
        self.btn_clear.draw(self.screen)

        # Only light up Deal if a bet has been placed
        self.btn_deal.check_hover(mouse_pos)
        if self.bet == 0:
            # Draw greyed-out deal button
            grey_rect = self.btn_deal.rect
            pygame.draw.rect(self.screen, (60, 60, 60), grey_rect, border_radius=8)
            pygame.draw.rect(self.screen, (90, 90, 90), grey_rect, 2, border_radius=8)
            lbl = self.fonts["large"].render("Deal", True, (100, 100, 100))
            self.screen.blit(lbl, lbl.get_rect(center=grey_rect.center))
        else:
            self.btn_deal.draw(self.screen)

    def _draw_action_buttons(self):
        """Hit, Stand, Double Down buttons during player turn."""
        mouse_pos = pygame.mouse.get_pos()
        for btn in [self.btn_hit, self.btn_stand, self.btn_double]:
            btn.check_hover(mouse_pos)
            btn.draw(self.screen)

    def _draw_hint(self):
        """AI strategy hint banner."""
        if not self.hint:
            return
        panel = pygame.Rect(SCREEN_WIDTH // 2 - 180, 558, 360, 36)
        pygame.draw.rect(self.screen, DARK_GREY, panel, border_radius=6)
        pygame.draw.rect(self.screen, GOLD, panel, 1, border_radius=6)
        hint_label = self.fonts["small"].render(f"🤖  {self.hint}", True, GOLD)
        self.screen.blit(hint_label, hint_label.get_rect(center=panel.center))

    def _draw_result(self):
        """Win / lose / push overlay and Next Round button."""
        # Semi-transparent dark panel
        overlay = pygame.Surface((460, 120), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (SCREEN_WIDTH // 2 - 230, 490))

        msg_color = (
            (80, 200, 80)   if "win"  in self.message.lower() else
            (200, 80, 80)   if "lose" in self.message.lower() else
            TEXT_LIGHT
        )
        msg_label = self.fonts["large"].render(self.message, True, msg_color)
        self.screen.blit(msg_label, msg_label.get_rect(center=(SCREEN_WIDTH // 2, 520)))

        mouse_pos = pygame.mouse.get_pos()
        self.btn_next.check_hover(mouse_pos)
        self.btn_next.draw(self.screen)

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def _hand_total(self, hand):
        """
        Temporary total calculator for display purposes.
        Replace with hand.get_value() once game classes are connected.
        Handles basic Ace (11 → 1) logic.
        """
        total = 0
        aces  = 0
        for card in hand:
            if card == "?":
                continue
            rank = card[:-1]   # strip suit symbol
            if rank in ("J", "Q", "K"):
                total += 10
            elif rank == "A":
                total += 11
                aces  += 1
            else:
                try:
                    total += int(rank)
                except ValueError:
                    pass
            while total > 21 and aces:
                total -= 10
                aces  -= 1
        return total