import os
import sys

from flask import Flask, session, request, jsonify
from flask_cors import CORS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from game.card import Card
    from game.deck import Deck
    from game.hand import Hand
    from game.player import Player
    from game.rules import Rules
    from database.db import create_tables
    from database.stats import save_stats, get_player_stats, get_all_player_stats
except ImportError:
    from backend.game.card import Card
    from backend.game.deck import Deck
    from backend.game.hand import Hand
    from backend.game.player import Player
    from backend.game.rules import Rules
    from backend.database.db import create_tables
    from backend.database.stats import save_stats, get_player_stats, get_all_player_stats

app = Flask(__name__)
app.secret_key = "ace-dev-secret-key"
CORS(app, supports_credentials=True)

# Create database tables on startup if they don't exist
create_tables()

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

def apply_outcome(result):
    """
    Updates win/loss/push counters and chips in the session
    based on the round result string.
    Returns the updated chip count.
    """
    chips  = session.get("chips", 0)
    bet    = session.get("bet", 0)
    wins   = session.get("wins", 0)
    losses = session.get("losses", 0)
    pushes = session.get("pushes", 0)

    if result == "blackjack":
        chips += bet + int(bet * 1.5)
        wins  += 1
    elif result == "win":
        chips += bet * 2
        wins  += 1
    elif result == "push":
        chips += bet
        pushes += 1
    else:
        losses += 1  # bet already deducted at deal time

    session["chips"]  = chips
    session["wins"]   = wins
    session["losses"] = losses
    session["pushes"] = pushes

    return chips

def clear_round():
    """Remove active round data from session after a round ends."""
    for key in ["player_hand", "dealer_hand", "deck", "bet"]:
        session.pop(key, None)

# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------

