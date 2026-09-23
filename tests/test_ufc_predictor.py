import unittest

import numpy as np
import pandas as pd

from ufc_predictor import FighterState, build_prefight_dataset, canonicalize_fights, predict_matchup


class PredictorTests(unittest.TestCase):
    def test_corner_identity_is_reconstructed_from_winner_and_loser(self):
        raw = pd.DataFrame([
            {
                "winner_name": "Alice",
                "loser_name": "Beth",
                "winner": "blue",
                "event_date": "01/01/2020",
                "event_name": "One",
                "bout_type": "Women's Bout",
                "time_format": "3 Rnd (5-5-5)",
                "method": "Decision",
            }
        ])
        fight = canonicalize_fights(raw).iloc[0]
        self.assertEqual(fight.red_fighter, "Beth")
        self.assertEqual(fight.blue_fighter, "Alice")
        self.assertEqual(fight.red_win, 0)

    def test_features_are_emitted_before_current_fight_updates_state(self):
        raw = pd.DataFrame([
            {
                "winner_name": "Alice",
                "loser_name": "Beth",
                "winner": "red",
                "event_date": "01/01/2020",
                "event_name": "One",
                "bout_type": "Bout",
                "time_format": "3 Rnd (5-5-5)",
                "method": "Decision",
            },
            {
                "winner_name": "Alice",
                "loser_name": "Beth",
                "winner": "red",
                "event_date": "01/02/2020",
                "event_name": "Two",
                "bout_type": "Bout",
                "time_format": "3 Rnd (5-5-5)",
                "method": "Decision",
            },
        ])
        dataset, _ = build_prefight_dataset(canonicalize_fights(raw), profiles={})
        self.assertEqual(dataset.iloc[0].elo_diff, 0)
        self.assertEqual(dataset.iloc[0].red_debut, 1)
        self.assertEqual(dataset.iloc[0].blue_debut, 1)
        self.assertGreater(dataset.iloc[1].elo_diff, 0)
        self.assertEqual(dataset.iloc[1].red_debut, 0)
        self.assertEqual(dataset.iloc[1].blue_debut, 0)

    def test_swapping_fighters_returns_complementary_probability(self):
        class CornerBiasedModel:
            def predict_proba(self, rows):
                probability = np.clip(
                    0.60 + rows["elo_diff"].to_numpy() / 2000 + rows["red_experience"].to_numpy() / 100,
                    0.01,
                    0.99,
                )
                return np.column_stack((1 - probability, probability))

        states = {
            "alice": FighterState(elo=1600, fights=10, wins=7),
            "beth": FighterState(elo=1450, fights=4, wins=2),
        }
        profiles = {
            "alice": {"height": 68, "reach": 70, "dob": pd.Timestamp("1990-01-01")},
            "beth": {"height": 66, "reach": 67, "dob": pd.Timestamp("1992-01-01")},
        }
        options = {"date": pd.Timestamp("2026-01-01")}

        alice_first = predict_matchup(CornerBiasedModel(), states, profiles, "alice", "beth", **options)
        beth_first = predict_matchup(CornerBiasedModel(), states, profiles, "beth", "alice", **options)

        self.assertAlmostEqual(alice_first + beth_first, 1.0, places=12)


if __name__ == "__main__":
    unittest.main()
