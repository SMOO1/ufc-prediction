"""Leakage-safe UFC fight winner model.

The original project trained on winner-minus-loser career aggregates while the
target described the winner's corner. This module instead reconstructs the red
and blue corners and creates dynamic features using only earlier fights.
"""

from __future__ import annotations

import argparse
import difflib
import json
import math
import re
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ufcstats_client import FighterProfile, UFCStatsClient, UFCStatsError, normalize_fighter_name


ROOT = Path(__file__).resolve().parent
DEFAULT_FIGHTS = ROOT / "stats_processed.csv"
DEFAULT_FIGHTERS = ROOT / "raw_fighter_details.csv"

FEATURES = [
    "elo_diff",
    "experience_diff",
    "red_experience",
    "blue_experience",
    "win_rate_diff",
    "recent_win_rate_diff",
    "streak_diff",
    "layoff_diff",
    "opponent_elo_diff",
    "finish_win_rate_diff",
    "stopped_loss_rate_diff",
    "height_diff",
    "reach_diff",
    "age_diff",
    "red_debut",
    "blue_debut",
    "title_bout",
    "womens_bout",
    "scheduled_rounds",
]
TRAINING_YEARS = 8


def normalize_name(value: Any) -> str:
    """Create a stable join key for names from the two source files."""
    return normalize_fighter_name(value)


def parse_height(value: Any) -> float:
    match = re.search(r"(\d+)\s*'\s*(\d+)", str(value))
    return float(int(match.group(1)) * 12 + int(match.group(2))) if match else np.nan


def parse_reach(value: Any) -> float:
    match = re.search(r"\d+(?:\.\d+)?", str(value))
    return float(match.group()) if match else np.nan


def load_profiles(path: Path = DEFAULT_FIGHTERS) -> dict[str, dict[str, Any]]:
    raw = pd.read_csv(path)
    raw["key"] = raw["fighter_name"].map(normalize_name)
    raw["height"] = raw["Height"].map(parse_height)
    raw["reach"] = raw["Reach"].map(parse_reach)
    raw["dob"] = pd.to_datetime(raw["DOB"], errors="coerce")
    return raw.set_index("key")[["fighter_name", "height", "reach", "dob"]].to_dict("index")


def canonicalize_fights(raw: pd.DataFrame) -> pd.DataFrame:
    """Recover red/blue identities without looking at same-fight statistics."""
    fights = raw.copy()
    fights["event_date"] = pd.to_datetime(fights["event_date"], dayfirst=True, errors="raise")
    winner_is_red = fights["winner"].str.casefold().eq("red")
    fights["red_fighter"] = np.where(winner_is_red, fights["winner_name"], fights["loser_name"])
    fights["blue_fighter"] = np.where(winner_is_red, fights["loser_name"], fights["winner_name"])
    fights["red_key"] = fights["red_fighter"].map(normalize_name)
    fights["blue_key"] = fights["blue_fighter"].map(normalize_name)
    fights["red_win"] = winner_is_red.astype(int)
    return fights.sort_values(["event_date", "event_name", "red_key", "blue_key"]).reset_index(drop=True)


@dataclass
class FighterState:
    elo: float = 1500.0
    fights: int = 0
    wins: int = 0
    finish_wins: int = 0
    stopped_losses: int = 0
    streak: int = 0
    opponent_elo_sum: float = 0.0
    last_date: pd.Timestamp | None = None
    recent: deque[int] = field(default_factory=lambda: deque(maxlen=5))

    @property
    def win_rate(self) -> float:
        return (self.wins + 1.0) / (self.fights + 2.0)

    @property
    def recent_win_rate(self) -> float:
        return (sum(self.recent) + 1.0) / (len(self.recent) + 2.0)

    @property
    def opponent_elo(self) -> float:
        return self.opponent_elo_sum / self.fights if self.fights else 1500.0

    @property
    def finish_win_rate(self) -> float:
        return (self.finish_wins + 1.0) / (self.fights + 2.0)

    @property
    def stopped_loss_rate(self) -> float:
        return (self.stopped_losses + 1.0) / (self.fights + 2.0)


def _profile_value(profiles: dict[str, dict[str, Any]], key: str, field_name: str) -> float:
    profile = profiles.get(key)
    if not profile:
        return np.nan
    value = profile.get(field_name, np.nan)
    return float(value) if pd.notna(value) else np.nan


