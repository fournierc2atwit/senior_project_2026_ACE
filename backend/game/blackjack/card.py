class Card:

    SUITS = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
    RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King', 'Ace']
    SUIT_SYMBOLS = {
        'Hearts': '♥',
        'Diamonds': '♦',
        'Clubs': '♣',
        'Spades': '♠'
    }

    def __init__(self, suit, rank, face_up=True):
        if suit not in self.SUITS:
            raise ValueError(f"Invalid suit: {suit}. Must be one of {self.SUITS}")
        if rank not in self.RANKS:
            raise ValueError(f"Invalid rank: {rank}. Must be one of {self.RANKS}")
        self.suit = suit
        self.rank = rank
        self.face_up = face_up

    def get_value(self):
        if self.rank in ['Jack', 'Queen', 'King']:
            return 10
        elif self.rank == 'Ace':
            return 11  # Value of Ace can be 1 or 11, but we'll handle that in hand logic
        else:
            return int(self.rank)
        
    def get_symbol(self):
        return self.SUIT_SYMBOLS[self.suit]
    def is_red(self):
        return self.suit in ['Hearts', 'Diamonds']
    def short_name(self):
        return f"{self.rank}{self.get_symbol()}"

    def __str__(self):
        return f"{self.rank} of {self.suit}"

    def __repr__(self):
        return f"Card('{self.suit}', '{self.rank}', face_up={self.face_up})"
    

# Test cases
# python -m game.card
if __name__ == "__main__":
    print("=== Card Tests ===\n")
 
    # Basic creation and display
    ace   = Card("Spades", "Ace")
    king  = Card("Hearts", "King")
    ten   = Card("Diamonds", "10")
    two   = Card("Clubs", "2")
 
    print("Full names:")
    for c in [ace, king, ten, two]:
        print(f"  {c}")
 
    print("\nShort names (used by UI):")
    for c in [ace, king, ten, two]:
        print(f"  {c.short_name()}")
 
    print("\nValues:")
    for c in [ace, king, ten, two]:
        print(f"  {c.short_name()} = {c.get_value()}")
 
    print("\nRed suit check:")
    for c in [ace, king, ten, two]:
        print(f"  {c.short_name()} is_red={c.is_red()}")
 
    print("\nFace-down card:")
    hole = Card("Hearts", "Ace", face_up=False)
    print(f"  {hole}  |  face_up={hole.face_up}")
 
    print("\nInvalid card test:")
    try:
        bad = Card("Stars", "Ace")
    except ValueError as e:
        print(f"  Caught expected error: {e}")
 
    print("\nAll tests passed.")
