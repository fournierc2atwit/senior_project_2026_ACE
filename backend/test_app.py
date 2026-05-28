import unittest

from backend.app import app


class BackendApiTestCase(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_new_game_returns_initial_chips(self):
        response = self.client.post("/api/new-game")
        self.assertEqual(200, response.status_code)

        data = response.get_json()
        self.assertEqual("success", data["status"])
        self.assertEqual(1000, data["chips"])

    def test_deal_invalid_bet_returns_400(self):
        self.client.post("/api/new-game")
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
        self.client.post("/api/new-game")

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

    def test_double_down_route(self):
        self.client.post("/api/new-game")
        self.client.post("/api/deal", json={"bet": 100})

        response = self.client.post("/api/double")
        self.assertEqual(200, response.status_code)

        data = response.get_json()
        self.assertEqual("success", data["status"])
        self.assertIn(data["outcome"], ["win", "lose", "push", "blackjack"])
        self.assertIsInstance(data["chips"], int)
        self.assertGreaterEqual(len(data["player_hand"]["cards"]), 3)
        self.assertGreaterEqual(len(data["dealer_hand"]["cards"]), 2)


if __name__ == "__main__":
    unittest.main()