def _age_on(profiles: dict[str, dict[str, Any]], key: str, date: pd.Timestamp) -> float:
    profile = profiles.get(key)
    if not profile or pd.isna(profile.get("dob")):
        return np.nan
    return (date - profile["dob"]).days / 365.2425


def _layoff(state: FighterState, date: pd.Timestamp) -> float:
    if state.last_date is None:
        return np.nan
    return float(min(max((date - state.last_date).days, 0), 1825))


def _scheduled_rounds(time_format: Any) -> float:
    match = re.search(r"(\d+)\s*Rnd", str(time_format), flags=re.IGNORECASE)
    return float(match.group(1)) if match else np.nan


def matchup_features(
    red_key: str,
    blue_key: str,
    date: pd.Timestamp,
    red: FighterState,
    blue: FighterState,
    profiles: dict[str, dict[str, Any]],
    *,
    title_bout: bool = False,
    womens_bout: bool = False,
    scheduled_rounds: float = 3.0,
) -> dict[str, float]:
    red_layoff, blue_layoff = _layoff(red, date), _layoff(blue, date)
    layoff_diff = red_layoff - blue_layoff if pd.notna(red_layoff) and pd.notna(blue_layoff) else np.nan
    return {
        "elo_diff": red.elo - blue.elo,
        "experience_diff": math.log1p(red.fights) - math.log1p(blue.fights),
        "red_experience": math.log1p(red.fights),
        "blue_experience": math.log1p(blue.fights),
        "win_rate_diff": red.win_rate - blue.win_rate,
        "recent_win_rate_diff": red.recent_win_rate - blue.recent_win_rate,
        "streak_diff": red.streak - blue.streak,
        "layoff_diff": layoff_diff,
        "opponent_elo_diff": red.opponent_elo - blue.opponent_elo,
        "finish_win_rate_diff": red.finish_win_rate - blue.finish_win_rate,
        "stopped_loss_rate_diff": red.stopped_loss_rate - blue.stopped_loss_rate,
        "height_diff": _profile_value(profiles, red_key, "height") - _profile_value(profiles, blue_key, "height"),
        "reach_diff": _profile_value(profiles, red_key, "reach") - _profile_value(profiles, blue_key, "reach"),
        "age_diff": _age_on(profiles, red_key, date) - _age_on(profiles, blue_key, date),
        "red_debut": float(red.fights == 0),
        "blue_debut": float(blue.fights == 0),
        "title_bout": float(title_bout),
        "womens_bout": float(womens_bout),
        "scheduled_rounds": float(scheduled_rounds),
    }


def _is_finish(method: Any) -> bool:
    text = str(method).casefold()
    return "ko" in text or "submission" in text


def _new_streak(current: int, won: int) -> int:
    if won:
        return current + 1 if current > 0 else 1
    return current - 1 if current < 0 else -1


def update_states(
    red: FighterState,
    blue: FighterState,
    *,
    red_win: int,
    date: pd.Timestamp,
    method: Any,
    k_factor: float = 32.0,
) -> None:
    """Update both fighters only after their feature row has been emitted."""
    expected_red = 1.0 / (1.0 + 10.0 ** ((blue.elo - red.elo) / 400.0))
    red_elo_before, blue_elo_before = red.elo, blue.elo
    red.elo += k_factor * (red_win - expected_red)
    blue.elo += k_factor * ((1 - red_win) - (1 - expected_red))
    red.opponent_elo_sum += blue_elo_before
    blue.opponent_elo_sum += red_elo_before

    red.fights += 1
    blue.fights += 1
    red.wins += red_win
    blue_win = 1 - red_win
    blue.wins += blue_win
    red.recent.append(red_win)
    blue.recent.append(blue_win)
    red.streak = _new_streak(red.streak, red_win)
    blue.streak = _new_streak(blue.streak, blue_win)

    if _is_finish(method):
        winner, loser = (red, blue) if red_win else (blue, red)
        winner.finish_wins += 1
        loser.stopped_losses += 1
    red.last_date = date
    blue.last_date = date


