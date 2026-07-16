from backend.ai.slots_odds import (
    ALLOWED_BETS,
    PAYOUTS,
    REAL_SLOT_RTP_HIGH,
    REAL_SLOT_RTP_LOW,
    SYMBOL_WEIGHTS,
    expected_loss,
    expected_spins_until_broke,
    expected_value,
    hit_frequency,
    house_edge,
    jackpot_symbol,
    outcome_table,
    probability_of_hitting_in,
    probability_of_no_win,
    rtp,
    spins_for_even_odds,
    std_dev,
    symbol_probability,
    three_match_probability,
    two_cherry_probability,
)
 
HEAVY_BET_FRACTION = 0.25
RECKLESS_BET_FRACTION = 0.50
 
COLD_STREAK_NOTICE = 6
 
MEANINGFUL_SESSION = 200
 
 
def _pct(x):
    return f"{x * 100:.2f}%"
 
 
def _rare_pct(x):
    pct = x * 100
    if pct <= 0:
        return "0%"
    if pct >= 0.01:
        return f"{pct:.2f}%"
    return f"{pct:.8f}".rstrip("0").rstrip(".") + "%"
 
 
def _plural(symbol):
    if symbol.endswith("y") and not symbol.endswith(("ay", "ey", "iy", "oy", "uy")):
        return symbol[:-1] + "ies"
    return symbol + "s"
 
 
def _detect_cold_streak(history):
    streak = 0
    for spin in reversed(history or []):
        if spin.get("won"):
            break
        streak += 1
    return streak
 
 
def _detect_escalation(history, amount):
    if not history:
        return None
    last = history[-1]
    last_amount = last.get("amount", 0)
    if last.get("won") or last_amount <= 0 or amount <= last_amount:
        return None
 
    losses = _detect_cold_streak(history)
    return {"from": last_amount, "to": amount, "consecutive_losses": losses}
 
 
def _near_miss(reels):
    if not reels:
        return None
    jp = jackpot_symbol()
    if list(reels).count(jp) == 2:
        return jp
    return None
 
 
