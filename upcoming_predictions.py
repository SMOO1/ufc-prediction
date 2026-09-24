"""Emit model predictions for the next event currently listed by UFCStats."""

from __future__ import annotations

import json
import sys

import pandas as pd

from ufc_predictor import (
    DEFAULT_FIGHTERS,
    DEFAULT_FIGHTS,
    build_prefight_dataset,
    canonicalize_fights,
    load_profiles,
    normalize_name,
    predict_matchup,
    train_and_evaluate,
)
from ufcstats_client import UFCStatsClient, UFCStatsError


def build_upcoming_predictions() -> dict:
    client = UFCStatsClient()
    event = client.get_upcoming_event()
    profiles = load_profiles(DEFAULT_FIGHTERS)

    # The bundled historical data supplies almost every active fighter. Only fetch
    # individual live profiles for new UFC entrants missing from that dataset.
    for bout in event.bouts:
        for name, url in (
            (bout.fighter1, bout.fighter1_url),
            (bout.fighter2, bout.fighter2_url),
        ):
            if normalize_name(name) not in profiles:
                profile = client.get_fighter_by_url(name, url)
                profiles[normalize_name(name)] = profile.model_values()

    fights = canonicalize_fights(pd.read_csv(DEFAULT_FIGHTS, sep=";"))
    dataset, states = build_prefight_dataset(fights, profiles)
    model, _, _ = train_and_evaluate(dataset)
    fight_date = pd.Timestamp(event.date)

    bouts = []
    for index, bout in enumerate(event.bouts):
        title_bout = "title" in bout.weight_class.casefold()
        probability1 = predict_matchup(
            model,
            states,
            profiles,
            bout.fighter1,
            bout.fighter2,
            date=fight_date,
            title_bout=title_bout,
            womens_bout="women" in bout.weight_class.casefold(),
            scheduled_rounds=5 if index == 0 or title_bout else 3,
        )
        bouts.append({
            "fighter1": bout.fighter1,
            "fighter2": bout.fighter2,
            "fighter1Probability": probability1,
            "fighter2Probability": 1.0 - probability1,
            "predictedWinner": bout.fighter1 if probability1 >= 0.5 else bout.fighter2,
            "weightClass": bout.weight_class,
        })

    return {
        "event": {
            "name": event.name,
            "date": event.date.date().isoformat(),
            "location": event.location,
            "url": event.url,
        },
        "bouts": bouts,
        "source": "UFCStats",
    }


def main() -> None:
    try:
        print(json.dumps(build_upcoming_predictions(), separators=(",", ":")))
    except (UFCStatsError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
