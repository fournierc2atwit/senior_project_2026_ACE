HI_LO_VALUES = {
    '2': +1, '3': +1, '4': +1, '5': +1, '6': +1,
    '7': 0, '8': 0, '9': 0,
    '10': -1, 'Jack': -1, 'Queen': -1, 'King': -1, 'Ace': -1,
}


def card_tag(card):
    return HI_LO_VALUES[card.rank]


class CardCounter:
    def __init__(self, num_decks=6, system=None):
        self.num_decks = num_decks
        self.system = system or HI_LO_VALUES
        self.running_count = 0
        self.cards_seen = 0

    def count_card(self, card):
        self.running_count += self.system[card.rank]
        self.cards_seen += 1

    def count_cards(self, cards):
        for c in cards:
            self.count_card(c)

    def decks_remaining(self):
        cards_left = self.num_decks * 52 - self.cards_seen
        return cards_left / 52

    def true_count(self):
        decks = self.decks_remaining()
        if decks <= 0:
            return 0.0
        return self.running_count / decks

    def reset(self):
        self.running_count = 0
        self.cards_seen = 0

    def status(self):
        return {
            "running_count": self.running_count,
            "true_count": round(self.true_count(), 2),
            "decks_remaining": round(self.decks_remaining(), 2),
            "cards_seen": self.cards_seen,
        }

    def __repr__(self):
        return (f"CardCounter(running={self.running_count}, "
                f"true={self.true_count():.2f}, "
                f"decks_left={self.decks_remaining():.2f})")


BASE_HOUSE_EDGE = 0.5
EDGE_PER_TRUE_COUNT = 0.5


def estimated_edge(true_count):
    return EDGE_PER_TRUE_COUNT * true_count - BASE_HOUSE_EDGE


def bet_units(true_count, max_units=8, spread_start=2):
    if true_count < spread_start:
        return 1
    return min(int(true_count), max_units)


def recommend_bet(true_count, unit=10, max_units=8, spread_start=2):
    """Return (units, dollar_amount) for a given true count."""
    units = bet_units(true_count, max_units=max_units, spread_start=spread_start)
    return units, units * unit


ILLUSTRIOUS_18 = {
    # --- positive-count deviations (lots of tens left) ---
    ('hard', 16, 10): (0,  'GE', 'S'),   # 16 vs 10: stand (basic = hit)
    ('hard', 16,  9): (5,  'GE', 'S'),   # 16 vs 9:  stand (basic = hit)
    ('hard', 15, 10): (4,  'GE', 'S'),   # 15 vs 10: stand (basic = hit)
    ('hard', 12,  3): (2,  'GE', 'S'),   # 12 vs 3:  stand (basic = hit)
    ('hard', 12,  2): (3,  'GE', 'S'),   # 12 vs 2:  stand (basic = hit)
    ('pair', 10,  5): (5,  'GE', 'P'),   # 10,10 vs 5: split (basic = stand)
    ('pair', 10,  6): (4,  'GE', 'P'),   # 10,10 vs 6: split (basic = stand)
    ('hard', 10, 10): (4,  'GE', 'D'),   # 10 vs 10: double (basic = hit)
    ('hard', 10, 11): (4,  'GE', 'D'),   # 10 vs A:  double (basic = hit)
    ('hard', 11, 11): (1,  'GE', 'D'),   # 11 vs A:  double (basic = hit, S17)
    ('hard',  9,  2): (1,  'GE', 'D'),   # 9 vs 2:   double (basic = hit)
    ('hard',  9,  7): (3,  'GE', 'D'),   # 9 vs 7:   double (basic = hit)

    # --- negative-count deviations (lots of low cards left) ---
    ('hard', 13,  2): (-1, 'LE', 'H'),   # 13 vs 2: hit (basic = stand)
    ('hard', 13,  3): (-2, 'LE', 'H'),   # 13 vs 3: hit (basic = stand)
    ('hard', 12,  4): (0,  'LE', 'H'),   # 12 vs 4: hit (basic = stand)
    ('hard', 12,  5): (-2, 'LE', 'H'),   # 12 vs 5: hit (basic = stand)
    ('hard', 12,  6): (-1, 'LE', 'H'),   # 12 vs 6: hit (basic = stand)
}

