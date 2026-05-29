# Dealer up-card values run 2..11, where 11 == Ace and 10 covers 10/J/Q/K.
# The order here defines the COLUMN order of every table below.
DEALER_VALUES = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
 
# Human-readable names for each final action code.
ACTION_NAMES = {'H': 'Hit', 'S': 'Stand', 'D': 'Double Down', 'P': 'Split'}
 
# ---------------------------------------------------------------------------
# HARD TOTALS  (no Ace, or an Ace that has been forced down to count as 1)
# Key   = the hand's total (5-21)
# Value = 10 actions, one per dealer up-card, in DEALER_VALUES order.
# ---------------------------------------------------------------------------
#                    2    3    4    5    6    7    8    9   10    A
HARD_STRATEGY = {
    5:  ['H', 'H', 'H', 'H', 'H', 'H', 'H', 'H', 'H', 'H'],
    6:  ['H', 'H', 'H', 'H', 'H', 'H', 'H', 'H', 'H', 'H'],
    7:  ['H', 'H', 'H', 'H', 'H', 'H', 'H', 'H', 'H', 'H'],
    8:  ['H', 'H', 'H', 'H', 'H', 'H', 'H', 'H', 'H', 'H'],
    9:  ['H', 'D', 'D', 'D', 'D', 'H', 'H', 'H', 'H', 'H'],
    10: ['D', 'D', 'D', 'D', 'D', 'D', 'D', 'D', 'H', 'H'],
    11: ['D', 'D', 'D', 'D', 'D', 'D', 'D', 'D', 'D', 'H'],
    12: ['H', 'H', 'S', 'S', 'S', 'H', 'H', 'H', 'H', 'H'],
    13: ['S', 'S', 'S', 'S', 'S', 'H', 'H', 'H', 'H', 'H'],
    14: ['S', 'S', 'S', 'S', 'S', 'H', 'H', 'H', 'H', 'H'],
    15: ['S', 'S', 'S', 'S', 'S', 'H', 'H', 'H', 'H', 'H'],
    16: ['S', 'S', 'S', 'S', 'S', 'H', 'H', 'H', 'H', 'H'],
    17: ['S', 'S', 'S', 'S', 'S', 'S', 'S', 'S', 'S', 'S'],
    18: ['S', 'S', 'S', 'S', 'S', 'S', 'S', 'S', 'S', 'S'],
    19: ['S', 'S', 'S', 'S', 'S', 'S', 'S', 'S', 'S', 'S'],
    20: ['S', 'S', 'S', 'S', 'S', 'S', 'S', 'S', 'S', 'S'],
    21: ['S', 'S', 'S', 'S', 'S', 'S', 'S', 'S', 'S', 'S'],
}
 
# ---------------------------------------------------------------------------
# SOFT TOTALS  (an Ace is currently counting as 11)
# Key = the soft total. 13 == A,2 ... 21 == A,10 (blackjack).
# 12 is included only to cover an un-splittable pair of Aces (A,A = soft 12),
# which should always hit.
# ---------------------------------------------------------------------------
#                     2     3     4     5     6     7    8    9   10    A
SOFT_STRATEGY = {
    12: ['H',  'H',  'H',  'H',  'H',  'H', 'H', 'H', 'H', 'H'],  # A,A (if not split)
    13: ['H',  'H',  'H',  'D',  'D',  'H', 'H', 'H', 'H', 'H'],  # A,2
    14: ['H',  'H',  'H',  'D',  'D',  'H', 'H', 'H', 'H', 'H'],  # A,3
    15: ['H',  'H',  'D',  'D',  'D',  'H', 'H', 'H', 'H', 'H'],  # A,4
    16: ['H',  'H',  'D',  'D',  'D',  'H', 'H', 'H', 'H', 'H'],  # A,5
    17: ['H',  'D',  'D',  'D',  'D',  'H', 'H', 'H', 'H', 'H'],  # A,6
    18: ['S',  'Ds', 'Ds', 'Ds', 'Ds', 'S', 'S', 'H', 'H', 'H'],  # A,7
    19: ['S',  'S',  'S',  'S',  'S',  'S', 'S', 'S', 'S', 'S'],  # A,8
    20: ['S',  'S',  'S',  'S',  'S',  'S', 'S', 'S', 'S', 'S'],  # A,9
    21: ['S',  'S',  'S',  'S',  'S',  'S', 'S', 'S', 'S', 'S'],  # A,10
}
 
