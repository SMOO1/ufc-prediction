const form = document.querySelector("#predictionForm");
const submitButton = document.querySelector("#submitButton");
const buttonLabel = submitButton.querySelector(".button-label");
const buttonLoading = submitButton.querySelector(".button-loading");
const errorMessage = document.querySelector("#errorMessage");
const results = document.querySelector("#results");

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    hideError();
    results.hidden = true;

    const fighter1 = document.querySelector("#fighter1").value.trim();
    const fighter2 = document.querySelector("#fighter2").value.trim();
    if (!fighter1 || !fighter2) {
        showError("Enter the full name of both fighters.");
        return;
    }

    setLoading(true);
    try {
        const response = await fetch("/api/predictions", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({fighter1, fighter2})
        });

        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(data.message || "The prediction could not be completed.");
        }
        renderResults(data);
    } catch (error) {
        showError(error.message || "The prediction service is unavailable. Please try again.");
    } finally {
        setLoading(false);
    }
});

function setLoading(isLoading) {
    submitButton.disabled = isLoading;
    buttonLabel.hidden = isLoading;
    buttonLoading.hidden = !isLoading;
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.hidden = false;
    errorMessage.scrollIntoView({behavior: "smooth", block: "center"});
}

function hideError() {
    errorMessage.hidden = true;
    errorMessage.textContent = "";
}

function renderResults(data) {
    const prediction = data.prediction;
    const redPercent = prediction.redProbability * 100;
    const bluePercent = prediction.blueProbability * 100;
    const redWins = redPercent >= bluePercent;

    text("#redResultName", prediction.redName);
    text("#blueResultName", prediction.blueName);
    text("#redProbability", formatPercent(prediction.redProbability));
    text("#blueProbability", formatPercent(prediction.blueProbability));
    text("#winnerName", redWins ? prediction.redName : prediction.blueName);
    text("#confidenceLabel", confidenceLabel(Math.max(redPercent, bluePercent)));

    const profileCards = document.querySelector("#profileCards");
    profileCards.replaceChildren();
    data.fighters.forEach((fighter) => profileCards.append(profileCard(fighter)));

    results.hidden = false;
    results.scrollIntoView({behavior: "smooth", block: "start"});
}

function profileCard(fighter) {
    const card = document.createElement("article");
    card.className = "profile-card";
    card.innerHTML = `
        <header>
            <div><h3></h3><p class="nickname"></p></div>
            <span class="record"></span>
        </header>
        <div class="stats-grid"></div>
        <div class="detail-row"></div>
        <a class="profile-link" target="_blank" rel="noreferrer">UFCStats ↗</a>`;

    card.querySelector("h3").textContent = fighter.name;
    const nickname = card.querySelector(".nickname");
    nickname.textContent = fighter.nickname ? `“${fighter.nickname}”` : "";
    nickname.hidden = !fighter.nickname;
    card.querySelector(".record").textContent = fighter.record || "Record N/A";

    const stats = [
        ["SLpM", number(fighter.slpm)],
        ["Str. acc.", percent(fighter.strikingAccuracy)],
        ["SApM", number(fighter.sapm)],
        ["Str. def.", percent(fighter.strikingDefense)],
        ["TD avg.", number(fighter.takedownAverage)],
        ["TD acc.", percent(fighter.takedownAccuracy)],
        ["TD def.", percent(fighter.takedownDefense)],
        ["Sub avg.", number(fighter.submissionAverage)]
    ];
    const statsGrid = card.querySelector(".stats-grid");
    for (const [label, value] of stats) {
        statsGrid.append(statElement(label, value));
    }

    const details = [
        ["Height", height(fighter.heightInches)],
        ["Reach", fighter.reachInches == null ? "N/A" : `${number(fighter.reachInches)} in`],
        ["Weight", fighter.weightLbs == null ? "N/A" : `${number(fighter.weightLbs)} lbs`],
        ["Stance", fighter.stance || "N/A"],
        ["Born", fighter.dob ? formatDate(fighter.dob) : "N/A"]
    ];
    const detailRow = card.querySelector(".detail-row");
    for (const [label, value] of details) {
        detailRow.append(statElement(label, value));
    }

    const link = card.querySelector(".profile-link");
    link.href = fighter.url;
    return card;
}

function statElement(label, value) {
    const item = document.createElement("div");
    item.className = "stat";
    const key = document.createElement("span");
    const result = document.createElement("strong");
    key.textContent = label;
    result.textContent = value;
    item.append(key, result);
    return item;
}

function text(selector, value) {
    document.querySelector(selector).textContent = value;
}

function number(value) {
    return value == null ? "N/A" : Number(value).toFixed(2).replace(/\.00$/, "").replace(/(\.\d)0$/, "$1");
}

function percent(value) {
    return value == null ? "N/A" : `${Math.round(value * 100)}%`;
}

function formatPercent(value) {
    return `${(value * 100).toFixed(1)}%`;
}

function height(inches) {
    if (inches == null) return "N/A";
    return `${Math.floor(inches / 12)}′ ${Math.round(inches % 12)}″`;
}

function formatDate(value) {
    return new Intl.DateTimeFormat("en", {year: "numeric", month: "short", day: "numeric", timeZone: "UTC"})
        .format(new Date(`${value}T00:00:00Z`));
}

function confidenceLabel(winnerPercent) {
    if (winnerPercent >= 70) return "High model separation";
    if (winnerPercent >= 60) return "Moderate model separation";
    return "Close matchup";
}
