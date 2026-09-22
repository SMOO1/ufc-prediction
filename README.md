# UFC Prediction

A leakage-safe UFC winner predictor built from the included historical fight results.

The model reconstructs the red and blue corners for every bout and calculates Elo,
experience, recent form, streak, layoff, opponent-strength, finishing, age, height,
and reach features using only information available before that fight. It never uses
statistics from the fight being predicted or final career averages in historical rows.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Evaluate the model

```bash
python regression.py
```

Evaluation uses a chronological split on complete event dates. The most recent 20%
of event dates are held out; no random train/test split is used. Model fitting uses
the eight years preceding the split because corner assignment and the UFC roster have
changed substantially since the earliest events.

## Predict a matchup with automatic UFCStats lookup

Enter only two exact full names using underscores. The app resolves both names on
UFCStats, downloads the profile fields shown on the fighter pages, displays them,
and makes the prediction. The first input is red and the second input is blue:

```bash
python regression.py israel_adesanya joe_pyfer --date 2026-10-01
```

Names are case-insensitive. Punctuation is optional, so both `sean_omalley` and
`"sean_o'malley"` resolve to Sean O'Malley. If either exact full name is absent
from UFCStats, the prediction stops and asks for a different name.

Bout context can also be supplied:

```bash
python regression.py \
  red_firstname_red_lastname blue_firstname_blue_lastname \
  --date 2026-10-01 --rounds 5 --title
```

For development without a network request, pass `--offline`; this uses the bundled
fighter details and still rejects names that are unknown to the local dataset.

To persist the fitted pipeline and fighter state:

```bash
python regression.py --model-out artifacts/ufc_model.joblib
```

## Important data rule

For a bout on date `D`, its features are calculated from bouts strictly before `D`.
Only after the feature row is recorded are Elo and fighter histories updated with the
result. Static height, reach, and date of birth come from `raw_fighter_details.csv`;
the aggregate striking and grappling columns are intentionally not used because they
represent final/current career summaries rather than dated snapshots.
