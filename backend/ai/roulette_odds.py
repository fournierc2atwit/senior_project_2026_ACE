from math import comb, log
 
POCKETS = 38
GREEN_POCKETS = 2
 
BET_SPECS = {
    "straight": {"payout": 35, "winners": 1,  "label": "Straight (single number)"},
    "color":    {"payout": 1,  "winners": 18, "label": "Color (red / black)"},
    "parity":   {"payout": 1,  "winners": 18, "label": "Parity (odd / even)"},
    "dozen":    {"payout": 2,  "winners": 12, "label": "Dozen (1-12 / 13-24 / 25-36)"},
}
 
VALID_BET_TYPES = set(BET_SPECS)
 
 
def _spec(bet_type):
    if bet_type not in BET_SPECS:
        raise ValueError(
            f"Unknown bet type {bet_type!r}. Use one of: {sorted(VALID_BET_TYPES)}"
        )
    return BET_SPECS[bet_type]
 
def win_probability(bet_type):
    return _spec(bet_type)["winners"] / POCKETS
 
 
def payout_ratio(bet_type):
    return _spec(bet_type)["payout"]
 
 
def expected_value(bet_type, amount=1):
    p = win_probability(bet_type)
    return (p * payout_ratio(bet_type) - (1 - p)) * amount
 
 
def house_edge(bet_type=None):
    if bet_type is None:
        return GREEN_POCKETS / POCKETS
    return -expected_value(bet_type, 1)
 
 
def variance(bet_type, amount=1):
    p = win_probability(bet_type)
    r = payout_ratio(bet_type)
    ev = p * r - (1 - p)
    e_x2 = p * (r ** 2) + (1 - p) * 1
    return (e_x2 - ev ** 2) * (amount ** 2)
 
 
def std_dev(bet_type, amount=1):
    return variance(bet_type, amount) ** 0.5

def expected_loss(amount, spins=1):
    return house_edge() * amount * spins
 
 
def expected_spins_until_broke(bankroll, amount):
    if amount <= 0:
        raise ValueError("amount must be greater than 0")
    per_spin = expected_loss(amount)
    if per_spin <= 0:
        return float("inf")
    return bankroll / per_spin
 
 
def probability_of_profit(bet_type, spins, amount=1):
    p = win_probability(bet_type)
    r = payout_ratio(bet_type)
    threshold = spins / (r + 1)
 
    total = 0.0
    for k in range(spins + 1):
        if k > threshold:
            total += comb(spins, k) * (p ** k) * ((1 - p) ** (spins - k))
    return total
 
 
def probability_of_no_win(bet_type, spins):
    return (1 - win_probability(bet_type)) ** spins
 
def streak_probability(bet_type, length):
    return win_probability(bet_type) ** length
 
 
def probability_after_streak(bet_type, streak_length=0):
    return win_probability(bet_type)
 
 
def martingale_analysis(bankroll, base_bet, bet_type="color"):
    p_win = win_probability(bet_type)
    p_lose = 1 - p_win
 
    steps = 0
    while base_bet * (2 ** (steps + 1) - 1) <= bankroll:
        steps += 1
 
    if steps == 0:
        return {
            "steps": 0,
            "max_loss": 0,
            "bust_probability": 1.0,
            "expected_value": 0.0,
            "affordable": False,
        }
 
    bust_prob = p_lose ** steps
    max_loss = base_bet * (2 ** steps - 1)
    survive_prob = 1 - bust_prob
 
    ev = survive_prob * base_bet - bust_prob * max_loss
 
    return {
        "steps": steps,
        "max_loss": max_loss,
        "bust_probability": bust_prob,
        "win_probability": survive_prob,
        "expected_value": ev,
        "affordable": True,
    }
 
 
def compare_bets(amount=1):
    rows = []
    for bet_type in ("color", "parity", "dozen", "straight"):
        rows.append({
            "bet_type":       bet_type,
            "label":          BET_SPECS[bet_type]["label"],
            "payout":         payout_ratio(bet_type),
            "win_probability": win_probability(bet_type),
            "house_edge":     house_edge(bet_type),
            "expected_value": expected_value(bet_type, amount),
            "std_dev":        std_dev(bet_type, amount),
        })
    return rows
 
 
def all_edges_identical():
    edges = {round(house_edge(bt), 10) for bt in VALID_BET_TYPES}
    return len(edges) == 1
 
 