def build_prefight_dataset(
    fights: pd.DataFrame,
    profiles: dict[str, dict[str, Any]],
) -> tuple[pd.DataFrame, dict[str, FighterState]]:
    states: dict[str, FighterState] = {}
    rows: list[dict[str, Any]] = []
    for fight in fights.to_dict("records"):
        red = states.setdefault(fight["red_key"], FighterState())
        blue = states.setdefault(fight["blue_key"], FighterState())
        bout_type = str(fight.get("bout_type", ""))
        values = matchup_features(
            fight["red_key"],
            fight["blue_key"],
            fight["event_date"],
            red,
            blue,
            profiles,
            title_bout="title" in bout_type.casefold(),
            womens_bout="women" in bout_type.casefold(),
            scheduled_rounds=_scheduled_rounds(fight.get("time_format")),
        )
        rows.append({
            **values,
            "event_date": fight["event_date"],
            "event_name": fight.get("event_name", ""),
            "red_fighter": fight["red_fighter"],
            "blue_fighter": fight["blue_fighter"],
            "red_win": fight["red_win"],
        })
        update_states(red, blue, red_win=fight["red_win"], date=fight["event_date"], method=fight.get("method"))
    return pd.DataFrame(rows), states


def make_model() -> Pipeline:
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression(max_iter=5000, C=0.5, random_state=42)),
    ])


def chronological_split(dataset: pd.DataFrame, train_fraction: float = 0.8) -> tuple[np.ndarray, np.ndarray, pd.Timestamp]:
    dates = np.array(sorted(dataset["event_date"].unique()))
    if len(dates) < 2:
        raise ValueError("At least two event dates are required")
    cutoff = pd.Timestamp(dates[min(max(int(len(dates) * train_fraction), 1), len(dates) - 1)])
    train = np.flatnonzero(dataset["event_date"].to_numpy() < cutoff)
    test = np.flatnonzero(dataset["event_date"].to_numpy() >= cutoff)
    return train, test, cutoff


def evaluate(model: Pipeline, dataset: pd.DataFrame, test_rows: np.ndarray) -> dict[str, float]:
    y = dataset.iloc[test_rows]["red_win"].astype(int)
    probability = model.predict_proba(dataset.iloc[test_rows][FEATURES])[:, 1]
    return {
        "accuracy": accuracy_score(y, probability >= 0.5),
        "roc_auc": roc_auc_score(y, probability),
        "log_loss": log_loss(y, probability),
        "brier_score": brier_score_loss(y, probability),
        "red_baseline_accuracy": float(y.mean()),
        "n_test": float(len(y)),
    }


def _recent_rows(dataset: pd.DataFrame, rows: np.ndarray, end: pd.Timestamp) -> np.ndarray:
    """Limit fitting to the modern era so obsolete corner priors do not dominate."""
    start = end - pd.DateOffset(years=TRAINING_YEARS)
    return np.array([row for row in rows if dataset.iloc[row]["event_date"] >= start], dtype=int)


def train_and_evaluate(dataset: pd.DataFrame) -> tuple[Pipeline, dict[str, float], pd.Timestamp]:
    train_rows, test_rows, cutoff = chronological_split(dataset)
    train_rows = _recent_rows(dataset, train_rows, cutoff)
    evaluation_model = make_model()
    evaluation_model.fit(dataset.iloc[train_rows][FEATURES], dataset.iloc[train_rows]["red_win"])
    metrics = evaluate(evaluation_model, dataset, test_rows)
    metrics["n_train"] = float(len(train_rows))
    final_model = make_model()
    all_rows = np.arange(len(dataset))
    final_rows = _recent_rows(dataset, all_rows, dataset["event_date"].max() + pd.Timedelta(days=1))
    final_model.fit(dataset.iloc[final_rows][FEATURES], dataset.iloc[final_rows]["red_win"])
    return final_model, metrics, cutoff


