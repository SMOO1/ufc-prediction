# FightScope — UFC Prediction Website

A full-stack UFC winner prediction website with a Spring Boot backend, responsive
browser interface, live UFCStats profiles, and a leakage-safe Python model.

The model reconstructs the red and blue corners for every bout and calculates Elo,
experience, recent form, streak, layoff, opponent-strength, finishing, age, height,
and reach features using only information available before that fight. It never uses
statistics from the fight being predicted or final career averages in historical rows.

## Requirements

- Java 21+
- Python 3.11+

Maven does not need to be installed; the repository includes Maven Wrapper.

## Setup and run the website

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./mvnw spring-boot:run
```

Open [http://localhost:8080](http://localhost:8080). Spring Boot serves the site
and the `/api/predictions` endpoint. Each request validates its inputs, runs the
Python prediction engine without a shell, enforces a timeout, and returns JSON.

If needed, configure a different Python executable or project directory:

```bash
PYTHON_EXECUTABLE=/path/to/python UFC_PROJECT_ROOT=/path/to/repo ./mvnw spring-boot:run
```

Health checks are available at `http://localhost:8080/actuator/health`.

## Cloud deployment

The repository includes a production `Dockerfile` and a Render Blueprint. The
container packages Java 21, the Spring Boot application, Python, its model
dependencies, and the two datasets required at prediction time.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/SMOO1/ufc-prediction)

Render uses the platform-provided `PORT`, checks `/actuator/health`, and can
redeploy automatically after changes land on the connected branch. Free web
services can sleep during inactivity, so their first request after a pause can
take longer.

## Architecture

```text
Browser UI → Spring Boot REST API → Python prediction engine → UFCStats
```

- `src/main/java`: API validation, process management, timeouts, and error responses
- `src/main/resources/static`: responsive HTML, CSS, and JavaScript frontend
- `ufc_predictor.py`: chronological feature generation and trained model
- `ufcstats_client.py`: exact-name profile lookup and parsing

## Evaluate or use the model from the terminal

```bash
python regression.py
```

Evaluation uses a chronological split on complete event dates. The most recent 20%
of event dates are held out; no random train/test split is used. Model fitting uses
the eight years preceding the split because corner assignment and the UFC roster have
changed substantially since the earliest events.

## Predict a matchup with automatic UFCStats lookup

On the website, enter the two full names normally with spaces; underscores are not
required. The app resolves both names on UFCStats, downloads the profile fields,
displays them, and makes the prediction. From the terminal, quote names containing
spaces:

```bash
python regression.py "Israel Adesanya" "Joe Pyfer" --date 2026-10-01
```

Names are case-insensitive. Punctuation is optional, so both `"Sean O'Malley"` and
`"Sean OMalley"` resolve to Sean O'Malley. If either exact full name is absent
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