INSURANCE_INDEX = 3


def _triggers(true_count, index, direction):
    if direction == 'GE':
        return true_count >= index
    return true_count <= index   # 'LE'


def get_deviation(total, dealer_value, true_count, basic_action,
                  is_soft=False, is_pair=False, pair_value=None,
                  can_double=True, can_split=True):
    if is_pair and pair_value == 10:
        entry = ILLUSTRIOUS_18.get(('pair', 10, dealer_value))
        if entry:
            index, direction, action = entry
            if action == 'P' and not can_split:
                return None
            if _triggers(true_count, index, direction):
                return {'action': action, 'index': index, 'direction': direction}
        return None

    if is_soft or basic_action == 'P':
        return None

    entry = ILLUSTRIOUS_18.get(('hard', total, dealer_value))
    if not entry:
        return None
    index, direction, action = entry
    if action == 'D' and not can_double:
        return None
    if _triggers(true_count, index, direction):
        return {'action': action, 'index': index, 'direction': direction}
    return None


def should_take_insurance(dealer_value, true_count):
    if dealer_value != 11:
        return None
    return true_count >= INSURANCE_INDEX


if __name__ == "__main__":
    # ---- counting math ----
    class _FakeCard:
        def __init__(self, rank):
            self.rank = rank

    c = CardCounter(num_decks=6)
    c.count_cards([_FakeCard(r) for r in ['5', '5', '6', '10', 'Ace']])
    assert c.running_count == 1, c.running_count          # +1+1+1-1-1
    assert c.cards_seen == 5

    # true count: force a clean 3-decks-remaining scenario
    c.running_count, c.cards_seen = 6, 156                # 312-156 = 156 = 3 decks
    assert round(c.true_count(), 2) == 2.0, c.true_count()

    # ---- betting ramp ----
    assert bet_units(1.0) == 1
    assert bet_units(2.0) == 2
    assert bet_units(5.0) == 5
    assert bet_units(12.0) == 8            # capped at max_units

    # ---- deviations ----
    # 16 vs 10: stand at TC >= 0, hit below
    assert get_deviation(16, 10, 0.0, 'H')['action'] == 'S'
    assert get_deviation(16, 10, -1.0, 'H') is None
    # 15 vs 10: stand at +4
    assert get_deviation(15, 10, 4.0, 'H')['action'] == 'S'
    assert get_deviation(15, 10, 3.0, 'H') is None
    # 12 vs 3: stand at +2
    assert get_deviation(12, 3, 2.0, 'H')['action'] == 'S'
    # 12 vs 4: hit at TC <= 0 (negative deviation; basic = stand)
    assert get_deviation(12, 4, 0.0, 'S')['action'] == 'H'
    assert get_deviation(12, 4, 1.0, 'S') is None
    # 11 vs A: double at +1, but only if doubling is allowed
    assert get_deviation(11, 11, 1.0, 'H')['action'] == 'D'
    assert get_deviation(11, 11, 1.0, 'H', can_double=False) is None
    # 10,10 vs 6: split at +4 (only if splitting allowed)
    assert get_deviation(20, 6, 4.0, 'S', is_pair=True, pair_value=10)['action'] == 'P'
    assert get_deviation(20, 6, 3.0, 'S', is_pair=True, pair_value=10) is None
    assert get_deviation(20, 6, 4.0, 'S', is_pair=True, pair_value=10,
                         can_split=False) is None
    # 8,8 vs 10 must NOT trigger the hard-16 stand deviation (basic = split)
    assert get_deviation(16, 10, 3.0, 'P', is_pair=True, pair_value=8) is None
    # insurance
    assert should_take_insurance(11, 3.0) is True
    assert should_take_insurance(11, 2.0) is False
    assert should_take_insurance(10, 5.0) is None

    print("counting.py self-checks passed.")