def predict_matchup(
    model: Pipeline,
    states: dict[str, FighterState],
    profiles: dict[str, dict[str, Any]],
    red_name: str,
    blue_name: str,
    *,
    date: pd.Timestamp,
    title_bout: bool = False,
    womens_bout: bool = False,
    scheduled_rounds: int = 3,
) -> float:
    red_key, blue_key = normalize_name(red_name), normalize_name(blue_name)
    known = set(states) | set(profiles)
    for supplied, key in ((red_name, red_key), (blue_name, blue_key)):
        if key not in known:
            suggestions = difflib.get_close_matches(key, sorted(known), n=3, cutoff=0.65)
            hint = f" Did you mean: {', '.join(suggestions)}?" if suggestions else ""
            raise ValueError(f"Unknown fighter: {supplied}.{hint}")
    red = states.get(red_key, FighterState())
    blue = states.get(blue_key, FighterState())
    row = matchup_features(
        red_key,
        blue_key,
        date,
        red,
        blue,
        profiles,
        title_bout=title_bout,
        womens_bout=womens_bout,
        scheduled_rounds=float(scheduled_rounds),
    )
    return float(model.predict_proba(pd.DataFrame([row], columns=FEATURES))[0, 1])


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train and evaluate a leakage-safe UFC predictor")
    parser.add_argument("fighter1", nargs="?", help="Red fighter as firstname_lastname")
    parser.add_argument("fighter2", nargs="?", help="Blue fighter as firstname_lastname")
    parser.add_argument("--fights", type=Path, default=DEFAULT_FIGHTS)
    parser.add_argument("--fighters", type=Path, default=DEFAULT_FIGHTERS)
    parser.add_argument("--predict", nargs=2, metavar=("RED_FIGHTER", "BLUE_FIGHTER"))
    parser.add_argument("--date", type=pd.Timestamp, default=pd.Timestamp.today().normalize())
    parser.add_argument("--rounds", type=int, choices=(3, 5), default=3)
    parser.add_argument("--title", action="store_true")
    parser.add_argument("--women", action="store_true")
    parser.add_argument("--offline", action="store_true", help="Use bundled fighter details instead of UFCStats")
    parser.add_argument("--json", action="store_true", help="Emit one machine-readable JSON response")
    parser.add_argument("--model-out", type=Path)
    return parser


def main() -> None:
    parser = _parser()
    args = parser.parse_args()
    positional_pair = (args.fighter1, args.fighter2) if args.fighter1 or args.fighter2 else None
    if positional_pair and not all(positional_pair):
        parser.error("provide both fighter inputs as firstname1_lastname1 firstname2_lastname2")
    if positional_pair and args.predict:
        parser.error("use either positional fighter inputs or --predict, not both")
    pair = tuple(args.predict) if args.predict else positional_pair
    if args.json and not pair:
        parser.error("--json requires two fighter inputs")

    profiles = load_profiles(args.fighters)
    live_profiles: list[FighterProfile] = []
    if pair and not args.offline:
        client = UFCStatsClient()
        try:
            live_profiles = [client.get_fighter(name) for name in pair]
        except UFCStatsError as exc:
            parser.error(str(exc))
        for profile in live_profiles:
            profiles[normalize_name(profile.name)] = profile.model_values()
        pair = (live_profiles[0].name, live_profiles[1].name)

    fights = canonicalize_fights(pd.read_csv(args.fights, sep=";"))
    dataset, states = build_prefight_dataset(fights, profiles)
    model, metrics, cutoff = train_and_evaluate(dataset)

    if args.model_out:
        args.model_out.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"model": model, "states": states, "profiles": profiles, "features": FEATURES}, args.model_out)
        if not args.json:
            print(f"Saved model: {args.model_out}")

    probability = None
    if pair:
        red_name, blue_name = pair
        probability = predict_matchup(
            model,
            states,
            profiles,
            red_name,
            blue_name,
            date=args.date,
            title_bout=args.title,
            womens_bout=args.women,
            scheduled_rounds=args.rounds,
        )

    if args.json:
        payload = {
            "prediction": {
                "redName": pair[0],
                "blueName": pair[1],
                "redProbability": probability,
                "blueProbability": 1.0 - probability,
                "date": args.date.date().isoformat(),
                "rounds": args.rounds,
                "titleBout": args.title,
                "womensBout": args.women,
            },
            "fighters": [profile.api_values() for profile in live_profiles],
            "metrics": {
                **metrics,
                "holdoutStart": cutoff.date().isoformat(),
                "holdoutEnd": dataset.event_date.max().date().isoformat(),
            },
        }
        print(json.dumps(payload, separators=(",", ":")))
        return

    print(f"Chronological holdout: {cutoff.date()} through {dataset.event_date.max().date()}")
    for name, value in metrics.items():
        print(f"{name}: {int(value) if name in {'n_train', 'n_test'} else f'{value:.4f}'}")

    if pair:
        if live_profiles:
            print()
            print(live_profiles[0].summary())
            print()
            print(live_profiles[1].summary())
            print()
        print(f"{red_name} (red): {probability:.1%}")
        print(f"{blue_name} (blue): {1.0 - probability:.1%}")


if __name__ == "__main__":
    main()