@app.route("/api/new-game", methods=["POST"])
def new_game():
    """
    Initialize a new session for a player.
    Accepts an optional player name to load saved stats from the database.
    Body: { "name": "Colby" }  (optional)
    """
    data = request.get_json() or {}
    name = data.get("name", "Player")
    name = name.strip().lower()

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
    session["name"]      = name
    session["chips"]     = chips
    session["wins"]      = wins
    session["losses"]    = losses
    session["pushes"]    = pushes
    session["bankrupts"] = bankrupts

    return jsonify({
        "status":   "success",
        "name":     name,
        "chips":    chips,
        "returning": saved is not None,
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

    session["deck"]        = save_deck(deck)
    session["player_hand"] = save_hand(player_hand)
    session["dealer_hand"] = save_hand(dealer_hand)
    session["bet"]         = bet
    session["chips"]       = chips - bet

    return jsonify({
        "status":      "success",
        "player_hand": serialize_hand(player_hand),
        "dealer_hand": serialize_hand(dealer_hand, hide_second=True),
        "chips":       session["chips"],
        "bet":         bet,
    })


@app.route("/api/hit", methods=["POST"])
def hit():
    """Deal one card to the player and check for bust."""
    if "player_hand" not in session:
        return jsonify({ "status": "error", "message": "No active round." }), 400

    deck        = load_deck(session["deck"])
    player_hand = load_hand(session["player_hand"])

    player_hand.add_card(deck.deal())

    session["deck"]        = save_deck(deck)
    session["player_hand"] = save_hand(player_hand)

    bust = player_hand.is_bust()

    # If bust, auto-resolve the round
    if bust:
        chips = apply_outcome("lose")
        _persist_stats()
        clear_round()

    return jsonify({
        "status":      "success",
        "player_hand": serialize_hand(player_hand),
        "bust":        bust,
        "chips":       session.get("chips"),
    })


@app.route("/api/stand", methods=["POST"])
def stand():
    """End the player's turn, run the dealer, and resolve the round."""
    if "player_hand" not in session:
        return jsonify({ "status": "error", "message": "No active round." }), 400

    deck        = load_deck(session["deck"])
    player_hand = load_hand(session["player_hand"])
    dealer_hand = load_hand(session["dealer_hand"])

    Rules.run_dealer(dealer_hand, deck)

    result = Rules.determine_winner(player_hand, dealer_hand)
    chips  = apply_outcome(result)
    _persist_stats()
    clear_round()

    return jsonify({
        "status":      "success",
        "dealer_hand": serialize_hand(dealer_hand),
        "outcome":     result,
        "message":     _outcome_message(result),
        "chips":       chips,
    })


@app.route("/api/double", methods=["POST"])
def double():
    """Double the bet, deal one card, run the dealer, and resolve."""
    if "player_hand" not in session:
        return jsonify({ "status": "error", "message": "No active round." }), 400

    chips = session.get("chips", 0)
    bet   = session.get("bet", 0)

    if bet > chips:
        return jsonify({ "status": "error", "message": "Not enough chips to double down." }), 400

    deck        = load_deck(session["deck"])
    player_hand = load_hand(session["player_hand"])
    dealer_hand = load_hand(session["dealer_hand"])

    # Deduct the extra bet and double it
    session["chips"] = chips - bet
    session["bet"]   = bet * 2

    player_hand.add_card(deck.deal())

    Rules.run_dealer(dealer_hand, deck)

    result = Rules.determine_winner(player_hand, dealer_hand)
    chips  = apply_outcome(result)
    _persist_stats()
    clear_round()

    return jsonify({
        "status":      "success",
        "player_hand": serialize_hand(player_hand),
        "dealer_hand": serialize_hand(dealer_hand),
        "outcome":     result,
        "message":     _outcome_message(result),
        "chips":       chips,
    })


@app.route("/api/hint", methods=["GET"])
def hint():
    """
    Return the basic strategy recommendation for the current hand.
    Placeholder — Reymond will replace this with the full strategy engine.
    """
    if "player_hand" not in session or "dealer_hand" not in session:
        return jsonify({ "status": "error", "message": "No active round." }), 400

    player_hand = load_hand(session["player_hand"])
    dealer_hand = load_hand(session["dealer_hand"])

    player_total  = player_hand.get_value()
    dealer_upcard = dealer_hand.cards[0].get_value()
    is_soft       = player_hand.is_soft()

    # Placeholder logic — replace with strategy.py lookup
    if player_total >= 17:
        action      = "Stand"
        explanation = "You have a strong hand. Standing is the safest play."
    elif player_total <= 11:
        action      = "Hit"
        explanation = "You cannot bust with one card. Always hit on 11 or below."
    elif is_soft:
        action      = "Hit"
        explanation = "Soft hands are flexible. Hitting gives you a chance to improve."
    else:
        action      = "Hit" if player_total < 17 else "Stand"
        explanation = "Basic strategy recommends hitting on hard totals below 17."

    return jsonify({
        "status":      "success",
        "action":      action,
        "explanation": explanation,
        "player_total": player_total,
        "dealer_upcard": dealer_upcard,
    })


@app.route("/api/stats", methods=["GET"])
def stats():
    """Return the current player's session and all-time stats from the database."""
    name = session.get("name", "Player")

    # Session stats
    session_stats = {
        "chips":  session.get("chips", Player.STARTING_CHIPS),
        "wins":   session.get("wins", 0),
        "losses": session.get("losses", 0),
        "pushes": session.get("pushes", 0),
    }


    # All-time stats from database
    saved = get_player_stats(name)
    if saved:
        player_name, chips, wins, losses, pushes, games_played, bankrupts = saved

        if games_played > 0:
            win_percentage = round((wins / games_played) * 100, 2)
            loss_percentage = round((losses / games_played) * 100, 2)
            push_percentage = round((pushes / games_played) * 100, 2)
        else:
            win_percentage = 0
            loss_percentage = 0
            push_percentage = 0

        alltime_stats = {
            "games_played": games_played,
            "wins":         wins,
            "losses":       losses,
            "pushes":       pushes,
            "bankrupts":    bankrupts,
            "chips":        chips,
            "win_percentage": win_percentage,
            "loss_percentage": loss_percentage,
            "push_percentage": push_percentage,
        }
    else:
        alltime_stats = None

    return jsonify({
        "status":       "success",
        "name":         name,
        "session":      session_stats,
        "all_time":     alltime_stats,
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
    players = get_all_player_stats()

    leaderboard = []

    for player in players:
        player_name, chips, wins, losses, pushes, games_played, bankrupts = player

        if games_played > 0:
            win_percentage = round((wins / games_played) * 100, 2)
        else:
            win_percentage = 0

        leaderboard.append({
            "player_name": player_name,
            "chips": chips,
            "wins": wins,
            "losses": losses,
            "pushes": pushes,
            "games_played": games_played,
            "bankrupts": bankrupts,
            "win_percentage": win_percentage
        })

    return jsonify({"leaderboard": leaderboard})


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _persist_stats():
    """Write current session stats to the database."""
    chips = session.get("chips", Player.STARTING_CHIPS)
    bankrupts = session.get("bankrupts", 0)

    if chips <= 0:
       bankrupts += 1
       chips = Player.STARTING_CHIPS
       session["chips"] = chips
       session["bankrupts"] = bankrupts

    save_stats(
       session.get("name", "Player"),
       chips,
       session.get("wins", 0),
       session.get("losses", 0),
       session.get("pushes", 0),
       bankrupts,
    )

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