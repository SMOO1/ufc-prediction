"""Small, rate-conscious client for public fighter profiles on UFCStats."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL = "http://ufcstats.com"
USER_AGENT = "ufc-prediction/1.0 (personal research project)"


class UFCStatsError(RuntimeError):
    """Raised when UFCStats cannot be queried or parsed."""


class FighterNotFound(UFCStatsError):
    """Raised when an exact full-name match does not exist on UFCStats."""


def normalize_fighter_name(value: Any) -> str:
    """Normalize spaces, underscores, punctuation, and case for exact matching."""
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode()
    text = text.replace("_", " ").casefold()
    text = re.sub(r"[^a-z0-9\s]+", "", text)
    return " ".join(text.split())


def display_input_name(value: Any) -> str:
    return " ".join(str(value).replace("_", " ").split())


def _number(value: str) -> float | None:
    match = re.search(r"-?\d+(?:\.\d+)?", value)
    return float(match.group()) if match else None


def _percent(value: str) -> float | None:
    number = _number(value)
    return number / 100.0 if number is not None else None


def _height_inches(value: str) -> float | None:
    match = re.search(r"(\d+)\s*'\s*(\d+)", value)
    return float(int(match.group(1)) * 12 + int(match.group(2))) if match else None


@dataclass(frozen=True)
class FighterProfile:
    name: str
    nickname: str
    url: str
    record: str
    height_inches: float | None
    weight_lbs: float | None
    reach_inches: float | None
    stance: str | None
    dob: datetime | None
    slpm: float | None
    str_acc: float | None
    sapm: float | None
    str_def: float | None
    td_avg: float | None
    td_acc: float | None
    td_def: float | None
    sub_avg: float | None

    def model_values(self) -> dict[str, Any]:
        """Return the static fields used by the leakage-safe prediction model."""
        return {
            "fighter_name": self.name,
            "height": self.height_inches,
            "reach": self.reach_inches,
            "dob": self.dob,
        }

    def api_values(self) -> dict[str, Any]:
        """Return JSON-safe profile data for the Spring Boot web API."""
        return {
            "name": self.name,
            "nickname": self.nickname,
            "record": self.record,
            "url": self.url,
            "heightInches": self.height_inches,
            "weightLbs": self.weight_lbs,
            "reachInches": self.reach_inches,
            "stance": self.stance,
            "dob": self.dob.date().isoformat() if self.dob else None,
            "slpm": self.slpm,
            "strikingAccuracy": self.str_acc,
            "sapm": self.sapm,
            "strikingDefense": self.str_def,
            "takedownAverage": self.td_avg,
            "takedownAccuracy": self.td_acc,
            "takedownDefense": self.td_def,
            "submissionAverage": self.sub_avg,
        }

    def summary(self) -> str:
        def show(value: Any, suffix: str = "") -> str:
            return "N/A" if value is None else f"{value:g}{suffix}"

        dob = self.dob.strftime("%b %d, %Y") if self.dob else "N/A"
        percentages = {
            "Str. Acc.": self.str_acc,
            "Str. Def.": self.str_def,
            "TD Acc.": self.td_acc,
            "TD Def.": self.td_def,
        }
        lines = [
            f"UFCStats: {self.name}" + (f' \"{self.nickname}\"' if self.nickname else ""),
            f"  Record: {self.record or 'N/A'}",
            f"  Height: {show(self.height_inches, ' in')} | Weight: {show(self.weight_lbs, ' lbs')} | Reach: {show(self.reach_inches, ' in')}",
            f"  Stance: {self.stance or 'N/A'} | DOB: {dob}",
            f"  SLpM: {show(self.slpm)} | SApM: {show(self.sapm)} | TD Avg.: {show(self.td_avg)} | Sub. Avg.: {show(self.sub_avg)}",
            "  " + " | ".join(
                f"{label}: {'N/A' if value is None else f'{value:.0%}'}" for label, value in percentages.items()
            ),
        ]
        return "\n".join(lines)


class UFCStatsClient:
    """Resolve exact fighter names and retrieve their current UFCStats profile."""

    def __init__(self, *, timeout: float = 20.0, session: requests.Session | None = None):
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT
        self._directory_cache: dict[str, list[dict[str, str]]] = {}
        self._profile_cache: dict[str, FighterProfile] = {}

    @staticmethod
    def _solve_browser_check(html: str) -> tuple[str, int]:
        nonce_match = re.search(r'nonce\s*=\s*"([^"]+)"', html)
        zeros_match = re.search(r"new Array\((\d+)\s*\+\s*1\)", html)
        if not nonce_match or not zeros_match:
            raise UFCStatsError("UFCStats returned an unsupported browser check")
        nonce = nonce_match.group(1)
        target = "0" * int(zeros_match.group(1))
        solution = 0
        while not hashlib.sha256(f"{nonce}:{solution}".encode()).hexdigest().startswith(target):
            solution += 1
        return nonce, solution

    def _get(self, url: str) -> requests.Response:
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            if "Checking your browser" in response.text and 'xhr.open(\'POST\',"/__c"' in response.text:
                nonce, solution = self._solve_browser_check(response.text)
                challenge_url = urljoin(response.url, "/__c")
                solved = self.session.post(
                    challenge_url,
                    data={"nonce": nonce, "n": solution},
                    headers={"Referer": response.url},
                    timeout=self.timeout,
                )
                solved.raise_for_status()
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
            if "Checking your browser" in response.text:
                raise UFCStatsError("UFCStats browser check could not be completed")
            return response
        except requests.RequestException as exc:
            raise UFCStatsError(f"Could not reach UFCStats: {exc}") from exc

    @staticmethod
    def parse_directory(html: str) -> list[dict[str, str]]:
        fighters: list[dict[str, str]] = []
        soup = BeautifulSoup(html, "html.parser")
        for row in soup.select("tr.b-statistics__table-row"):
            cells = row.select("td.b-statistics__table-col")
            link = row.select_one('a[href*="/fighter-details/"]')
            if len(cells) < 3 or link is None:
                continue
            first = cells[0].get_text(" ", strip=True)
            last = cells[1].get_text(" ", strip=True)
            if not first or not last:
                continue
            fighters.append({
                "name": f"{first} {last}",
                "nickname": cells[2].get_text(" ", strip=True),
                "url": link.get("href", "").strip(),
            })
        return fighters

    @staticmethod
    def parse_profile(html: str, match: dict[str, str]) -> FighterProfile:
        soup = BeautifulSoup(html, "html.parser")
        values: dict[str, str] = {}
        for item in soup.select("li.b-list__box-list-item"):
            text = " ".join(item.stripped_strings)
            if ":" not in text:
                continue
            label, value = text.split(":", 1)
            key = re.sub(r"[^A-Z]+", " ", label.upper()).strip()
            values[key] = value.strip()

        title = soup.select_one("h2.b-content__title")
        title_text = " ".join(title.stripped_strings) if title else ""
        record_match = re.search(r"Record:\s*(.+)$", title_text)
        dob = None
        if values.get("DOB"):
            try:
                dob = datetime.strptime(values["DOB"], "%b %d, %Y")
            except ValueError:
                pass

        required = {"HEIGHT", "WEIGHT", "REACH", "STANCE", "SLPM", "SAPM"}
        if not required.intersection(values):
            raise UFCStatsError(f"UFCStats profile markup was not recognized for {match['name']}")

        return FighterProfile(
            name=match["name"],
            nickname=match.get("nickname", ""),
            url=match["url"],
            record=record_match.group(1).strip() if record_match else "",
            height_inches=_height_inches(values.get("HEIGHT", "")),
            weight_lbs=_number(values.get("WEIGHT", "")),
            reach_inches=_number(values.get("REACH", "")),
            stance=values.get("STANCE") or None,
            dob=dob,
            slpm=_number(values.get("SLPM", "")),
            str_acc=_percent(values.get("STR ACC", "")),
            sapm=_number(values.get("SAPM", "")),
            str_def=_percent(values.get("STR DEF", "")),
            td_avg=_number(values.get("TD AVG", "")),
            td_acc=_percent(values.get("TD ACC", "")),
            td_def=_percent(values.get("TD DEF", "")),
            sub_avg=_number(values.get("SUB AVG", "")),
        )

    def _directory(self, letter: str) -> list[dict[str, str]]:
        if letter not in self._directory_cache:
            url = f"{BASE_URL}/statistics/fighters?char={letter}&page=all"
            self._directory_cache[letter] = self.parse_directory(self._get(url).text)
        return self._directory_cache[letter]

    def get_fighter(self, user_input: str) -> FighterProfile:
        query = normalize_fighter_name(user_input)
        if len(query.split()) < 2:
            raise FighterNotFound(
                f"Enter a full fighter name using firstname_lastname, not {user_input!r}"
            )
        if query in self._profile_cache:
            return self._profile_cache[query]

        displayed = display_input_name(user_input)
        last_name = normalize_fighter_name(displayed.split()[-1])
        matches = [
            fighter
            for fighter in self._directory(last_name[0])
            if normalize_fighter_name(fighter["name"]) == query
        ]
        if not matches:
            raise FighterNotFound(
                f"No UFCStats fighter found for {user_input!r}. "
                "Enter a different exact full name using firstname_lastname."
            )

        profile = self.parse_profile(self._get(matches[0]["url"]).text, matches[0])
        self._profile_cache[query] = profile
        return profile
