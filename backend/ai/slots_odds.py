from itertools import product
 
from backend.game.slots.machine import SlotMachine
from backend.game.slots.rules import Rules as SlotRules
 
SYMBOL_WEIGHTS = dict(SlotMachine.SYMBOL_WEIGHTS)
PAYOUTS = dict(SlotRules.PAYOUTS)
ALLOWED_BETS = sorted(SlotRules.ALLOWED_BETS)
 
REELS = 3
TOTAL_WEIGHT = sum(SYMBOL_WEIGHTS.values())
 
TWO_CHERRY_SYMBOL = "cherry"
TWO_CHERRY_MULTIPLIER = 2
 
REAL_SLOT_RTP_LOW = 0.88
REAL_SLOT_RTP_HIGH = 0.96
 
 
def symbol_probability(symbol):
    if symbol not in SYMBOL_WEIGHTS:
        raise ValueError(f"Unknown symbol {symbol!r}. "
                         f"Known: {sorted(SYMBOL_WEIGHTS)}")
    return SYMBOL_WEIGHTS[symbol] / TOTAL_WEIGHT
 
 
def _classify(reels):
    if reels[0] == reels[1] == reels[2]:
        return f"three_{reels[0]}", PAYOUTS[reels[0]]
    if reels.count(TWO_CHERRY_SYMBOL) == 2:
        return "two_cherries", TWO_CHERRY_MULTIPLIER
    return "lose", None
 
 
def outcome_table():
    buckets = {}
    for combo in product(SYMBOL_WEIGHTS, repeat=REELS):
        p = 1.0
        for symbol in combo:
            p *= symbol_probability(symbol)
        name, mult = _classify(list(combo))
        if name not in buckets:
            buckets[name] = {"outcome": name, "multiplier": mult, "probability": 0.0}
        buckets[name]["probability"] += p
 
    rows = []
    for row in buckets.values():
        mult = row["multiplier"]
        row["return_contribution"] = (
            row["probability"] * (1 + mult) if mult is not None else 0.0
        )
        rows.append(row)
 
    rows.sort(key=lambda r: (r["multiplier"] is None,
                             -(r["multiplier"] or 0)))
    return rows
 
_TABLE = outcome_table()
_WINNERS = [r for r in _TABLE if r["multiplier"] is not None]
 
 
def three_match_probability(symbol):
    return symbol_probability(symbol) ** REELS
 
 
def two_cherry_probability():
    p = symbol_probability(TWO_CHERRY_SYMBOL)
    return 3 * (p ** 2) * (1 - p)
 
 
def hit_frequency():
    return sum(r["probability"] for r in _WINNERS)
 
 
def rtp():
    return sum(r["return_contribution"] for r in _TABLE)
 
 
def house_edge():
    return 1 - rtp()
 
 
def expected_value(amount=1):
    return -house_edge() * amount
 
 
def variance(amount=1):
    ev = expected_value(1)
    e_x2 = 0.0
    for row in _TABLE:
        net = row["multiplier"] if row["multiplier"] is not None else -1
        e_x2 += row["probability"] * (net ** 2)
    return (e_x2 - ev ** 2) * (amount ** 2)
 
 
def std_dev(amount=1):
    return variance(amount) ** 0.5
 
 
def rtp_is_bet_independent():
    returns = set()
    for bet in ALLOWED_BETS:
        total = sum(r["probability"] * (1 + r["multiplier"]) * bet
                    for r in _WINNERS)
        returns.add(round(total / bet, 12))
    return len(returns) == 1
 
def expected_loss(amount, spins=1):
    return house_edge() * amount * spins
 
 
def expected_spins_until_broke(bankroll, amount):
    if amount <= 0:
        raise ValueError("amount must be greater than 0")
    per_spin = expected_loss(amount)
    if per_spin <= 0:
        return float("inf")
    return bankroll / per_spin
 
 
def probability_of_no_win(spins):
    return (1 - hit_frequency()) ** spins
 
 
def probability_of_hitting_in(symbol, spins):
    p = three_match_probability(symbol)
    return 1 - (1 - p) ** spins
 
 
def spins_for_even_odds(symbol):
    from math import log
    p = three_match_probability(symbol)
    if p <= 0:
        return float("inf")
    return log(0.5) / log(1 - p)
 
 
def jackpot_symbol():
    return max(PAYOUTS, key=lambda s: PAYOUTS[s])
 

