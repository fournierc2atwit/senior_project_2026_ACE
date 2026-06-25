import random


class SlotMachine:
    """
    Simple slot machine reel generator.

    Uses weighted symbols so common symbols appear more often
    and rare symbols like seven appear less often.
    """

    SYMBOL_WEIGHTS = {
        "cherry": 30,
        "lemon": 25,
        "bell": 20,
        "star": 15,
        "diamond": 8,
        "seven": 2,
    }

    def spin(self):
        symbols = list(self.SYMBOL_WEIGHTS.keys())
        weights = list(self.SYMBOL_WEIGHTS.values())

        return random.choices(symbols, weights=weights, k=3)


        