import os
import sys

from flask import Flask, session, request, jsonify
from flask_cors import CORS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Put project root on sys.path so package imports resolve when running
# `python app.py` from inside the `backend/` folder.
PROJECT_ROOT = os.path.dirname(BASE_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Use package-style imports (rely on PROJECT_ROOT being on sys.path)
from backend.game.blackjack.card import Card
from backend.game.blackjack.deck import Deck
from backend.game.blackjack.hand import Hand
from backend.game.blackjack.player import Player
from backend.game.blackjack.rules import Rules
from backend.game.roulette.wheel import Wheel
from backend.game.roulette.rules import Rules as RouletteRules
from backend.game.slots.machine import SlotMachine
from backend.game.slots.rules import Rules as SlotRules
from backend.ai.roulette_advise import RouletteAdvisor
from database.db import create_tables
from database.stats import save_stats, get_player_stats, get_all_player_stats, save_slot_spin, get_slots_stats, save_roulette_spin, get_roulette_stats, get_all_roulette_stats,  get_all_slots_stats

app = Flask(__name__)
app.secret_key = "ace-dev-secret-key"
CORS(app, supports_credentials=True)

# Create database tables on startup if they don't exist
try:
    create_tables()
except ValueError as exc:
    print(f"Database unavailable; stats persistence disabled: {exc}")

# Roulette wheel instance — stateless, created once at startup
_wheel = Wheel()

# Slot machine instance — stateless, created once at startup
_slot_machine = SlotMachine()
_roulette_advisor = RouletteAdvisor()

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def serialize_hand(hand, hide_second=False):
    """Convert a Hand object to a JSON-serializable dict."""
    return {
        "cards":     hand.short_names(hide_second=hide_second),
        "total":     hand.get_value() if not hide_second else "?",
        "bust":      hand.is_bust(),
        "blackjack": hand.is_blackjack(),
    }

def load_hand(card_list):
    """Rebuild a Hand object from session-stored card dicts."""
    hand = Hand()
    for c in card_list:
        hand.add_card(Card(c["suit"], c["rank"]))
    return hand

def load_deck(card_list):
    """Rebuild a Deck from session-stored card dicts."""
    deck = Deck()
    deck.cards = [Card(c["suit"], c["rank"]) for c in card_list]
    deck.dealt = []
    return deck

def save_deck(deck):
    return [{"suit": c.suit, "rank": c.rank} for c in deck.cards]

def save_hand(hand):
    return [{"suit": c.suit, "rank": c.rank} for c in hand.cards]

def save_player_hands(hands):
    return [save_hand(hand) for hand in hands]

def load_player_hands(hands_list):
    return [load_hand(card_list) for card_list in hands_list]

def get_player_hands():
    return (load_player_hands(session["player_hands"]) if "player_hands" in session
            else ([load_hand(session["player_hand"])] if "player_hand" in session else []))

def get_hand_statuses():
    statuses = session.get("hand_statuses")
    hands = session.get("player_hands")
    return statuses if statuses and hands and len(statuses) == len(hands) else ["active"] * len(get_player_hands())

def get_active_hand_index():
    return next((i for i, s in enumerate(get_hand_statuses()) if s == "active"), session.get("active_hand_index", 0))

def persist_player_hands(hands, bets, active_index=0, statuses=None):
    session["player_hands"] = save_player_hands(hands)
    session["hand_bets"] = bets
    session["bet"] = sum(bets)
    session["active_hand_index"] = active_index
    session["hand_statuses"] = statuses if statuses is not None else ["active"] + ["pending"] * (len(hands) - 1)

def advance_to_next_hand(statuses, current_index):
    for idx in range(current_index + 1, len(statuses)):
        if statuses[idx] == "pending":
            return idx
    return None

def apply_hand_outcome(result, bet):
    chips = session.get("chips", 0)

    if result == "blackjack":
        chips += bet + int(bet * 1.5)
        session["wins"] = session.get("wins", 0) + 1
    elif result == "win":
        chips += bet * 2
        session["wins"] = session.get("wins", 0) + 1
    elif result == "push":
        chips += bet
        session["pushes"] = session.get("pushes", 0) + 1
    else:
        session["losses"] = session.get("losses", 0) + 1

    session["chips"] = chips

def resolve_round(player_hands, dealer_hand, hand_bets, deck):
    Rules.run_dealer(dealer_hand, deck)
    results = []
    for hand, bet in zip(player_hands, hand_bets):
        result = Rules.determine_winner(hand, dealer_hand)
        results.append(result)
        apply_hand_outcome(result, bet)
    return results

def summarize_split_outcome(results):
    wins = sum(1 for r in results if r in ("win", "blackjack"))
    losses = results.count("lose")

    if wins > losses:
        return "win"
    if losses > wins:
        return "lose"
    return "push"

def split_outcome_message(results):
    if len(results) == 1:
        return _outcome_message(results[0])

    wins = sum(1 for r in results if r in ("win", "blackjack"))
    pushes = results.count("push")
    losses = results.count("lose")

    parts = []
    if wins:
        parts.append(f"{wins} win{'s' if wins != 1 else ''}")
    if pushes:
        parts.append(f"{pushes} push{'es' if pushes != 1 else ''}")
    if losses:
        parts.append(f"{losses} loss{'es' if losses != 1 else ''}")

    return ", ".join(parts).capitalize() + "."

def apply_outcome(result):
    """
    Updates win/loss/push counters and chips in the session
    based on the round result string.
    Returns the updated chip count.
    """
    chips = session.get("chips", 0)
    bet = session.get("bet", 0)
    wins, losses, pushes = session.get("wins", 0), session.get("losses", 0), session.get("pushes", 0)
    if result == "blackjack":
        chips += bet + int(bet * 1.5); wins += 1
    elif result == "win":
        chips += bet * 2; wins += 1
    elif result == "push":
        chips += bet; pushes += 1
    else:
        losses += 1
    session.update({"chips": chips, "wins": wins, "losses": losses, "pushes": pushes})
    return chips

def clear_round():
    """Remove active round data from session after a round ends."""
    for key in ["player_hand", "player_hands", "hand_bets", "hand_statuses", "active_hand_index", "dealer_hand", "deck", "bet"]:
        session.pop(key, None)

# ------------------------------------------------------------------
# Routes — Blackjack
# ------------------------------------------------------------------

@app.route("/api/new-game", methods=["POST"])
def new_game():
    """
    Initialize a new session for a player.
    Accepts an optional player name to load saved stats from the database.
    Body: { "name": "Colby" }  (optional)
    """
    data = request.get_json(silent=True) or {}
    name = data.get("name", "Player")
    name = name.strip().lower()

    tutorial_mode = data.get("tutorial", False)
    restore_session = data.get("restore_session", False)

    if tutorial_mode:
        player_name = "Tutorial"
        chips = Player.STARTING_CHIPS
        wins = 0
        losses = 0
        pushes = 0
        bankrupts = 0
    elif restore_session:
        player_name = name
        chips = data.get("chips", Player.STARTING_CHIPS)
        wins = data.get("wins", 0)
        losses = data.get("losses", 0)
        pushes = data.get("pushes", 0)
        bankrupts = data.get("bankrupts", 0)
    else:
        saved = get_player_stats(name)

        if saved:
            player_name, chips, wins, losses, pushes, games_played, bankrupts = saved
            # Reset chips if the player was bankrupt last session
            if chips <= 0:
                chips = Player.STARTING_CHIPS
        else:
            chips     = Player.STARTING_CHIPS
            wins      = 0
            losses    = 0
            pushes    = 0
            bankrupts = 0

    session.clear()
    session["name"]      = player_name
    session["chips"]     = chips
    session["wins"]      = wins
    session["losses"]    = losses
    session["pushes"]    = pushes
    session["bankrupts"] = bankrupts
    if tutorial_mode:
        session["tutorial"] = True
    else:
        session.pop("tutorial", None)

    returning = False
    if not tutorial_mode and not restore_session:
        returning = saved is not None

    return jsonify({
        "status":   "success",
        "name":     player_name,
        "chips":    chips,
        "returning": returning,
    })


@app.route("/api/deal", methods=["POST"])
def deal():
    """
    Place a bet and deal the opening hand.
    Body: { "bet": 100 }
    """
    data  = request.get_json() or {}
    bet   = data.get("bet", 0)
    chips = session.get("chips", Player.STARTING_CHIPS)

    if bet <= 0 or bet > chips:
        return jsonify({ "status": "error", "message": "Invalid bet amount." }), 400

    deck        = Deck()
    player_hand = Hand()
    dealer_hand = Hand()

    player_hand.add_card(deck.deal())
    dealer_hand.add_card(deck.deal())
    player_hand.add_card(deck.deal())
    dealer_hand.add_card(deck.deal())

    session["deck"]          = save_deck(deck)
    persist_player_hands([player_hand], [bet], active_index=0)
    session["dealer_hand"] = save_hand(dealer_hand)
    session["chips"]       = chips - bet

    return jsonify({
        "status":         "success",
        "player_hand":    serialize_hand(player_hand),
        "dealer_hand":    serialize_hand(dealer_hand, hide_second=True),
        "chips":          session["chips"],
        "bet":            bet,
        "hand_count":     1,
        "active_hand_index": 0,
        "can_split":      player_hand.is_pair(),
    })


@app.route("/api/hit", methods=["POST"])
def hit():
    """Deal one card to the active player hand and continue play."""
    if "player_hands" not in session and "player_hand" not in session:
        return jsonify({ "status": "error", "message": "No active round." }), 400

    deck = load_deck(session["deck"])
    player_hands = get_player_hands()
    hand_bets = session.get("hand_bets", [session.get("bet", 0)])
    statuses = get_hand_statuses()
    active_index = get_active_hand_index()

    player_hand = player_hands[active_index]
    player_hand.add_card(deck.deal())

    if player_hand.is_bust():
        statuses[active_index] = "bust"
        next_index = advance_to_next_hand(statuses, active_index)

        if next_index is not None:
            statuses[next_index] = "active"
            persist_player_hands(player_hands, hand_bets, next_index, statuses)
            session["deck"] = save_deck(deck)
            return jsonify({
                "status":           "success",
                "player_hand":      serialize_hand(player_hands[next_index]),
                "hand_count":       len(player_hands),
                "active_hand_index": next_index,
                "can_split":        False,
                "bust":             True,
                "chips":            session.get("chips"),
            })

        dealer_hand = load_hand(session["dealer_hand"])
        results = resolve_round(player_hands, dealer_hand, hand_bets, deck)
        summary = summarize_split_outcome(results)
        message = split_outcome_message(results)
        _persist_stats()
        bankrupt = session.get("chips", 0) <= 0
        if bankrupt:
            message = f"{message} You went bankrupt!"
        clear_round()

        return jsonify({
            "status":      "success",
            "player_hand": serialize_hand(player_hand),
            "dealer_hand": serialize_hand(dealer_hand),
            "outcome":     summary,
            "message":     message,
            "chips":       session.get("chips"),
            "bust":        True,
            "bankrupt":    bankrupt,
        })

    persist_player_hands(player_hands, hand_bets, active_index, statuses)
    session["deck"] = save_deck(deck)

    return jsonify({
        "status":           "success",
        "player_hand":      serialize_hand(player_hand),
        "hand_count":       len(player_hands),
        "active_hand_index": active_index,
        "can_split":        False,
        "bust":             False,
        "chips":            session.get("chips"),
    })


@app.route("/api/stand", methods=["POST"])
def stand():
    """End the player's turn for the current hand and continue or resolve."""
    if "player_hands" not in session and "player_hand" not in session:
        return jsonify({ "status": "error", "message": "No active round." }), 400

    deck = load_deck(session["deck"])
    player_hands = get_player_hands()
    hand_bets = session.get("hand_bets", [session.get("bet", 0)])
    statuses = get_hand_statuses()
    active_index = get_active_hand_index()

    statuses[active_index] = "stood"
    next_index = advance_to_next_hand(statuses, active_index)

    if next_index is not None:
        statuses[next_index] = "active"
        persist_player_hands(player_hands, hand_bets, next_index, statuses)
        session["deck"] = save_deck(deck)
        return jsonify({
            "status":           "success",
            "player_hand":      serialize_hand(player_hands[next_index]),
            "hand_count":       len(player_hands),
            "active_hand_index": next_index,
            "can_split":        False,
            "chips":            session.get("chips"),
        })

    dealer_hand = load_hand(session["dealer_hand"])
    results = resolve_round(player_hands, dealer_hand, hand_bets, deck)
    summary = summarize_split_outcome(results)
    message = split_outcome_message(results)
    _persist_stats()
    bankrupt = session.get("chips", 0) <= 0
    if bankrupt:
        message = f"{message} You went bankrupt!"
    clear_round()

    return jsonify({
        "status":      "success",
        "dealer_hand": serialize_hand(dealer_hand),
        "outcome":     summary,
        "message":     message,
        "chips":       session.get("chips"),
        "bankrupt":    bankrupt,
    })


@app.route("/api/double", methods=["POST"])
def double():
    """Double the current hand's bet, deal one card, and continue or resolve."""
    if "player_hands" not in session and "player_hand" not in session:
        return jsonify({ "status": "error", "message": "No active round." }), 400

    deck = load_deck(session["deck"])
    player_hands = get_player_hands()
    hand_bets = session.get("hand_bets", [session.get("bet", 0)])
    statuses = get_hand_statuses()
    active_index = get_active_hand_index()
    player_hand = player_hands[active_index]
    current_bet = hand_bets[active_index]
    chips = session.get("chips", 0)

    if current_bet > chips:
        return jsonify({ "status": "error", "message": "Not enough chips to double down." }), 400
    if player_hand.card_count() != 2:
        return jsonify({ "status": "error", "message": "Double down is only allowed on the first two cards." }), 400

    session["chips"] = chips - current_bet
    hand_bets[active_index] = current_bet * 2

    player_hand.add_card(deck.deal())
    if player_hand.is_bust():
        statuses[active_index] = "bust"
    else:
        statuses[active_index] = "stood"

    next_index = advance_to_next_hand(statuses, active_index)
    if next_index is not None:
        statuses[next_index] = "active"
        persist_player_hands(player_hands, hand_bets, next_index, statuses)
        session["deck"] = save_deck(deck)
        return jsonify({
            "status":           "success",
            "player_hand":      serialize_hand(player_hands[next_index]),
            "hand_count":       len(player_hands),
            "active_hand_index": next_index,
            "can_split":        False,
            "chips":            session.get("chips"),
        })

    dealer_hand = load_hand(session["dealer_hand"])
    results = resolve_round(player_hands, dealer_hand, hand_bets, deck)
    summary = summarize_split_outcome(results)
    message = split_outcome_message(results)
    _persist_stats()
    bankrupt = session.get("chips", 0) <= 0
    if bankrupt:
        message = f"{message} You went bankrupt!"
    clear_round()

    return jsonify({
        "status":      "success",
        "player_hand": serialize_hand(player_hand),
        "dealer_hand": serialize_hand(dealer_hand),
        "outcome":     summary,
        "message":     message,
        "chips":       session.get("chips"),
        "bankrupt":    bankrupt,
    })


@app.route("/api/split", methods=["POST"])
def split():
    """Split a starting pair into two hands and continue play."""
    if "player_hands" not in session and "player_hand" not in session:
        return jsonify({ "status": "error", "message": "No active round." }), 400

    player_hands = get_player_hands()
    hand_bets = session.get("hand_bets", [session.get("bet", 0)])
    if len(player_hands) != 1 or player_hands[0].card_count() != 2:
        return jsonify({ "status": "error", "message": "Split is only allowed on a fresh pair." }), 400

    player_hand = player_hands[0]
    if not player_hand.is_pair():
        return jsonify({ "status": "error", "message": "Split is only allowed when both cards match." }), 400

    bet_amount = hand_bets[0]
    chips = session.get("chips", 0)
    if bet_amount > chips:
        return jsonify({ "status": "error", "message": "Not enough chips to split." }), 400

    deck = load_deck(session["deck"])
    first_card, second_card = player_hand.cards
    hand1 = Hand(); hand1.add_card(first_card)
    hand2 = Hand(); hand2.add_card(second_card)
    hand1.add_card(deck.deal())
    hand2.add_card(deck.deal())

    session["chips"] = chips - bet_amount
    persist_player_hands([hand1, hand2], [bet_amount, bet_amount], active_index=0, statuses=["active", "pending"])
    session["deck"] = save_deck(deck)

    return jsonify({
        "status":           "success",
        "player_hand":      serialize_hand(hand1),
        "hand_count":       2,
        "active_hand_index": 0,
        "can_split":        False,
        "chips":            session.get("chips"),
    })


from backend.ai.advise import Advisor

_advisor = Advisor()

@app.route("/api/hint", methods=["GET"])
def hint():
    """Return the basic strategy recommendation for the current hand."""
    if "dealer_hand" not in session:
        return jsonify({ "status": "error", "message": "No active round." }), 400

    player_hands = get_player_hands()
    if not player_hands:
        return jsonify({ "status": "error", "message": "No active round." }), 400

    active_index = get_active_hand_index()
    player_hand = player_hands[active_index]
    dealer_hand = load_hand(session["dealer_hand"])

    # Dealer upcard is always the first card
    dealer_upcard = dealer_hand.cards[0]

    # Can only double/split on the opening two cards
    can_double = player_hand.card_count() == 2
    can_split  = player_hand.is_pair()

    rec = _advisor.recommend(
        player_hand,
        dealer_upcard,
        can_double=can_double,
        can_split=can_split,
    )

    return jsonify({
        "status":      "success",
        "action":      rec["action_name"],
        "explanation": rec["reason"],
        "raw_action":  rec["action"],
    })


# ------------------------------------------------------------------
# Routes — Roulette
# ------------------------------------------------------------------

@app.route("/api/roulette/advice", methods=["POST"])
def roulette_advice():
    """Explain the selected roulette bet before the player spins."""
    data = request.get_json() or {}
    bet_type = data.get("bet_type")
    bet_value = data.get("bet_value")
    amount = data.get("amount", 0)
    chips = session.get("chips", Player.STARTING_CHIPS)

    try:
        amount = int(amount)
        if bet_type in ("straight", "dozen") and bet_value != "00":
            bet_value = int(bet_value)
        RouletteRules.validate_bet(bet_type, bet_value, _wheel)
    except (TypeError, ValueError) as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400

    if amount <= 0:
        return jsonify({"status": "error", "message": "Place a bet first."}), 400

    advice = _roulette_advisor.recommend(
        chips, amount, bet_type, bet_value, session.get("roulette_history", [])
    )
    return jsonify({"status": "success", "advice": advice})

@app.route("/api/roulette/spin", methods=["POST"])
def roulette_spin():
    """
    Place a bet, spin the wheel, and resolve the result in one call.
    Stateless — no session data persists between spins beyond chip balance.

    Body: {
        "bet_type":  "straight" | "color" | "parity" | "dozen",
        "bet_value": <int|str depending on bet_type>,
        "amount":    int
    }
    """
    data      = request.get_json() or {}
    bet_type  = data.get("bet_type")
    bet_value = data.get("bet_value")
    amount    = data.get("amount", 0)
    chips     = session.get("chips", Player.STARTING_CHIPS)


    try:
        amount = int(amount)

        if bet_type in ("straight", "dozen") and bet_value != "00":
            bet_value = int(bet_value)
    except (TypeError, ValueError):
        return jsonify({ "status": "error", "message": "Invalid bet amount or value." }), 400
        
    if amount <= 0 or amount > chips:
        return jsonify({ "status": "error", "message": "Invalid bet amount." }), 400

    try:
        RouletteRules.validate_bet(bet_type, bet_value, _wheel)
    except ValueError as e:
        return jsonify({ "status": "error", "message": str(e) }), 400

    # Deduct the bet up front, same pattern as Blackjack's deal route
    session["chips"] = chips - amount

    number = _wheel.spin()
    result = RouletteRules.resolve_bet(bet_type, bet_value, amount, _wheel, number)

    history = session.get("roulette_history", [])
    history.append({
        "number": number,
        "color": result["color"],
        "dozen": (number - 1) // 12 + 1 if isinstance(number, int) and number else None,
        "is_odd": isinstance(number, int) and number != 0 and number % 2 == 1,
        "is_even": isinstance(number, int) and number != 0 and number % 2 == 0,
        "amount": amount,
        "won": result["won"],
    })
    session["roulette_history"] = history[-10:]
    advice_evaluation = _roulette_advisor.evaluate({
        **result,
        "bet_type": bet_type,
        "bet_value": bet_value,
        "amount": amount,
    })

    new_chips = session["chips"] + result["total_return"]
    session["chips"] = new_chips

    # Save updated chip count to regular player stats
    _persist_stats()
    
    # Save roulette-specific stats separately
    save_roulette_spin(
        session.get("name", "Player"),
        bet_type,
        amount,
        result["total_return"],
        result["payout"],
        result["won"]
    )

    return jsonify({
        "status":       "success",
        "number":       result["number"],
        "color":        result["color"],
        "won":          result["won"],
        "bet_type":     bet_type,
        "bet_value":    bet_value,
        "amount":       amount,
        "payout":       result["payout"],
        "total_return": result["total_return"],
        "chips":        new_chips,
        "advice_evaluation": advice_evaluation,
    })

@app.route("/api/roulette/stats", methods=["GET"])
def roulette_stats():
    """Return roulette-specific stats for the current player."""
    name = session.get("name", "Player")

    saved = get_roulette_stats(name)

    if saved:
        (
            player_name,
            spins,
            wins,
            losses,
            total_wagered,
            total_payout,
            biggest_win,
            straight_bets,
            color_bets,
            parity_bets,
            dozen_bets,
        ) = saved
    else:
        player_name = name
        spins = 0
        wins = 0
        losses = 0
        total_wagered = 0
        total_payout = 0
        biggest_win = 0
        straight_bets = 0
        color_bets = 0
        parity_bets = 0
        dozen_bets = 0

    if spins > 0:
        win_percentage = round((wins / spins) * 100, 2)
    else:
        win_percentage = 0

    net_profit = total_payout - total_wagered

    return jsonify({
        "status": "success",
        "player_name": player_name,
        "spins": spins,
        "wins": wins,
        "losses": losses,
        "total_wagered": total_wagered,
        "total_payout": total_payout,
        "biggest_win": biggest_win,
        "net_profit": net_profit,
        "win_percentage": win_percentage,
        "straight_bets": straight_bets,
        "color_bets": color_bets,
        "parity_bets": parity_bets,
        "dozen_bets": dozen_bets,
    })


# ------------------------------------------------------------------
# Routes — Slots
# ------------------------------------------------------------------

@app.route("/api/slots/spin", methods=["POST"])
def slots_spin():
    """
    Place a chosen bet, spin the slot machine, and resolve the result.

    Body example:
    {
        "amount": 100
    }
    """
    data = request.get_json() or {}

    # This is the bet amount chosen by the player/frontend
    amount = data.get("amount", 0)

    # Current player chips from session
    chips = session.get("chips", Player.STARTING_CHIPS)

    # Make sure amount is a number
    try:
        amount = int(amount)
    except (TypeError, ValueError):
        return jsonify({
            "status": "error",
            "message": "Invalid bet amount."
        }), 400

    # Check if the bet is allowed and player has enough chips
    try:
        SlotRules.validate_bet(amount, chips)
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

    # Deduct the chosen bet
    session["chips"] = chips - amount

    # Spin the slots and calculate result
    result = SlotRules.resolve_spin(_slot_machine, amount)

    # Add winnings/return back to chips
    new_chips = session["chips"] + result["total_return"]
    session["chips"] = new_chips

    # Save updated chips/stats to database
    _persist_stats()
    
    # Save slots-specific stats separately
    save_slot_spin(
        session.get("name", "Player"),
        amount,
        result["total_return"],
        result["payout"],
        result["won"]
    )

    return jsonify({
        "status": "success",
        "game": "slots",
        "reels": result["reels"],
        "won": result["won"],
        "result": result["result"],
        "amount": amount,
        "multiplier": result["multiplier"],
        "payout": result["payout"],
        "total_return": result["total_return"],
        "chips": new_chips,
        "message": result["message"],
    })

@app.route("/api/slots/stats", methods=["GET"])
def slots_stats():
    """Return slots-specific stats for the current player."""
    name = session.get("name", "Player")

    saved = get_slots_stats(name)

    if saved:
        player_name, spins, wins, losses, total_wagered, total_payout, biggest_win = saved
    else:
        player_name = name
        spins = 0
        wins = 0
        losses = 0
        total_wagered = 0
        total_payout = 0
        biggest_win = 0

    if spins > 0:
        win_percentage = round((wins / spins) * 100, 2)
    else:
        win_percentage = 0

    net_profit = total_payout - total_wagered

    return jsonify({
        "status": "success",
        "player_name": player_name,
        "spins": spins,
        "wins": wins,
        "losses": losses,
        "total_wagered": total_wagered,
        "total_payout": total_payout,
        "biggest_win": biggest_win,
        "net_profit": net_profit,
        "win_percentage": win_percentage,
    })

# ------------------------------------------------------------------
# Routes — Stats / Database
# ------------------------------------------------------------------

@app.route("/api/stats", methods=["GET"])
def stats():
    """Return shared, Blackjack, Slots, and Roulette stats for the current player."""
    name = session.get("name", "Player")

    player_saved = get_player_stats(name)
    slots_saved = get_slots_stats(name)
    roulette_saved = get_roulette_stats(name)

    # Shared chip balance and Blackjack stats
    if player_saved:
        (
            player_name,
            chips,
            blackjack_wins,
            blackjack_losses,
            blackjack_pushes,
            blackjack_games,
            bankrupts,
        ) = player_saved
    else:
        player_name = name
        chips = session.get("chips", Player.STARTING_CHIPS)
        blackjack_wins = 0
        blackjack_losses = 0
        blackjack_pushes = 0
        blackjack_games = 0
        bankrupts = 0

    if blackjack_games > 0:
        blackjack_win_percentage = round(
            (blackjack_wins / blackjack_games) * 100, 2
        )
        blackjack_loss_percentage = round(
            (blackjack_losses / blackjack_games) * 100, 2
        )
        blackjack_push_percentage = round(
            (blackjack_pushes / blackjack_games) * 100, 2
        )
    else:
        blackjack_win_percentage = 0
        blackjack_loss_percentage = 0
        blackjack_push_percentage = 0

    blackjack_stats = {
        "games_played": blackjack_games,
        "wins": blackjack_wins,
        "losses": blackjack_losses,
        "pushes": blackjack_pushes,
        "win_percentage": blackjack_win_percentage,
        "loss_percentage": blackjack_loss_percentage,
        "push_percentage": blackjack_push_percentage,
    }

    # Keep all_time so the current frontend does not break
    if player_saved:
        alltime_stats = {
            "games_played": blackjack_games,
            "wins": blackjack_wins,
            "losses": blackjack_losses,
            "pushes": blackjack_pushes,
            "bankrupts": bankrupts,
            "chips": chips,
            "win_percentage": blackjack_win_percentage,
            "loss_percentage": blackjack_loss_percentage,
            "push_percentage": blackjack_push_percentage,
        }
    else:
        alltime_stats = None

    # Slots stats
    if slots_saved:
        (
            _slot_player_name,
            slot_spins,
            slot_wins,
            slot_losses,
            slot_total_wagered,
            slot_total_payout,
            slot_biggest_win,
        ) = slots_saved
    else:
        slot_spins = 0
        slot_wins = 0
        slot_losses = 0
        slot_total_wagered = 0
        slot_total_payout = 0
        slot_biggest_win = 0

    slot_win_percentage = (
        round((slot_wins / slot_spins) * 100, 2)
        if slot_spins > 0
        else 0
    )

    slots_stats = {
        "spins": slot_spins,
        "wins": slot_wins,
        "losses": slot_losses,
        "total_wagered": slot_total_wagered,
        "total_payout": slot_total_payout,
        "biggest_win": slot_biggest_win,
        "net_profit": slot_total_payout - slot_total_wagered,
        "win_percentage": slot_win_percentage,
    }

    # Roulette stats
    if roulette_saved:
        (
            _roulette_player_name,
            roulette_spins,
            roulette_wins,
            roulette_losses,
            roulette_total_wagered,
            roulette_total_payout,
            roulette_biggest_win,
            straight_bets,
            color_bets,
            parity_bets,
            dozen_bets,
        ) = roulette_saved
    else:
        roulette_spins = 0
        roulette_wins = 0
        roulette_losses = 0
        roulette_total_wagered = 0
        roulette_total_payout = 0
        roulette_biggest_win = 0
        straight_bets = 0
        color_bets = 0
        parity_bets = 0
        dozen_bets = 0

    roulette_win_percentage = (
        round((roulette_wins / roulette_spins) * 100, 2)
        if roulette_spins > 0
        else 0
    )

    roulette_stats = {
        "spins": roulette_spins,
        "wins": roulette_wins,
        "losses": roulette_losses,
        "total_wagered": roulette_total_wagered,
        "total_payout": roulette_total_payout,
        "biggest_win": roulette_biggest_win,
        "net_profit": roulette_total_payout - roulette_total_wagered,
        "win_percentage": roulette_win_percentage,
        "straight_bets": straight_bets,
        "color_bets": color_bets,
        "parity_bets": parity_bets,
        "dozen_bets": dozen_bets,
    }

    session_stats = {
        "chips": session.get("chips", Player.STARTING_CHIPS),
        "wins": session.get("wins", 0),
        "losses": session.get("losses", 0),
        "pushes": session.get("pushes", 0),
    }

    return jsonify({
        "status": "success",
        "name": player_name,
        "session": session_stats,

        # Shared player information
        "shared": {
            "chips": chips,
            "bankrupts": bankrupts,
        },

        # Keep old response for the existing frontend
        "all_time": alltime_stats,

        # New game-specific sections
        "blackjack": blackjack_stats,
        "slots": slots_stats,
        "roulette": roulette_stats,
    })


@app.route("/api/save", methods=["POST"])
def save():
    """
    Manually save the current session stats to the database.
    Called when the player exits or cashes out.
    """
    _persist_stats()
    return jsonify({ "status": "success", "message": "Stats saved." })


@app.route("/api/leaderboard", methods=["GET"])
def leaderboard():
    """Return shared chips and game-specific stats for every player."""
    players = get_all_player_stats()
    all_slots = get_all_slots_stats()
    all_roulette = get_all_roulette_stats()

    # Make lookup dictionaries using player name
    slots_by_player = {
        row[0].lower(): row
        for row in all_slots
    }

    roulette_by_player = {
        row[0].lower(): row
        for row in all_roulette
    }

    leaderboard_data = []

    for player in players:
        (
            player_name,
            chips,
            blackjack_wins,
            blackjack_losses,
            blackjack_pushes,
            blackjack_games,
            bankrupts,
        ) = player

        if blackjack_games > 0:
            blackjack_win_percentage = round(
                (blackjack_wins / blackjack_games) * 100, 2
            )
        else:
            blackjack_win_percentage = 0

        # Get this player's Slots stats
        slot_row = slots_by_player.get(player_name.lower())

        if slot_row:
            (
                _slot_name,
                slot_spins,
                slot_wins,
                slot_losses,
                slot_total_wagered,
                slot_total_payout,
                slot_biggest_win,
            ) = slot_row
        else:
            slot_spins = 0
            slot_wins = 0
            slot_losses = 0
            slot_total_wagered = 0
            slot_total_payout = 0
            slot_biggest_win = 0

        slot_win_percentage = (
            round((slot_wins / slot_spins) * 100, 2)
            if slot_spins > 0
            else 0
        )

        # Get this player's Roulette stats
        roulette_row = roulette_by_player.get(player_name.lower())

        if roulette_row:
            (
                _roulette_name,
                roulette_spins,
                roulette_wins,
                roulette_losses,
                roulette_total_wagered,
                roulette_total_payout,
                roulette_biggest_win,
                straight_bets,
                color_bets,
                parity_bets,
                dozen_bets,
            ) = roulette_row
        else:
            roulette_spins = 0
            roulette_wins = 0
            roulette_losses = 0
            roulette_total_wagered = 0
            roulette_total_payout = 0
            roulette_biggest_win = 0
            straight_bets = 0
            color_bets = 0
            parity_bets = 0
            dozen_bets = 0

        roulette_win_percentage = (
            round((roulette_wins / roulette_spins) * 100, 2)
            if roulette_spins > 0
            else 0
        )

        leaderboard_data.append({
            # Existing fields used by the current frontend
            "player_name": player_name,
            "chips": chips,
            "wins": blackjack_wins,
            "losses": blackjack_losses,
            "pushes": blackjack_pushes,
            "games_played": blackjack_games,
            "bankrupts": bankrupts,
            "win_percentage": blackjack_win_percentage,

            # New Blackjack section
            "blackjack": {
                "games_played": blackjack_games,
                "wins": blackjack_wins,
                "losses": blackjack_losses,
                "pushes": blackjack_pushes,
                "win_percentage": blackjack_win_percentage,
            },

            # New Slots section
            "slots": {
                "spins": slot_spins,
                "wins": slot_wins,
                "losses": slot_losses,
                "total_wagered": slot_total_wagered,
                "total_payout": slot_total_payout,
                "biggest_win": slot_biggest_win,
                "net_profit": slot_total_payout - slot_total_wagered,
                "win_percentage": slot_win_percentage,
            },

            # New Roulette section
            "roulette": {
                "spins": roulette_spins,
                "wins": roulette_wins,
                "losses": roulette_losses,
                "total_wagered": roulette_total_wagered,
                "total_payout": roulette_total_payout,
                "biggest_win": roulette_biggest_win,
                "net_profit": (
                    roulette_total_payout - roulette_total_wagered
                ),
                "win_percentage": roulette_win_percentage,
                "straight_bets": straight_bets,
                "color_bets": color_bets,
                "parity_bets": parity_bets,
                "dozen_bets": dozen_bets,
            },
        })

    return jsonify({
        "status": "success",
        "leaderboard": leaderboard_data,
    })


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _persist_stats():
    """Write current session stats to the database."""
    if session.get("tutorial", False):
        return

    chips = session.get("chips", Player.STARTING_CHIPS)
    bankrupts = session.get("bankrupts", 0)
    if chips <= 0:
        bankrupts += 1
        chips = 0
        session.update({"chips": chips, "bankrupts": bankrupts})
    save_stats(session.get("name", "Player"), chips, session.get("wins", 0), session.get("losses", 0), session.get("pushes", 0), bankrupts)

def _outcome_message(result):
    messages = {
        "blackjack": "Blackjack! You win 3:2!",
        "win":       "You win!",
        "push":      "Push — bet returned.",
        "lose":      "You lose.",
    }
    return messages.get(result, "Round over.")


# ------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
