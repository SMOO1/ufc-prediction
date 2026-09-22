import unittest

import pandas as pd

from ufc_predictor import build_prefight_dataset, canonicalize_fights


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


if __name__ == "__main__":
    unittest.main()
