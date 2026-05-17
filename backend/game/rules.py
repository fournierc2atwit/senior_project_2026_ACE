class Rules:
    @staticmethod
    def determine_winner(player_hand, dealer_hand):
        if player_hand.is_bust():
            return "lose"

        if dealer_hand.is_bust():
            return "win"

        if player_hand.is_blackjack() and not dealer_hand.is_blackjack():
            return "blackjack"

        if dealer_hand.is_blackjack() and not player_hand.is_blackjack():
            return "lose"

        player_total = player_hand.get_value()
        dealer_total = dealer_hand.get_value()

        if player_total > dealer_total:
            return "win"
        elif player_total < dealer_total:
            return "lose"
        else:
            return "push"

    @staticmethod
    def dealer_should_hit(dealer_hand):
        return dealer_hand.get_value() < 17