# ---------------------------------------------------------------------------
# PAIRS  (two cards of equal RANK — the split decisions)
# Key = the value of ONE card of the pair (2-11, where 11 == a pair of Aces).
# 10/J/Q/K all map to value 10, so the "10" row covers any two ten-value cards.
#
# Only 'P' entries trigger a split. The non-'P' entries (e.g. the 5,5 and 10,10
# rows) are filled in to match the look of public charts, but the engine never
# acts on them directly: when the chart doesn't say split, the hand is replayed
# as its plain total instead (see resolve_code).
# ---------------------------------------------------------------------------
#                     2    3    4    5    6    7    8    9   10    A
PAIR_STRATEGY = {
    2:  ['P', 'P', 'P', 'P', 'P', 'P', 'H', 'H', 'H', 'H'],  # 2,2
    3:  ['P', 'P', 'P', 'P', 'P', 'P', 'H', 'H', 'H', 'H'],  # 3,3
    4:  ['H', 'H', 'H', 'P', 'P', 'H', 'H', 'H', 'H', 'H'],  # 4,4
    5:  ['D', 'D', 'D', 'D', 'D', 'D', 'D', 'D', 'H', 'H'],  # 5,5  -> never split (play as hard 10)
    6:  ['P', 'P', 'P', 'P', 'P', 'H', 'H', 'H', 'H', 'H'],  # 6,6
    7:  ['P', 'P', 'P', 'P', 'P', 'P', 'H', 'H', 'H', 'H'],  # 7,7
    8:  ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],  # 8,8  -> always split
    9:  ['P', 'P', 'P', 'P', 'P', 'S', 'P', 'P', 'S', 'S'],  # 9,9
    10: ['S', 'S', 'S', 'S', 'S', 'S', 'S', 'S', 'S', 'S'],  # 10,10 -> never split
    11: ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],  # A,A  -> always split
}
 
 
# ---------------------------------------------------------------------------
# The decision engine
# ---------------------------------------------------------------------------
def _col(dealer_value):
    if dealer_value not in DEALER_VALUES:
        raise ValueError(f"dealer_value must be 2-11 (11 = Ace), got {dealer_value}")
    return DEALER_VALUES.index(dealer_value)
 
 
def get_raw_code(total, dealer_value, is_soft=False, is_pair=False, pair_value=None):
    col = _col(dealer_value)
 
    # Pairs take priority: the pair chart already encodes "don't split" cases.
    if is_pair and pair_value is not None:
        return PAIR_STRATEGY[pair_value][col]
 
    # Soft totals (an Ace is counting as 11).
    if is_soft and total in SOFT_STRATEGY:
        return SOFT_STRATEGY[total][col]
 
    # Hard totals. Anything below 5 or above 21 is clamped into the table range.
    clamped = max(5, min(total, 21))
    return HARD_STRATEGY[clamped][col]
 
 
def resolve_code(code, dealer_value, total, is_soft=False,
                 can_double=True, can_split=True):
    if code == 'P':
        if can_split:
            return 'P'
        # Can't split (e.g. the game hasn't implemented it, or it's a 3+ card
        # hand): play the pair as a normal total instead.
        fallback = get_raw_code(total, dealer_value, is_soft=is_soft, is_pair=False)
        return resolve_code(fallback, dealer_value, total, is_soft=is_soft,
                            can_double=can_double, can_split=False)
    if code == 'D':
        return 'D' if can_double else 'H'
    if code == 'Ds':
        return 'D' if can_double else 'S'
    return code  # 'H' or 'S'
 
 
def get_action(total, dealer_value, is_soft=False, is_pair=False, pair_value=None,
               can_double=True, can_split=True):
    raw = get_raw_code(total, dealer_value, is_soft=is_soft,
                       is_pair=is_pair, pair_value=pair_value)
    return resolve_code(raw, dealer_value, total, is_soft=is_soft,
                        can_double=can_double, can_split=can_split)
 
 
# ---------------------------------------------------------------------------
# Chart rendering (handy for the team's "cross-reference vs public chart" eval)
# ---------------------------------------------------------------------------
def render_chart(title, table, key_fmt):
    head = "  " + "".join(f"{('A' if d == 11 else d):>4}" for d in DEALER_VALUES)
    lines = [title, " " * 6 + head]
    for key in sorted(table):
        row = "".join(f"{c:>4}" for c in table[key])
        lines.append(f"  {key_fmt(key):<5}{row}")
    return "\n".join(lines)
 
 
if __name__ == "__main__":
    print(render_chart("HARD TOTALS", HARD_STRATEGY, lambda k: str(k)))
    print()
    print(render_chart("SOFT TOTALS (A,x)", SOFT_STRATEGY,
                       lambda k: f"A,{k - 11}" if k > 12 else "A,A"))
    print()
    print(render_chart("PAIRS", PAIR_STRATEGY,
                       lambda k: ("A,A" if k == 11 else f"{k},{k}")))
 
    # A few internal sanity checks against well-known answers.
    assert get_action(16, 10) == 'H'
    assert get_action(16, 6) == 'S'
    assert get_action(11, 6) == 'D'
    assert get_action(11, 6, can_double=False) == 'H'
    assert get_action(8, 6, is_pair=True, pair_value=8) == 'P'
    assert get_action(12, 5, is_soft=True, is_pair=True, pair_value=11,
                      can_split=False) == 'H'      # un-splittable A,A
    print("\nstrategy.py self-checks passed.")