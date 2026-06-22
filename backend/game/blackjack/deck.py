import random
from backend.game.blackjack.card import Card

class Deck:

    """
    Goals:
    - Create a standard 52-card deck
    - Shuffle the deck
    - Deal cards from the top of the deck one at a time
    - Automatically reshuffle when the deck runs low on cards
    """

    RESHUFFLE_THRESHOLD = 15  # When to reshuffle the deck

    def __init__(self):
        self.cards = []
        self.dealt = []
        self.build()
        self.shuffle()

    def build(self):
        self.cards = [
            Card(suit,rank)
            for suit in Card.SUITS
            for rank in Card.RANKS
        ]

    def shuffle(self):
        self.cards.extend(self.dealt)
        self.dealt = []
        random.shuffle(self.cards)

    def deal(self):
        if len(self.cards) <= self.RESHUFFLE_THRESHOLD:
            print("Reshuffling...")
            self.shuffle()

        card = self.cards.pop()
        self.dealt.append(card)
        return card
    
    def cards_remaining(self):
        return len(self.cards)
    
    def cards_dealt(self):
        return len(self.dealt)
    
    def __len__(self):
        return len(self.cards)
    
    def __repr__(self):
        return f"Deck(remaining={self.cards_remaining()}, dealt={self.cards_dealt()})"
    
# Test cases 
# # python -m game.deck
# ----------------------------------------------------------------------
if __name__ == "__main__":
    print("=== Deck Tests ===\n")
 
    deck = Deck()
 
    # Test 1: Full deck size
    print(f"Test 1 — Full deck size: {len(deck)} cards (expected 52)")
    assert len(deck) == 52, "Deck should have 52 cards"
 
    # Test 2: All 52 cards are unique
    short_names = [c.short_name() for c in deck.cards]
    assert len(short_names) == len(set(short_names)), "All cards should be unique"
    print(f"Test 2 — All cards unique: PASS")
 
    # Test 3: Deal a card
    card = deck.deal()
    print(f"Test 3 — Dealt card: {card}  |  Remaining: {len(deck)} (expected 51)")
    assert len(deck) == 51, "Deck should have 51 cards after one deal"
 
    # Test 4: Deal all cards and confirm count
    while len(deck) > 0:
        deck.deal()
    print(f"Test 4 — Dealt all cards. Dealt pile: {deck.cards_dealt()} (expected 52)")
    assert deck.cards_dealt() == 52
 
    # Test 5: Auto-reshuffle on next deal after deck is empty
    print(f"Test 5 — Auto-reshuffle on empty deck...")
    card = deck.deal()
    print(f"  Dealt after reshuffle: {card}  |  Remaining: {len(deck)}")
    assert len(deck) > 0, "Deck should have reshuffled"
 
    # Test 6: Manual shuffle resets dealt pile
    deck2 = Deck()
    for _ in range(10):
        deck2.deal()
    print(f"Test 6 — Before manual shuffle: remaining={deck2.cards_remaining()}, dealt={deck2.cards_dealt()}")
    deck2.shuffle()
    print(f"         After manual shuffle:  remaining={deck2.cards_remaining()}, dealt={deck2.cards_dealt()} (expected 52, 0)")
    assert deck2.cards_remaining() == 52
    assert deck2.cards_dealt() == 0
 
    # Test 7: Confirm deck is shuffled (not in build order)
    deck3 = Deck()
    first_five = [c.short_name() for c in deck3.cards[-5:]]
    print(f"Test 7 — First 5 cards dealt: {first_five} (should not always be 2♥ 3♥ 4♥ 5♥ 6♥)")
 
    print("\nAll tests passed.") 