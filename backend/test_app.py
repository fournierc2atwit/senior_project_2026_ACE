import unittest
from unittest.mock import patch

from backend.app import app
from backend.game.blackjack.card import Card


def scripted_deck(*deal_order):
    """Create a deck class that deals the supplied cards in order."""
    class ScriptedDeck:
        def __init__(self):
            self.cards = [Card("Clubs", "2") for _ in range(20)] + list(reversed(deal_order))
            self.dealt = []
            self.reshuffled = False

        def deal(self):
            card = self.cards.pop()
            self.dealt.append(card)
            return card

    return ScriptedDeck


class BackendApiTestCase(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_new_game_returns_initial_chips(self):
        response = self.client.post("/api/new-game", json={"tutorial": True})
        self.assertEqual(200, response.status_code)

        data = response.get_json()
        self.assertEqual("success", data["status"])
        self.assertEqual(1000, data["chips"])

    def test_new_game_initializes_an_unknown_player(self):
        with patch("backend.app.get_player_stats", return_value=None):
            response = self.client.post("/api/new-game", json={"name": "New Player"})

        data = response.get_json()
        self.assertEqual(200, response.status_code)
        self.assertEqual("new player", data["name"])
        self.assertEqual(1000, data["chips"])
        self.assertFalse(data["returning"])

    def test_new_game_rejects_non_text_name(self):
        response = self.client.post("/api/new-game", json={"name": 42})

        self.assertEqual(400, response.status_code)
        self.assertEqual("error", response.get_json()["status"])

    def test_deal_rejects_non_integer_bet(self):
        response = self.client.post("/api/deal", json={"bet": "50"})

        self.assertEqual(400, response.status_code)
        self.assertEqual("error", response.get_json()["status"])

    def test_deal_invalid_bet_returns_400(self):
        self.client.post("/api/new-game", json={"tutorial": True})
        response = self.client.post("/api/deal", json={"bet": 0})

        self.assertEqual(400, response.status_code)
        data = response.get_json()
        self.assertEqual("error", data["status"])
        self.assertIn("Invalid bet", data["message"])

    def test_hit_without_round_returns_400(self):
        response = self.client.post("/api/hit")
        self.assertEqual(400, response.status_code)

        data = response.get_json()
        self.assertEqual("error", data["status"])
        self.assertIn("No active round", data["message"])

    def test_deal_hit_and_stand_cycle(self):
        self.client.post("/api/new-game", json={"tutorial": True})

        deck = scripted_deck(
            Card("Spades", "10"), Card("Hearts", "7"),
            Card("Diamonds", "8"), Card("Clubs", "9"),
            Card("Spades", "2"), Card("Hearts", "10"),
        )
        with patch("backend.app.Deck", deck):
            deal_response = self.client.post("/api/deal", json={"bet": 50})
            self.assertEqual(200, deal_response.status_code)
            deal_data = deal_response.get_json()

            self.assertEqual("success", deal_data["status"])
            self.assertEqual(950, deal_data["chips"])
            self.assertIn("player_hand", deal_data)
            self.assertIn("dealer_hand", deal_data)

            hit_response = self.client.post("/api/hit")
            self.assertEqual(200, hit_response.status_code)
            hit_data = hit_response.get_json()
            self.assertEqual("success", hit_data["status"])
            self.assertEqual(3, len(hit_data["player_hand"]["cards"]))
            self.assertIsInstance(hit_data["bust"], bool)

            stand_response = self.client.post("/api/stand")
            self.assertEqual(200, stand_response.status_code)
            stand_data = stand_response.get_json()

            self.assertEqual("success", stand_data["status"])
            self.assertIn(stand_data["outcome"], ["win", "lose", "push", "blackjack"])
            self.assertIsInstance(stand_data["chips"], int)

    def test_player_natural_blackjack_resolves_immediately(self):
        self.client.post("/api/new-game", json={"tutorial": True})
        deck = scripted_deck(
            Card("Spades", "Ace"), Card("Hearts", "9"),
            Card("Diamonds", "King"), Card("Clubs", "7"),
        )

        with patch("backend.app.Deck", deck):
            response = self.client.post("/api/deal", json={"bet": 50})

        data = response.get_json()
        self.assertEqual(200, response.status_code)
        self.assertEqual("blackjack", data["outcome"])
        self.assertEqual("Blackjack! You win 3:2!", data["message"])
        self.assertEqual(1075, data["chips"])

    def test_dealer_natural_blackjack_resolves_immediately(self):
        self.client.post("/api/new-game", json={"tutorial": True})
        deck = scripted_deck(
            Card("Spades", "9"), Card("Hearts", "Ace"),
            Card("Diamonds", "7"), Card("Clubs", "King"),
        )

        with patch("backend.app.Deck", deck):
            response = self.client.post("/api/deal", json={"bet": 50})

        data = response.get_json()
        self.assertEqual(200, response.status_code)
        self.assertEqual("lose", data["outcome"])
        self.assertEqual(950, data["chips"])

    def test_split_creates_two_hands_and_deducts_second_bet(self):
        self.client.post("/api/new-game", json={"tutorial": True})
        deck = scripted_deck(
            Card("Spades", "8"), Card("Hearts", "6"),
            Card("Diamonds", "8"), Card("Clubs", "10"),
            Card("Spades", "3"), Card("Hearts", "4"),
        )

        with patch("backend.app.Deck", deck):
            self.client.post("/api/deal", json={"bet": 50})
            response = self.client.post("/api/split")

        data = response.get_json()
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, data["hand_count"])
        self.assertEqual(900, data["chips"])
        self.assertEqual(2, len(data["player_hand"]["cards"]))

    def test_double_down_route(self):
        self.client.post("/api/new-game", json={"tutorial": True})
        deck = scripted_deck(
            Card("Spades", "9"), Card("Hearts", "7"),
            Card("Diamonds", "2"), Card("Clubs", "9"),
            Card("Spades", "10"), Card("Hearts", "10"),
        )
        with patch("backend.app.Deck", deck):
            self.client.post("/api/deal", json={"bet": 100})
            response = self.client.post("/api/double")

            self.assertEqual(200, response.status_code)
            data = response.get_json()
            self.assertEqual("success", data["status"])
            self.assertIn(data["outcome"], ["win", "lose", "push", "blackjack"])
            self.assertIsInstance(data["chips"], int)
            self.assertGreaterEqual(len(data["player_hand"]["cards"]), 3)
            self.assertGreaterEqual(len(data["dealer_hand"]["cards"]), 2)

    def test_roulette_rejects_invalid_bet_value(self):
        self.client.post("/api/new-game", json={"tutorial": True})
        response = self.client.post("/api/roulette/spin", json={
            "bet_type": "color", "bet_value": "green", "amount": 25,
        })

        self.assertEqual(400, response.status_code)
        self.assertEqual("error", response.get_json()["status"])

    def test_roulette_win_returns_correct_payout(self):
        self.client.post("/api/new-game", json={"tutorial": True})
        with patch("backend.app._wheel.spin", return_value=7):
            response = self.client.post("/api/roulette/spin", json={
                "bet_type": "color", "bet_value": "red", "amount": 25,
            })

        data = response.get_json()
        self.assertEqual(200, response.status_code)
        self.assertTrue(data["won"])
        self.assertEqual(25, data["payout"])
        self.assertEqual(1025, data["chips"])

    def test_slots_three_sevens_payout(self):
        self.client.post("/api/new-game", json={"tutorial": True})
        with patch("backend.app._slot_machine.spin", return_value=["seven"] * 3):
            response = self.client.post("/api/slots/spin", json={"amount": 25})

        data = response.get_json()
        self.assertEqual(200, response.status_code)
        self.assertEqual("three_match", data["result"])
        self.assertEqual(625, data["payout"])
        self.assertEqual(1625, data["chips"])
        self.assertEqual("hot_hand", data["advice_evaluation"]["teaching_moment"])

    def test_slots_advice_returns_machine_odds(self):
        self.client.post("/api/new-game", json={"tutorial": True})
        response = self.client.post("/api/slots/advice", json={"amount": 25})

        data = response.get_json()
        self.assertEqual(200, response.status_code)
        self.assertEqual("success", data["status"])
        self.assertEqual(83.84, data["advice"]["rtp_percent"])
        self.assertIn("explanation", data["advice"])

    def test_slots_rejects_bet_larger_than_available_chips(self):
        self.client.post("/api/new-game", json={"tutorial": True})
        with self.client.session_transaction() as session:
            session["chips"] = 10

        response = self.client.post("/api/slots/spin", json={"amount": 25})
        self.assertEqual(400, response.status_code)
        self.assertEqual("error", response.get_json()["status"])

    def test_repeated_saves_do_not_double_count_a_bankruptcy(self):
        self.client.post("/api/new-game", json={"tutorial": True})
        with self.client.session_transaction() as session:
            session["tutorial"] = False
            session["chips"] = 0
            session["bankrupts"] = 0

        self.client.post("/api/save")
        self.client.post("/api/save")

        with self.client.session_transaction() as session:
            self.assertEqual(1, session["bankrupts"])


if __name__ == "__main__":
    unittest.main()
