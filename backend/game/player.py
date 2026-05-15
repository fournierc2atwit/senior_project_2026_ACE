from game.hand import Hand

class Player:
    # Represents a player in the game
    # Goals:
    # - Manage player's chip count
    # - Handle betting logic (place bet, win, lose)
    # - Track the current hand
    # - Apply win/loss/push outcomes to chip count

    STARTING_CHIPS = 1000
    def __init__(self, name, chips=STARTING_CHIPS):
        self.name = name
        self.chips = chips
        self.hand = Hand()
        self.bet = 0

    def place_bet(self, amount):
        # Place a bet for the current round
        # Deducts the bet amount from player's chips
        # Returns True if bet is successfully placed, False if insufficient chips
        if amount <= 0:
            raise ValueError("Bet amount must be positive")
            return False
        if amount > self.chips:
            print(f"{self.name} does not have enough chips. Current chips: {self.chips}")
            return False
        self.bet = amount
        self.chips -= amount
        return True
    
    def clear_bet(self):
        # Clear the current bet (used after round is resolved)
        self.chips += self.bet
        self.bet = 0
    
    def double_down(self):
        # Doubles the current bet, but only if player has enough chips and has exactly 2 cards in hand
        if self.bet > self.chips:
            print(f"[{self.name}] Not enough chips to double down.")
            return False
        self.chips -= self.bet  # Deduct the additional bet amount
        self.bet *= 2
        return True
    
    # Outcome methods
    def win(self, blackjack=False):
        # Player wins the round
        # Standard win pays 1:1, blackjack pays 3:2
        if blackjack:
            payout = int(self.bet * 1.5)
        else:
            payout = self.bet
        self.chips += self.bet + payout  # Return original bet + winnings
        self.bet = 0
    def lose(self):
        # Player loses the round, bet is already deducted
        self.bet = 0
    def push(self):
        # Round is a tie, return the bet to player's chips
        self.chips += self.bet
        self.bet = 0

    # Hand management
    def new_hand(self):
        # Clear the current hand for a new round
        self.hand.clear()
    def is_broke(self):
        # Check if player has run out of chips and has no active bets
        return self.chips == 0 and self.bet == 0
    
    # Display
    def __str__(self):
        return (f"{self.name} — Chips: ${self.chips}  "
                f"Bet: ${self.bet}  Hand: {self.hand}")
    def __repr__(self):
        return f"Player(name='{self.name}', chips={self.chips}, bet={self.bet})"
    
# Test cases
if __name__ == "__main__":
    from game.card import Card
    from game.deck import Deck

print("=== Player Tests ===\n")

# Test 1: Starting state
p = Player("Colby")
assert p.chips == 1000 and p.bet == 0
print(f"Test 1  — Starting state       chips={p.chips}, bet={p.bet} (expected 1000, 0): PASS")

# Test 2: Valid bet
result = p.place_bet(100)
assert result and p.chips == 900 and p.bet == 100
print(f"Test 2  — Place $100 bet       chips={p.chips}, bet={p.bet} (expected 900, 100): PASS")

# Test 3: Clear bet
p.clear_bet()
assert p.chips == 1000 and p.bet == 0
print(f"Test 3  — Clear bet            chips={p.chips}, bet={p.bet} (expected 1000, 0): PASS")

# Test 4: Bet more than chips
result = p.place_bet(9999)
assert not result and p.chips == 1000
print(f"Test 4  — Bet > chips          rejected={not result}, chips={p.chips} (expected True, 1000): PASS")

# Test 5: Bet of 0
result = p.place_bet(0)
assert not result
print(f"Test 5  — Bet of 0             rejected={not result} (expected True): PASS")

# Test 6: Standard win
# chips=1000, bet 200 → chips=800. Win: 800 + 200 back + 200 payout = 1200
p.place_bet(200)
p.win()
assert p.chips == 1200
print(f"Test 6  — Win $200 bet         chips={p.chips} (expected 1200): PASS")

# Test 7: Blackjack win (3:2 payout)
# chips=1200, bet 200 → chips=1000. Win BJ: 1000 + 200 back + 300 payout = 1500
p.place_bet(200)
p.win(blackjack=True)
assert p.chips == 1500
print(f"Test 7  — Blackjack $200 bet   chips={p.chips} (expected 1500): PASS")

# Test 8: Loss
p2 = Player("Test", chips=500)
p2.place_bet(100)
p2.lose()
assert p2.chips == 400 and p2.bet == 0
print(f"Test 8  — Lose $100 bet        chips={p2.chips}, bet={p2.bet} (expected 400, 0): PASS")

# Test 9: Push
p2.place_bet(100)
p2.push()
assert p2.chips == 400 and p2.bet == 0
print(f"Test 9  — Push $100 bet        chips={p2.chips}, bet={p2.bet} (expected 400, 0): PASS")

# Test 10: Double down
p3 = Player("Test2", chips=500)
p3.place_bet(100)   # chips=400, bet=100
result = p3.double_down()
assert result and p3.chips == 300 and p3.bet == 200
print(f"Test 10 — Double down          chips={p3.chips}, bet={p3.bet} (expected 300, 200): PASS")

# Test 11: Double down — not enough chips
p4 = Player("Broke", chips=50)
p4.place_bet(50)    # chips=0, bet=50
result = p4.double_down()
assert not result and p4.bet == 50
print(f"Test 11 — Double down broke    rejected={not result}, bet={p4.bet} (expected True, 50): PASS")

# Test 12: is_broke
p5 = Player("Broke2", chips=0)
assert p5.is_broke()
print(f"Test 12 — is_broke             {p5.is_broke()} (expected True): PASS")

# Test 13: new_hand clears cards
p.new_hand()
deck = Deck()
p.hand.add_card(deck.deal())
p.hand.add_card(deck.deal())
assert len(p.hand) == 2
p.new_hand()
assert len(p.hand) == 0
print(f"Test 13 — new_hand()           len={len(p.hand)} (expected 0): PASS")

print("\nAll tests passed.")