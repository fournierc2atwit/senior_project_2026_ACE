class Rules:
    """
    Validates roulette bets and calculates payouts.

    Responsibilities:
        - Confirm a bet is well-formed for its bet type
        - Determine whether a bet wins against a spun number
        - Calculate the payout for winning bets

    Supported bet types (v1):
        "straight" — bet on a single number (0, "00", or 1-36). Pays 35:1.
        "color"    — bet on "red" or "black". Pays 1:1.
        "parity"   — bet on "odd" or "even". Pays 1:1.
        "dozen"    — bet on 1, 2, or 3 (1-12, 13-24, 25-36). Pays 2:1.

    All payout ratios represent winnings ONLY (not including the
    returned original bet). Total returned to the player on a win
    is bet_amount + payout.
    """

    PAYOUTS = {
        "straight": 35,
        "color":     1,
        "parity":    1,
        "dozen":     2,
    }

    VALID_BET_TYPES = set(PAYOUTS.keys())
    VALID_COLORS    = {"red", "black"}
    VALID_PARITIES  = {"odd", "even"}
    VALID_DOZENS    = {1, 2, 3}

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def validate_bet(bet_type, bet_value, wheel):
        """
        Confirms a bet is well-formed before it is placed.

        Args:
            bet_type  (str): One of "straight", "color", "parity", "dozen".
            bet_value      : The specific value being bet on.
            wheel    (Wheel): A Wheel instance, used to validate straight bets.

        Raises:
            ValueError: If the bet type or value is invalid.
        """
        if bet_type not in Rules.VALID_BET_TYPES:
            raise ValueError(
                f"Invalid bet type: {bet_type!r}. "
                f"Must be one of {sorted(Rules.VALID_BET_TYPES)}"
            )

        if bet_type == "straight":
            if bet_value not in wheel.ALL_NUMBERS:
                raise ValueError(
                    f"Invalid straight bet value: {bet_value!r}. "
                    f"Must be 0, '00', or 1-36."
                )

        elif bet_type == "color":
            if bet_value not in Rules.VALID_COLORS:
                raise ValueError(
                    f"Invalid color bet value: {bet_value!r}. "
                    f"Must be 'red' or 'black'."
                )

        elif bet_type == "parity":
            if bet_value not in Rules.VALID_PARITIES:
                raise ValueError(
                    f"Invalid parity bet value: {bet_value!r}. "
                    f"Must be 'odd' or 'even'."
                )

        elif bet_type == "dozen":
            if bet_value not in Rules.VALID_DOZENS:
                raise ValueError(
                    f"Invalid dozen bet value: {bet_value!r}. "
                    f"Must be 1, 2, or 3."
                )

    # ------------------------------------------------------------------
    # Win determination
    # ------------------------------------------------------------------

    @staticmethod
    def is_winning_bet(bet_type, bet_value, result_description):
        """
        Determines whether a bet wins against a spun result.

        Args:
            bet_type  (str): One of "straight", "color", "parity", "dozen".
            bet_value      : The specific value bet on.
            result_description (dict): Output of Wheel.describe(number).

        Returns:
            bool: True if the bet wins, False otherwise.
        """
        if bet_type == "straight":
            return bet_value == result_description["number"]

        if bet_type == "color":
            return bet_value == result_description["color"]

        if bet_type == "parity":
            if bet_value == "odd":
                return result_description["is_odd"]
            if bet_value == "even":
                return result_description["is_even"]
            return False

        if bet_type == "dozen":
            return bet_value == result_description["dozen"]

        return False

    # ------------------------------------------------------------------
    # Payout calculation
    # ------------------------------------------------------------------

    @staticmethod
    def calculate_payout(bet_type, bet_amount, won):
        """
        Calculates the payout for a resolved bet.

        Args:
            bet_type   (str) : One of "straight", "color", "parity", "dozen".
            bet_amount (int) : The amount wagered.
            won        (bool): Whether the bet won.

        Returns:
            dict: {
                "won":           bool,
                "payout":        int,  # winnings only, not including original bet
                "total_return":  int,  # bet_amount + payout if won, 0 if lost
            }
        """
        if not won:
            return {"won": False, "payout": 0, "total_return": 0}

        ratio  = Rules.PAYOUTS[bet_type]
        payout = bet_amount * ratio

        return {
            "won":          True,
            "payout":       payout,
            "total_return": bet_amount + payout,
        }

    # ------------------------------------------------------------------
    # Convenience: resolve a full bet in one call
    # ------------------------------------------------------------------

    @staticmethod
    def resolve_bet(bet_type, bet_value, bet_amount, wheel, number):
        """
        Runs the full bet resolution sequence for a single spin result:
            1. Validate the bet
            2. Describe the winning number
            3. Determine if the bet won
            4. Calculate the payout

        Args:
            bet_type   (str)  : One of "straight", "color", "parity", "dozen".
            bet_value         : The specific value bet on.
            bet_amount (int)  : The amount wagered.
            wheel      (Wheel): A Wheel instance.
            number     (int|str): The number that was already spun.

        Returns:
            dict: {
                "number":        int | str,
                "color":         str,
                "won":           bool,
                "payout":        int,
                "total_return":  int,
            }
        """
        Rules.validate_bet(bet_type, bet_value, wheel)

        description = wheel.describe(number)
        won         = Rules.is_winning_bet(bet_type, bet_value, description)
        outcome     = Rules.calculate_payout(bet_type, bet_amount, won)

        return {
            "number":       description["number"],
            "color":        description["color"],
            "won":          outcome["won"],
            "payout":       outcome["payout"],
            "total_return": outcome["total_return"],
        }


