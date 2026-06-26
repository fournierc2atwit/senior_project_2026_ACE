class Rules:
    """
    Validates slot bets and calculates slot payouts.
    """

    ALLOWED_BETS = {25, 50, 100, 250}

    PAYOUTS = {
        "cherry": 3,
        "lemon": 4,
        "bell": 5,
        "star": 8,
        "diamond": 12,
        "seven": 25,
    }

    @staticmethod
    def validate_bet(amount, chips):
        if amount <= 0:
            raise ValueError("Bet amount must be greater than 0.")

        if amount not in SlotRules.ALLOWED_BETS:
            raise ValueError("Invalid slot bet amount.")

        if amount > chips:
            raise ValueError("Not enough chips.")

    @staticmethod
    def calculate_payout(reels, amount):
        # Three matching symbols
        if reels[0] == reels[1] == reels[2]:
            symbol = reels[0]
            multiplier = SlotRules.PAYOUTS[symbol]
            payout = amount * multiplier

            return {
                "won": True,
                "result": "three_match",
                "multiplier": multiplier,
                "payout": payout,
                "total_return": amount + payout,
                "message": f"Three {symbol}s! You won ${payout}.",
            }

        # Small win for two cherries
        if reels.count("cherry") == 2:
            payout = amount * 2

            return {
                "won": True,
                "result": "two_cherries",
                "multiplier": 2,
                "payout": payout,
                "total_return": amount + payout,
                "message": f"Two cherries! You won ${payout}.",
            }

        return {
            "won": False,
            "result": "lose",
            "multiplier": 0,
            "payout": 0,
            "total_return": 0,
            "message": "No match. You lose.",
        }

    @staticmethod
    def resolve_spin(machine, amount):
        reels = machine.spin()
        outcome = SlotRules.calculate_payout(reels, amount)

        return {
            "reels": reels,
            "won": outcome["won"],
            "result": outcome["result"],
            "multiplier": outcome["multiplier"],
            "payout": outcome["payout"],
            "total_return": outcome["total_return"],
            "message": outcome["message"],
        }