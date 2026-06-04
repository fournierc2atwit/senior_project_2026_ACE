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
        self.wins = 0
        self.losses = 0
        self.pushes = 0
        self.bankrupts = 0

    def place_bet(self, amount):
        # Place a bet for the current round
        # Deducts the bet amount from player's chips
        # Returns True if bet is successfully placed, False if insufficient chips
        if amount <= 0:
            raise ValueError("Bet amount must be positive")
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
        self.wins += 1
        # Player wins the round
        # Standard win pays 1:1, blackjack pays 3:2
        if blackjack:
            payout = int(self.bet * 1.5)
        else:
            payout = self.bet
        self.chips += self.bet + payout  # Return original bet + winnings
        self.bet = 0
    def lose(self):
        self.losses += 1
        # Player loses the round, bet is already deducted
        self.bet = 0
    def push(self):
        self.pushes += 1
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
    