# ---------------------------------------------------------------------------
# Self-test — run with:  python -m backend.ai.slots_odds
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== The machine, enumerated exactly (all 216 combinations) ===\n")
    print(f"{'outcome':16}{'probability':>14}{'pays':>7}{'RTP share':>12}")
    for row in _TABLE:
        mult = row["multiplier"]
        pays = "—" if mult is None else f"{mult}x"
        print(f"{row['outcome']:16}{row['probability']:>14.6f}{pays:>7}"
              f"{row['return_contribution']:>12.4f}")
 
    print(f"\n  hit frequency : {hit_frequency() * 100:.2f}%  "
          f"(something lands ~1 spin in {1 / hit_frequency():.1f})")
    print(f"  RTP           : {rtp() * 100:.2f}%")
    print(f"  house edge    : {house_edge() * 100:.2f}%")
    print(f"  swing (SD)    : {std_dev(1):.2f} per unit staked")
 
    jp = jackpot_symbol()
    print(f"\n  jackpot       : three {jp}s, pays {PAYOUTS[jp]}x")
    print(f"  odds          : 1 in {1 / three_match_probability(jp):,.0f} spins")
    print(f"  coin-flip at  : {spins_for_even_odds(jp):,.0f} spins "
          f"(before it's more likely than not)")
 
    print("\n=== Does betting more help? ===\n")
    for bet in ALLOWED_BETS:
        print(f"  ${bet:>3}/spin -> RTP {rtp() * 100:.2f}%, "
              f"lose ~${expected_loss(bet):.2f}/spin, "
              f"~{expected_spins_until_broke(1000, bet):.0f} spins from 1000 chips")
    print("\n  Identical RTP at every tier. Bet size buys speed, not value.\n")
 
    print("=== How this machine compares ===\n")
    print(f"  this machine       : {rtp() * 100:.2f}% RTP  "
          f"({house_edge() * 100:.2f}% edge)")
    print(f"  the project's own roulette : 94.74% RTP  (5.26% edge)")
    print(f"  a real casino slot : {REAL_SLOT_RTP_LOW * 100:.0f}-"
          f"{REAL_SLOT_RTP_HIGH * 100:.0f}% RTP")
    print("\n  NOTE FOR THE TEAM: at 83.84% this machine is harsher than a real")
    print("  slot floor. That's a design choice, not a bug — but it's worth")
    print("  making on purpose. Raising the cherry weight or the two-cherry")
    print("  multiplier is the quickest lever on RTP.\n")
 
    # ---- assertions ----
    # Probabilities must form a valid distribution over the 216 combinations.
    total_p = sum(r["probability"] for r in _TABLE)
    assert abs(total_p - 1.0) < 1e-12, total_p
 
    # Exact values for the machine as currently tuned. If someone retunes it,
    # these will fail loudly — which is the point: the team should SEE the RTP
    # move, not discover it in production.
    assert TOTAL_WEIGHT == 100
    assert abs(symbol_probability("cherry") - 0.30) < 1e-12
    assert abs(symbol_probability("seven") - 0.02) < 1e-12
    assert abs(three_match_probability("seven") - 0.000008) < 1e-15
    assert abs(two_cherry_probability() - 0.189) < 1e-12
    assert abs(hit_frequency() - 0.24352) < 1e-9
    assert abs(rtp() - 0.838364) < 1e-6, rtp()
    assert abs(house_edge() - 0.161636) < 1e-6
 
    # Three cherries must NOT be double-counted as a two-cherry win.
    # (Name these rows explicitly — a substring filter on "cherry" silently
    # misses "two_cherries", since the plural is "cherr-ies", not "cherr-y".)
    assert abs(three_match_probability("cherry") - 0.027) < 1e-12
    rows_by_name = {r["outcome"]: r["probability"] for r in _TABLE}
    assert "three_cherry" in rows_by_name and "two_cherries" in rows_by_name
    assert abs(rows_by_name["three_cherry"] - 0.027) < 1e-12
    assert abs(rows_by_name["two_cherries"] - 0.189) < 1e-12
    # The two buckets are disjoint: 0.027 + 0.189, never 0.216 counted twice.
    assert abs(rows_by_name["three_cherry"]
               + rows_by_name["two_cherries"] - 0.216) < 1e-12
 
    # The headline claim: bet size cannot change the return.
    assert rtp_is_bet_independent()
    assert abs(expected_value(250) / 250 - expected_value(25) / 25) < 1e-12
 
    # Slots must be meaningfully worse than the project's own roulette (2/38).
    assert house_edge() > 3 * (2 / 38)
 
    # Bankroll math sanity: 1000 chips at $25 -> ~247 spins.
    assert 240 < expected_spins_until_broke(1000, 25) < 255
    assert expected_spins_until_broke(1000, 250) < 30
 
    # Jackpot really is a lottery ticket. (0.02**3 isn't exactly 8e-6 in binary
    # floating point, so compare with a tolerance rather than ==.)
    assert abs(1 / three_match_probability("seven") - 125_000) < 1e-6
    assert probability_of_hitting_in("seven", 100) < 0.001
 
    # And the engine must track the game, not a copy of it.
    assert SYMBOL_WEIGHTS == SlotMachine.SYMBOL_WEIGHTS
    assert PAYOUTS == SlotRules.PAYOUTS
 
    print("slots_odds.py self-checks passed.")