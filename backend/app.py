from backend.game.deck import Deck
from backend.game.player import Player
from backend.game.hand import Hand
from backend.game.rules import Rules

# Display the current hands for both the player and dealer
def show_hands(player, dealer, hide_dealer=True):
    print()
    if hide_dealer:
        print("Dealer:", dealer.hand.short_names(hide_second=True))
    else:
        print("Dealer:", dealer.hand)

    print("Player:", player.hand)
    print()

# Run one full round of blackjack
def play_round(player, deck):
    # Create dealer player object
    dealer = Player("Dealer")

    # Reset hands before starting a new round
    player.new_hand()
    dealer.new_hand()

    # player chooses bet amount for the round
    while True:
        try:
            bet = int(input("Enter your bet amount: "))
            if player.place_bet(bet):
                break
        except ValueError:
            print("Please enter a valid number.")

    # Initial deal
    player.hand.add_card(deck.deal())
    dealer.hand.add_card(deck.deal())
    player.hand.add_card(deck.deal())
    dealer.hand.add_card(deck.deal())

    show_hands(player, dealer, hide_dealer=True)

    # Player turn loop
    while not player.hand.is_bust():
        choice = input("Hit or stand? ").lower().strip()

        if choice == "hit":
            # Add another card to player's hand
            player.hand.add_card(deck.deal())
            show_hands(player, dealer, hide_dealer=True)
        elif choice == "stand":
            break
        else:
            print("Type hit or stand.")

    if player.hand.is_bust():
        print("You busted. You lose.")
        player.lose()
        return

    # Dealer turn starts after player stands
    print("Dealer reveals hand:")
    show_hands(player, dealer, hide_dealer=False)

    # Dealer must hit until reaching at least 17
    while Rules.dealer_should_hit(dealer.hand):
        print("Dealer hits.")
        dealer.hand.add_card(deck.deal())
        show_hands(player, dealer, hide_dealer=False)
    # Determine winner after both turns finish
    result = Rules.determine_winner(player.hand, dealer.hand)

    if result == "win":
        print("You win!")
        player.win()
    elif result == "blackjack":
        print("Blackjack! You win!")
        player.win(blackjack=True)
    elif result == "push":
        print("Push. You tied.")
        player.push()
    else:
        print("You lose.")
        player.lose()
        print(f"Current chips: {player.chips}")

# Main game loop
def main():
    deck = Deck()
    player = Player("Player")

    print("Welcome to A.C.E. Blackjack!")

    # Continue playing while player still has chips
    while player.chips > 0:
        print(f"\nChips: {player.chips}")
        play_round(player, deck)

        again = input("Play again? yes/no: ").lower().strip()
        if again != "yes":
            break

    print("Game over.")
    print(f"Final chips: {player.chips}")

if __name__ == "__main__":
    main()