# ---------------------------------------------------------------------------
# Self-test — run with:  python -m backend.ai.roulette_odds
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== The punchline: same edge, very different ride ===\n")
    print(f"{'bet':10}{'pays':>6}{'p(win)':>10}{'edge':>9}{'EV/$100':>10}{'SD/$100':>10}")
    for row in compare_bets(100):
        print(f"{row['bet_type']:10}{row['payout']:>5}:1"
              f"{row['win_probability']:>10.4f}"
              f"{row['house_edge'] * 100:>8.2f}%"
              f"{row['expected_value']:>10.2f}"
              f"{row['std_dev']:>10.2f}")
 
    print("\n  Every single bet: -5.26%. The wheel does not care what you pick.")
    print("  What changes is the SD column — how violently you get there.\n")
 
    print("=== Probability of being AHEAD after N spins ($100 flat) ===\n")
    print(f"{'spins':>7}{'color':>10}{'dozen':>10}{'straight':>10}")
    for n in (1, 10, 50, 100, 500):
        print(f"{n:>7}"
              f"{probability_of_profit('color', n) * 100:>9.1f}%"
              f"{probability_of_profit('dozen', n) * 100:>9.1f}%"
              f"{probability_of_profit('straight', n) * 100:>9.1f}%")
 
    print("\n=== Bankroll burn: 1000 chips ===\n")
    for amt in (10, 25, 50, 100):
        print(f"  ${amt:>3}/spin -> lose ~${expected_loss(amt):.2f}/spin, "
              f"~{expected_spins_until_broke(1000, amt):.0f} spins expected")
 
    print("\n=== Martingale on a 1000 bankroll, $25 base ===\n")
    m = martingale_analysis(1000, 25)
    print(f"  You can afford {m['steps']} doublings (max ladder loss ${m['max_loss']}).")
    print(f"  You bank $25 about {m['win_probability'] * 100:.1f}% of the time,")
    print(f"  and lose ${m['max_loss']} about {m['bust_probability'] * 100:.1f}% of the time.")
    print(f"  Expected value: ${m['expected_value']:.2f} per ladder. Still negative.\n")
 
    print("=== Gambler's fallacy, in numbers ===\n")
    print(f"  P(6 reds in a row, stated up front) = "
          f"{streak_probability('color', 6) * 100:.2f}%")
    print(f"  P(red on the next spin | 6 reds already) = "
          f"{probability_after_streak('color', 6) * 100:.2f}%")
    print("  The first number is small. The second is just 18/38, forever.\n")
 
    # ---- assertions ----
    # The headline claim: every bet type carries the identical edge.
    assert all_edges_identical()
    for bt in VALID_BET_TYPES:
        assert abs(house_edge(bt) - 2 / 38) < 1e-12, bt
        assert abs(expected_value(bt, 100) + 100 * 2 / 38) < 1e-9, bt
 
    # Probabilities line up with the wheel.
    assert win_probability("straight") == 1 / 38
    assert win_probability("color") == 18 / 38
    assert win_probability("dozen") == 12 / 38
 
    # Variance is where the bets actually differ.
    assert std_dev("straight") > std_dev("dozen") > std_dev("color")
    assert abs(std_dev("color") - 0.9986) < 1e-3
    assert abs(std_dev("straight") - 5.7626) < 1e-3
 
    # Bankroll math
    assert abs(expected_loss(100, 10) - 100 * 10 * 2 / 38) < 1e-9
    # 1000 bankroll at $25/spin: 25 * 0.0526 = $1.32 lost per spin -> ~760 spins.
    # (Contrast slots, whose 16.2% edge burns the same bankroll in ~247 spins.)
    assert 750 < expected_spins_until_broke(1000, 25) < 770
 
    # A single spin: "ahead" just means "won", so this is the win probability.
    assert abs(probability_of_profit("color", 1) - 18 / 38) < 1e-12
    assert abs(probability_of_profit("straight", 1) - 1 / 38) < 1e-12
    # Over many spins the even-money grinder is usually behind...
    assert probability_of_profit("color", 500) < 0.35
    # ...but the straight bettor keeps a fatter tail of finishing up.
    assert probability_of_profit("straight", 500) > probability_of_profit("color", 500)
 
    # The wheel has no memory: the streak length must not change the answer.
    assert probability_after_streak("color", 0) == probability_after_streak("color", 10)
 
    # Martingale never escapes the edge.
    m = martingale_analysis(1000, 25)
    assert m["steps"] == 5 and m["max_loss"] == 775
    assert m["expected_value"] < 0
    assert martingale_analysis(10, 25)["affordable"] is False
 
    print("roulette_odds.py self-checks passed.")