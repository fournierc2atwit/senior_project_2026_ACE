import random


class Wheel:
    """American roulette wheel."""

    GREEN_NUMBERS = {0, "00"}
    RED_NUMBERS = {
        1, 3, 5, 7, 9, 12, 14, 16, 18,
        19, 21, 23, 25, 27, 30, 32, 34, 36,
    }
    BLACK_NUMBERS = {
        2, 4, 6, 8, 10, 11, 13, 15, 17,
        20, 22, 24, 26, 28, 29, 31, 33, 35,
    }

    ALL_NUMBERS = [0, "00", *range(1, 37)]
    COLOR_MAP = {
        **{number: "green" for number in GREEN_NUMBERS},
        **{number: "red" for number in RED_NUMBERS},
        **{number: "black" for number in BLACK_NUMBERS},
    }

    def spin(self):
        return random.choice(self.ALL_NUMBERS)

    def get_color(self, number):
        try:
            return self.COLOR_MAP[number]
        except KeyError:
            raise ValueError(f"Invalid roulette number: {number!r}")

    def is_odd(self, number):
        return isinstance(number, int) and number not in self.GREEN_NUMBERS and number % 2 == 1

    def is_even(self, number):
        return isinstance(number, int) and number not in self.GREEN_NUMBERS and number % 2 == 0

    def get_dozen(self, number):
        if number in self.GREEN_NUMBERS:
            return None
        if 1 <= number <= 36:
            return (number - 1) // 12 + 1
        raise ValueError(f"Invalid roulette number: {number!r}")

    def describe(self, number):
        return {
            "number": number,
            "color": self.get_color(number),
            "is_odd": self.is_odd(number),
            "is_even": self.is_even(number),
            "dozen": self.get_dozen(number),
        }


# ----------------------------------------------------------------------
# Quick test — run directly to verify:
# python -m game.roulette.wheel
# ----------------------------------------------------------------------
if __name__ == "__main__":
    print("=== Wheel Tests ===\n")

    wheel = Wheel()

    # Test 1: 38 total pockets
    assert len(wheel.ALL_NUMBERS) == 38
    print(f"Test 1  — Total pockets: {len(wheel.ALL_NUMBERS)} (expected 38): PASS")

    # Test 2: Red + Black + Green covers all numbers exactly once
    all_colored = wheel.RED_NUMBERS | wheel.BLACK_NUMBERS | wheel.GREEN_NUMBERS
    assert all_colored == set(wheel.ALL_NUMBERS)
    assert len(wheel.RED_NUMBERS) == 18
    assert len(wheel.BLACK_NUMBERS) == 18
    assert len(wheel.GREEN_NUMBERS) == 2
    print(f"Test 2  — Color counts: 18 red, 18 black, 2 green: PASS")

    # Test 3: get_color for known numbers
    assert wheel.get_color(1) == "red"
    assert wheel.get_color(2) == "black"
    assert wheel.get_color(0) == "green"
    assert wheel.get_color("00") == "green"
    print(f"Test 3  — get_color() spot checks: PASS")

    # Test 4: odd/even
    assert wheel.is_odd(1) is True
    assert wheel.is_even(1) is False
    assert wheel.is_odd(2) is False
    assert wheel.is_even(2) is True
    assert wheel.is_odd(0) is False
    assert wheel.is_even(0) is False
    assert wheel.is_odd("00") is False
    assert wheel.is_even("00") is False
    print(f"Test 4  — is_odd() / is_even(): PASS")

    # Test 5: dozens
    assert wheel.get_dozen(5) == 1
    assert wheel.get_dozen(12) == 1
    assert wheel.get_dozen(13) == 2
    assert wheel.get_dozen(24) == 2
    assert wheel.get_dozen(25) == 3
    assert wheel.get_dozen(36) == 3
    assert wheel.get_dozen(0) is None
    assert wheel.get_dozen("00") is None
    print(f"Test 5  — get_dozen(): PASS")

    # Test 6: spin returns a valid pocket
    for _ in range(1000):
        result = wheel.spin()
        assert result in wheel.ALL_NUMBERS
    print(f"Test 6  — 1000 spins all return valid pockets: PASS")

    # Test 7: spin distribution sanity check (not a strict statistical test,
    # just confirms we're not always landing on the same number)
    results = [wheel.spin() for _ in range(2000)]
    unique_results = set(results)
    assert len(unique_results) > 20, "Spin results suspiciously non-random"
    print(f"Test 7  — Spin variety: {len(unique_results)} unique numbers in 2000 spins: PASS")

    # Test 8: describe()
    desc = wheel.describe(7)
    assert desc == {"number": 7, "color": "red", "is_odd": True, "is_even": False, "dozen": 1}
    print(f"Test 8  — describe(7) = {desc}: PASS")

    desc_00 = wheel.describe("00")
    assert desc_00 == {"number": "00", "color": "green", "is_odd": False, "is_even": False, "dozen": None}
    print(f"Test 9  — describe('00') = {desc_00}: PASS")

    # Test 10: invalid number raises
    try:
        wheel.get_color(99)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    print("wheel.py: basic checks passed")