class SlotsAdvisor:
    def __init__(self, heavy_fraction=HEAVY_BET_FRACTION,
                 reckless_fraction=RECKLESS_BET_FRACTION):
        self.heavy_fraction = heavy_fraction
        self.reckless_fraction = reckless_fraction
 
    def _bankroll_warning(self, chips, amount):
        if chips <= 0 or amount <= 0:
            return None
        fraction = amount / chips
        spins = expected_spins_until_broke(chips, amount)

        if fraction >= self.reckless_fraction:
            return {
                "code": "bankroll_reckless",
                "severity": "high",
                "message": (
                    f"${amount} is {_pct(fraction)} of your entire stack, on a game "
                    f"that keeps {_pct(house_edge())} of everything wagered. You're "
                    f"looking at roughly {spins:.0f} spins before it's gone. Betting "
                    f"less won't improve your odds — nothing does — but it's the only "
                    f"thing that buys you more game."
                ),
            }
        if fraction >= self.heavy_fraction:
            return {
                "code": "bankroll_heavy",
                "severity": "medium",
                "message": (
                    f"At ${amount} a spin you get about {spins:.0f} spins out of "
                    f"{chips:,} chips. This machine takes {_pct(house_edge())} of "
                    f"every chip wagered, so the bigger the bet, the faster the "
                    f"clock runs."
                ),
            }
        return None
 
    def _max_bet_warning(self, amount):
        if amount != max(ALLOWED_BETS):
            return None
        return {
            "code": "max_bet_myth",
            "severity": "medium",
            "message": (
                f"Max bet doesn't improve anything here. Every payout on this machine "
                f"is a flat multiple of your stake, so the return is exactly "
                f"{_pct(rtp())} whether you bet ${min(ALLOWED_BETS)} or ${amount}. "
                f"(Some real machines do lock a progressive jackpot behind max bet — "
                f"this one has no such feature.) All ${amount} buys you is a "
                f"{max(ALLOWED_BETS) // min(ALLOWED_BETS)}x faster burn: "
                f"~${expected_loss(amount):.2f} lost per spin instead of "
                f"~${expected_loss(min(ALLOWED_BETS)):.2f}."
            ),
        }
 
    def _cold_streak_warning(self, history):
        streak = _detect_cold_streak(history)
        if streak < COLD_STREAK_NOTICE:
            return None
        p_dry = probability_of_no_win(streak)
        return {
            "code": "cold_machine_myth",
            "severity": "low",
            "message": (
                f"{streak} spins without a hit — long enough that the machine starts "
                f"to feel broken, or 'cold'. It isn't either. Every spin draws three "
                f"fresh symbols independently; the machine holds no memory of what it "
                f"just did and is never 'due'. A dry run of {streak} has about a "
                f"{_pct(p_dry)} chance of happening at any moment, which means it "
                f"happens all the time. Your next spin is a {_pct(hit_frequency())} "
                f"shot, same as your first."
            ),
        }
 
    def _escalation_warning(self, history, amount):
        esc = _detect_escalation(history, amount)
        if not esc or esc["consecutive_losses"] < 3:
            return None
        return {
            "code": "chasing_losses",
            "severity": "high",
            "message": (
                f"You've lost {esc['consecutive_losses']} in a row and just raised "
                f"your bet from ${esc['from']} to ${esc['to']}. This is the reflex the "
                f"house is built on. Raising the stake does not raise your return — "
                f"it's {_pct(rtp())} at every tier — it only raises how much you lose "
                f"per spin, from ~${expected_loss(esc['from']):.2f} to "
                f"~${expected_loss(esc['to']):.2f}. Losses don't 'owe' you a "
                f"correction, and the machine can't pay one."
            ),
        }
 
    def recommend(self, chips, amount, history=None, session=None):
        history = history or []
        if amount not in ALLOWED_BETS:
            raise ValueError(f"Bet must be one of {ALLOWED_BETS}, got {amount!r}")
 
        warnings = [w for w in (
            self._escalation_warning(history, amount),
            self._bankroll_warning(chips, amount),
            self._max_bet_warning(amount),
            self._cold_streak_warning(history),
        ) if w]
 
        verdict = "Careful" if any(w["severity"] == "high" for w in warnings) \
            else "No edge to find"
 
        explanation = (
            f"This machine pays back {_pct(rtp())} of everything wagered, so every "
            f"${amount} spin costs you about ${expected_loss(amount):.2f} on average. "
            f"You'll hit something {_pct(hit_frequency())} of the time — roughly 1 "
            f"spin in {1 / hit_frequency():.0f} — but most hits are the small "
            f"two-cherry consolation, not a jackpot."
        )
 
        jp = jackpot_symbol()
        lesson = (
            f"There is no strategy here, and that's not a failure of imagination — "
            f"it's the design. The reels are drawn fresh and independently on every "
            f"spin, so nothing you do (bet size, timing, stopping the reels, "
            f"switching machines) changes a single probability. Bet size is your one "
            f"lever and it moves the stake and the payout together, leaving the "
            f"return pinned at {_pct(rtp())}. For scale: this machine's "
            f"{_pct(house_edge())} edge is over three times the {_pct(2 / 38)} on "
            f"this project's own roulette wheel, and three {_plural(jp)} — the "
            f"{PAYOUTS[jp]}x jackpot — land once every "
            f"{1 / three_match_probability(jp):,.0f} spins."
        )
 
        return {
            "verdict": verdict,
            "explanation": explanation,
            "lesson": lesson,
            "warnings": warnings,
            "amount": amount,
            "rtp_percent": round(rtp() * 100, 2),
            "house_edge_percent": round(house_edge() * 100, 2),
            "hit_frequency_percent": round(hit_frequency() * 100, 2),
            "expected_value": round(expected_value(amount), 2),
            "expected_loss_per_spin": round(expected_loss(amount), 2),
            "std_dev": round(std_dev(amount), 2),
            "spins_of_bankroll": (
                round(expected_spins_until_broke(chips, amount))
                if chips > 0 else 0
            ),
        }
 
    def evaluate(self, result, history=None):
        reels = result.get("reels", [])
        won = bool(result.get("won"))
        amount = result.get("amount", 0)
        payout = result.get("payout", 0)
        outcome = result.get("result", "")
 
        near = _near_miss(reels)
        if near and not won:
            p_two = 3 * (symbol_probability(near) ** 2) * (1 - symbol_probability(near))
            return {
                "won": False,
                "explanation": (
                    f"Two {_plural(near)} and a miss. That feels like you almost hit the "
                    f"jackpot — and that feeling is the most profitable illusion in "
                    f"the building. You weren't close to anything: the third reel was "
                    f"drawn independently and never 'nearly' matched. Two {_plural(near)} with "
                    f"no third comes up about {_rare_pct(p_two)} of the time, roughly "
                    f"once every {1 / p_two:.0f} spins, and it pays exactly nothing."
                ),
                "teaching_moment": "near_miss",
            }
 
        if won and outcome == "three_match":
            symbol = reels[0] if reels else "?"
            odds = three_match_probability(symbol)
            return {
                "won": True,
                "explanation": (
                    f"Three {_plural(symbol)} — ${payout:,} back. That's a {_rare_pct(odds)} "
                    f"outcome (about 1 in {1 / odds:,.0f} spins) and it landed. "
                    f"Enjoy it, but the machine hasn't changed: the next spin is "
                    f"drawn from the same weights, with the same {_pct(rtp())} return. "
                    f"A machine that just paid is not 'hot', and one that just took "
                    f"your money is not 'cold'. It has no memory at all."
                ),
                "teaching_moment": "hot_hand",
            }
 
        if won:
            return {
                "won": True,
                "explanation": (
                    f"Two cherries — ${payout:,} back. This is the machine's most "
                    f"common payout by far ({_pct(two_cherry_probability())} of spins) "
                    f"and it's the reason slots feel generous: you get frequent, "
                    f"comparatively small wins. Even so, they are not frequent enough "
                    f"to overcome the losing spins, so the long-run return remains "
                    f"{_pct(rtp())}."
                ),
                "teaching_moment": "small_win",
            }
 
        streak = _detect_cold_streak((history or []) + [result])
        explanation = (
            f"No match. Nothing has gone wrong — {_pct(1 - hit_frequency())} of spins "
            f"lose, by design."
        )
        if streak >= COLD_STREAK_NOTICE:
            explanation += (
                f" You're {streak} spins into a dry run, which feels like the machine "
                f"has turned against you. It hasn't: a streak this long has a "
                f"{_pct(probability_of_no_win(streak))} chance of occurring at any "
                f"point, and the reels don't know it's happening."
            )
        return {"won": False, "explanation": explanation, "teaching_moment": "loss"}
 
    def session_reality_check(self, spins, wagered, returned, amount=None):
        if spins <= 0 or wagered <= 0:
            return {
                "explanation": (
                    "No spins yet. Worth knowing before you start: this machine "
                    f"returns {_pct(rtp())} of everything wagered, so the house keeps "
                    f"{_pct(house_edge())} of it over time."
                ),
                "spins": 0,
            }
 
        actual_rtp = returned / wagered
        expected_return = rtp() * wagered
        net = returned - wagered
 
        avg_bet = amount or (wagered / spins)
        session_sd = std_dev(avg_bet) * (spins ** 0.5)
        z = ((returned - wagered) - expected_value(avg_bet) * spins) / session_sd \
            if session_sd > 0 else 0.0
 
        if spins < MEANINGFUL_SESSION:
            weight = (
                f"That's only {spins} spins, which is far too few to mean anything. "
                f"At this sample size the result is almost pure variance — the "
                f"{_pct(rtp())} return needs thousands of spins to show through."
            )
        else:
            weight = (
                f"Over {spins:,} spins the numbers are starting to converge on the "
                f"machine's true {_pct(rtp())}, which is exactly what the maths "
                f"predicts."
            )
 
        if net > 0:
            verdict = (
                f"You're up ${net:,} — genuinely lucky, not skilled, because there is "
                f"no skill available in this game. {weight} Every additional spin pulls "
                f"you back toward the house edge; the only way to keep a slots profit "
                f"is to stop having it taken back."
            )
        elif net == 0:
            verdict = f"You're exactly even after {spins:,} spins. {weight}"
        else:
            verdict = (
                f"You're down ${abs(net):,}. The maths expected you to be down about "
                f"${wagered - expected_return:,.0f} after wagering ${wagered:,}, so "
                f"this is {'roughly on script' if abs(z) < 2 else 'a rougher run than average'}"
                f" — not a broken machine, and not bad luck that owes you a correction. "
                f"{weight}"
            )
 
        return {
            "spins": spins,
            "wagered": wagered,
            "returned": returned,
            "net": net,
            "actual_rtp_percent": round(actual_rtp * 100, 2),
            "expected_rtp_percent": round(rtp() * 100, 2),
            "std_devs_from_expected": round(z, 2),
            "sample_is_meaningful": spins >= MEANINGFUL_SESSION,
            "explanation": verdict,
        }
 
    def payout_table(self):
        rows = []
        for row in outcome_table():
            if row["multiplier"] is None:
                continue
            p = row["probability"]
            rows.append({
                "outcome": row["outcome"],
                "multiplier": row["multiplier"],
                "probability_percent": round(p * 100, 4),
                "one_in": round(1 / p) if p > 0 else None,
                "rtp_share_percent": round(row["return_contribution"] * 100, 2),
            })
 
        jp = jackpot_symbol()
        return {
            "rows": rows,
            "rtp_percent": round(rtp() * 100, 2),
            "house_edge_percent": round(house_edge() * 100, 2),
            "loss_probability_percent": round((1 - hit_frequency()) * 100, 2),
            "takeaway": (
                f"Notice where the return actually comes from: the two-cherry "
                f"consolation prize alone supplies {round(two_cherry_probability() * 3 * 100)}% "
                f"of the {_pct(rtp())} return, while the {PAYOUTS[jp]}x jackpot "
                f"contributes almost nothing because it lands once in "
                f"{1 / three_match_probability(jp):,.0f} spins. The big number on the "
                f"paytable is advertising; the small frequent one is the actual game."
            ),
        }
 
 