# ----------------------------------------------------------------------
# Quick test — run directly to verify:
# python -m game.roulette.rules
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        from game.roulette.wheel import Wheel
    except ImportError:
        from backend.game.roulette.wheel import Wheel

    print("=== Rules Tests ===\n")

    wheel = Wheel()

    # Test 1: Straight bet win
    result = Rules.resolve_bet("straight", 7, 10, wheel, number=7)
    assert result["won"] is True
    assert result["payout"] == 350          # 10 * 35
    assert result["total_return"] == 360    # 350 + 10
    print(f"Test 1  — Straight win on 7      payout={result['payout']} (expected 350): PASS")

    # Test 2: Straight bet loss
    result = Rules.resolve_bet("straight", 7, 10, wheel, number=8)
    assert result["won"] is False
    assert result["payout"] == 0
    assert result["total_return"] == 0
    print(f"Test 2  — Straight loss          payout={result['payout']} (expected 0): PASS")

    # Test 3: Color bet win
    result = Rules.resolve_bet("color", "red", 50, wheel, number=1)  # 1 is red
    assert result["won"] is True
    assert result["payout"] == 50           # 1:1
    assert result["total_return"] == 100
    print(f"Test 3  — Color win (red on 1)   payout={result['payout']} (expected 50): PASS")

    # Test 4: Color bet loss on green
    result = Rules.resolve_bet("color", "red", 50, wheel, number=0)
    assert result["won"] is False
    print(f"Test 4  — Color loss on 0 (green): PASS")

    # Test 5: Parity bet win
    result = Rules.resolve_bet("parity", "odd", 20, wheel, number=3)
    assert result["won"] is True
    assert result["payout"] == 20
    print(f"Test 5  — Parity win (odd on 3)  payout={result['payout']} (expected 20): PASS")

    # Test 6: Parity bet loss on 0
    result = Rules.resolve_bet("parity", "odd", 20, wheel, number=0)
    assert result["won"] is False
    print(f"Test 6  — Parity loss on 0 (neither odd nor even): PASS")

    # Test 7: Dozen bet win
    result = Rules.resolve_bet("dozen", 1, 30, wheel, number=5)  # 5 is in dozen 1
    assert result["won"] is True
    assert result["payout"] == 60           # 30 * 2
    print(f"Test 7  — Dozen win (1st dozen on 5) payout={result['payout']} (expected 60): PASS")

    # Test 8: Dozen bet loss on 00
    result = Rules.resolve_bet("dozen", 1, 30, wheel, number="00")
    assert result["won"] is False
    print(f"Test 8  — Dozen loss on 00: PASS")

    # Test 9: Straight bet on "00" wins correctly
    result = Rules.resolve_bet("straight", "00", 10, wheel, number="00")
    assert result["won"] is True
    assert result["payout"] == 350
    print(f"Test 9  — Straight win on '00'   payout={result['payout']} (expected 350): PASS")

    # Test 10: Invalid bet type raises
    try:
        Rules.validate_bet("invalid_type", 5, wheel)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"Test 10 — Invalid bet type raises: PASS ({e})")

    # Test 11: Invalid straight bet value raises
    try:
        Rules.validate_bet("straight", 99, wheel)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"Test 11 — Invalid straight value raises: PASS ({e})")

    # Test 12: Invalid color value raises
    try:
        Rules.validate_bet("color", "green", wheel)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"Test 12 — Invalid color value raises: PASS ({e})")

    # Test 13: Invalid dozen value raises
    try:
        Rules.validate_bet("dozen", 4, wheel)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"Test 13 — Invalid dozen value raises: PASS ({e})")

    # Test 14: calculate_payout in isolation
    win_result  = Rules.calculate_payout("color", 100, won=True)
    lose_result = Rules.calculate_payout("color", 100, won=False)
    assert win_result  == {"won": True, "payout": 100, "total_return": 200}
    assert lose_result == {"won": False, "payout": 0, "total_return": 0}
    print(f"Test 14 — calculate_payout() isolated checks: PASS")

    print("\nAll tests passed.")