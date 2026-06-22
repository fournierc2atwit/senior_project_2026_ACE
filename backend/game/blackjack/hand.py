from backend.game.blackjack.card import Card
class Hand:

    # Goals:
    # - Store list of Card objects
    # - Calculate total value of hand (with Ace logic)
    # - Determine different hand states (busted, blackjack, etc.)
    # - Provide display-friendly representation of hand (for UI)

    def __init__(self):
        self.cards = []

    def add_card(self, card):
        # Add a Card object to the hand
        if not isinstance(card, Card):
            raise ValueError(f"Must add a Card object to the hand")
        self.cards.append(card)

    def clear(self):
        # Clear all cards from the hand
        self.cards = []
    
    def get_value(self):
        total = 0
        aces = 0
        for card in self.cards:
            total += card.get_value()
            if card.rank == "Ace":
                aces += 1
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        return total
    
    def is_soft(self):
        # Returns True if hand is soft (contains an Ace counted as 11), False otherwise
        total = sum(card.get_value() for card in self.cards)
        aces  = sum(1 for card in self.cards if card.rank == "Ace")
        
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        return aces > 0  # If we still have an Ace counted as 11, it's a soft hand
    
    def is_bust(self):
        # Returns True if hand value exceeds 21
        return self.get_value() > 21
    
    def is_blackjack(self):
        # Returns True if hand is a blackjack (exactly 2 cards: an Ace and a 10-value card)
        return len(self.cards) == 2 and self.get_value() == 21

    def is_pair(self):
        return len(self.cards) == 2 and self.cards[0].rank == self.cards[1].rank
    
    def card_count(self):
        # Returns the number of cards in the hand
        return len(self.cards)
    
    # For UI: Return a string representation of the hand (e.g. "A♠ 10♦")
    def short_names(self, hide_second=False):
        names = [card.short_name() for card in self.cards]

        if hide_second and len(names) >= 2:
            names[1] = "?"

        return names
        
    def __str__(self):
        return f"{' '.join(self.short_names())} (Total: {self.get_value()})"
    
    def __len__(self):
        return len(self.cards)
    

# Test cases
if __name__ == "__main__":
    from backend.game.blackjack.deck import Deck
 
    print("=== Hand Tests ===\n")
 
    def make_hand(*pairs):
        h = Hand()
        for suit, rank in pairs:
            h.add_card(Card(suit, rank))
        return h
 
    # Test 1: Basic total
    h = make_hand(("Spades", "K"), ("Hearts", "7"))
    assert h.get_value() == 17
    print(f"Test 1  — K + 7          = {h.get_value()} (expected 17): PASS")
 
    # Test 2: Ace as 11
    h = make_hand(("Spades", "A"), ("Hearts", "9"))
    assert h.get_value() == 20
    print(f"Test 2  — A + 9          = {h.get_value()} (expected 20): PASS")
 
    # Test 3: Ace drops to 1
    h = make_hand(("Spades", "A"), ("Hearts", "9"), ("Clubs", "5"))
    assert h.get_value() == 15
    print(f"Test 3  — A + 9 + 5      = {h.get_value()} (expected 15): PASS")
 
    # Test 4: Two Aces
    h = make_hand(("Spades", "A"), ("Hearts", "A"))
    assert h.get_value() == 12
    print(f"Test 4  — A + A          = {h.get_value()} (expected 12): PASS")
 
    # Test 5: Three Aces
    h = make_hand(("Spades", "A"), ("Hearts", "A"), ("Clubs", "A"))
    assert h.get_value() == 13
    print(f"Test 5  — A + A + A      = {h.get_value()} (expected 13): PASS")
 
    # Test 6: Blackjack
    h = make_hand(("Spades", "A"), ("Hearts", "K"))
    assert h.is_blackjack() and not h.is_bust()
    print(f"Test 6  — A + K          is_blackjack={h.is_blackjack()} (expected True): PASS")
 
    # Test 7: 3-card 21 is not Blackjack
    h = make_hand(("Spades", "7"), ("Hearts", "7"), ("Clubs", "7"))
    assert h.get_value() == 21 and not h.is_blackjack()
    print(f"Test 7  — 7 + 7 + 7 = 21 is_blackjack={h.is_blackjack()} (expected False): PASS")
 
    # Test 8: Bust
    h = make_hand(("Spades", "K"), ("Hearts", "Q"), ("Clubs", "5"))
    assert h.is_bust()
    print(f"Test 8  — K + Q + 5      = {h.get_value()}, is_bust={h.is_bust()} (expected True): PASS")
 
    # Test 9: Soft hand
    h = make_hand(("Spades", "A"), ("Hearts", "7"))
    assert h.is_soft()
    print(f"Test 9  — A + 7          is_soft={h.is_soft()} (expected True): PASS")
 
    # Test 10: Hard hand after Ace reduction
    h = make_hand(("Spades", "A"), ("Hearts", "7"), ("Clubs", "8"))
    assert not h.is_soft()
    print(f"Test 10 — A + 7 + 8      is_soft={h.is_soft()} (expected False): PASS")
 
    # Test 11: is_pair
    h = make_hand(("Spades", "8"), ("Hearts", "8"))
    assert h.is_pair()
    print(f"Test 11 — 8 + 8          is_pair={h.is_pair()} (expected True): PASS")
 
    # Test 12: short_names with hidden hole card
    h = make_hand(("Spades", "A"), ("Hearts", "K"))
    names = h.short_names(hide_second=True)
    assert names[1] == "?"
    print(f"Test 12 — hidden hole    {names} (expected ['A♠', '?']): PASS")
 
    # Test 13: clear()
    h = make_hand(("Spades", "K"), ("Hearts", "7"))
    h.clear()
    assert len(h) == 0
    print(f"Test 13 — clear()        len={len(h)} (expected 0): PASS")
 
    # Test 14: deal from real deck
    print(f"\nTest 14 — Deal 2 cards from a real deck:")
    deck = Deck()
    h = Hand()
    h.add_card(deck.deal())
    h.add_card(deck.deal())
    print(f"  {h}")
    assert len(h) == 2
    print(f"  len={len(h)} (expected 2): PASS")
 
    print("\nAll tests passed.")