# ---------------------------------------------------------------------------
# Self-test — run with:  python -m backend.ai.slots_advise
# ---------------------------------------------------------------------------
if __name__ == "__main__":
 
    def spin(reels, amount=25, won=False, payout=0, result="lose"):
        return {"reels": reels, "amount": amount, "won": won,
                "payout": payout, "result": result}
 
    adv = SlotsAdvisor()
    codes = lambda r: {w["code"] for w in r["warnings"]}
 
    print("=== Pre-spin advice, minimum bet ===\n")
    r = adv.recommend(1000, 25)
    print(f"  [{r['verdict']}] {r['explanation']}\n")
    print(f"  {r['lesson']}\n")
 
    print("=== Max bet — the 'bet big to win big' myth ===\n")
    r = adv.recommend(1000, 250)
    for w in r["warnings"]:
        print(f"  [{w['code']}] {w['message']}\n")
 
    print("=== Chasing: jumping tiers after 4 losses ===\n")
    losing = [spin(["lemon", "bell", "star"], amount=25) for _ in range(4)]
    r = adv.recommend(1000, 100, history=losing)
    for w in r["warnings"]:
        print(f"  [{w['code']}] {w['message']}\n")
 
    print("=== The near-miss: two sevens ===\n")
    e = adv.evaluate(spin(["seven", "seven", "lemon"], amount=100))
    print(f"  {e['explanation']}\n")
 
    print("=== A jackpot — and why it means nothing ===\n")
    e = adv.evaluate(spin(["seven", "seven", "seven"], amount=100, won=True,
                          payout=2500, result="three_match"))
    print(f"  {e['explanation']}\n")
 
    print("=== Session reality check ===\n")
    for label, (s, w, ret) in {
        "short lucky run": (40, 1000, 1600),
        "long grind":      (500, 12500, 10400),
    }.items():
        rc = adv.session_reality_check(s, w, ret, amount=25)
        print(f"  {label}: actual RTP {rc['actual_rtp_percent']}% "
              f"vs expected {rc['expected_rtp_percent']}%")
        print(f"    {rc['explanation']}\n")
 
    print("=== The paytable, with the odds attached ===\n")
    pt = adv.payout_table()
    print(f"  {'outcome':16}{'pays':>7}{'chance':>10}{'1 in':>10}{'of RTP':>9}")
    for row in pt["rows"]:
        print(f"  {row['outcome']:16}{row['multiplier']:>6}x"
              f"{row['probability_percent']:>9.3f}%"
              f"{row['one_in']:>10,}"
              f"{row['rtp_share_percent']:>8.1f}%")
    print(f"\n  {pt['takeaway']}\n")
 
    # ---- assertions ----
    # The advisor must never imply a bet size improves the return.
    assert adv.recommend(1000, 25)["rtp_percent"] == \
           adv.recommend(1000, 250)["rtp_percent"] == 83.84
 
    # ...and must say so out loud when the player maxes their bet.
    assert "max_bet_myth" in codes(adv.recommend(1000, 250))
    assert "max_bet_myth" not in codes(adv.recommend(1000, 25))
 
    # Expected loss must scale with the stake even though RTP does not.
    # (Compare with a tolerance: 40.41 is not exactly 10 * 4.04 once rounded.)
    assert abs(adv.recommend(1000, 250)["expected_loss_per_spin"]
               - 10 * adv.recommend(1000, 25)["expected_loss_per_spin"]) < 0.05
 
    # Regression: a rare outcome must never be reported to the player as
    # "0.00%". Telling someone who just hit a jackpot that it had no chance of
    # happening is both wrong-looking and the opposite of the intended lesson.
    jackpot_msg = adv.evaluate(spin(["seven", "seven", "seven"], won=True,
                                    payout=2500, result="three_match"))["explanation"]
    assert "0.00%" not in jackpot_msg, jackpot_msg
    assert _rare_pct(three_match_probability("seven")) == "0.0008%"
    assert _rare_pct(0.4737) == "47.37%"
 
    # Chasing needs BOTH an escalation and a losing run.
    assert "chasing_losses" in codes(adv.recommend(1000, 100, history=losing))
    assert "chasing_losses" not in codes(adv.recommend(1000, 25, history=losing))
    won_last = [spin(["cherry", "cherry", "bell"], amount=25, won=True,
                     payout=50, result="two_cherries")]
    assert "chasing_losses" not in codes(adv.recommend(1000, 100, history=won_last))
 
    # Cold-streak myth fires only after a real drought.
    assert "cold_machine_myth" in codes(
        adv.recommend(1000, 25, history=[spin(["lemon", "bell", "star"])] * 8))
    assert "cold_machine_myth" not in codes(
        adv.recommend(1000, 25, history=[spin(["lemon", "bell", "star"])] * 2))
 
    # Bankroll warnings.
    assert "bankroll_reckless" in codes(adv.recommend(150, 100))
    assert not codes(adv.recommend(10000, 25))
 
    # Near-miss detection must fire on two jackpot symbols and NOT on a win.
    assert adv.evaluate(spin(["seven", "seven", "lemon"]))["teaching_moment"] == "near_miss"
    assert adv.evaluate(spin(["seven", "seven", "seven"], won=True, payout=2500,
                             result="three_match"))["teaching_moment"] == "hot_hand"
    assert adv.evaluate(spin(["cherry", "cherry", "bell"], won=True, payout=50,
                             result="two_cherries"))["teaching_moment"] == "small_win"
    assert adv.evaluate(spin(["lemon", "bell", "star"]))["teaching_moment"] == "loss"
 
    # The reality check must not congratulate a lucky player on their skill.
    lucky = adv.session_reality_check(40, 1000, 1600, amount=25)
    assert lucky["net"] == 600 and not lucky["sample_is_meaningful"]
    assert "lucky" in lucky["explanation"].lower()
    # A long session should be flagged as a meaningful sample.
    assert adv.session_reality_check(500, 12500, 10400, amount=25)["sample_is_meaningful"]
    # And an empty session must not divide by zero.
    assert adv.session_reality_check(0, 0, 0)["spins"] == 0
 
    # Paytable rows must exclude the loss row and sum to the true RTP.
    pt = adv.payout_table()
    assert all(r["multiplier"] is not None for r in pt["rows"])
    assert abs(sum(r["rtp_share_percent"] for r in pt["rows"]) - 83.84) < 0.05
 
    # Regression: symbols must pluralise correctly in text the player reads.
    # Naive f"{symbol}s" renders "Three cherrys", which is visible in the UI.
    assert _plural("cherry") == "cherries"
    assert _plural("seven") == "sevens"
    assert _plural("bell") == "bells"
    cherry_win = adv.evaluate(spin(["cherry", "cherry", "cherry"], won=True,
                                   payout=75, result="three_match"))["explanation"]
    assert "cherries" in cherry_win and "cherrys" not in cherry_win, cherry_win
    # And no message may contain a naive plural for ANY symbol the machine has.
    for sym in SYMBOL_WEIGHTS:
        msg = adv.evaluate(spin([sym, sym, sym], won=True, payout=1,
                                result="three_match"))["explanation"]
        assert f"{sym}s" in msg or _plural(sym) in msg
        if sym.endswith("y"):
            assert f"{sym}s" not in msg, msg
 
    print("All slots_advise.py self-checks passed.")
