

// Keeps track of what's currently in the betslip
let betslipSelections = [];

checkAuth();

async function checkAuth() {
    try {
        const response = await fetch(`${API_BASE}/me`, {
            credentials: "include"
        });

        if (!response.ok) {
            window.location.href = "auth.html";
            return;
        }

        loadGames();

    } catch (error) {
        window.location.href = "auth.html";
    }
}

// Runs as soon as the page loads
loadGames();

async function loadGames() {
    const container = document.getElementById("games-container");

    try {
        const response = await fetch(`${API_BASE}/games`, {
            credentials: "include"
        });
        const data = await response.json();

        container.innerHTML = ""; // clear "Loading games..."

        data.games.forEach(game => {
            const card = createGameCard(game);
            container.appendChild(card);
        });

    } catch (error) {
        container.innerHTML = `<p class="loading-text">Couldn't load games. Is the backend running?</p>`;
        console.error(error);
    }
}

function createGameCard(game) {
    const card = document.createElement("div");
    card.className = "game-card";

    const kickoffTime = new Date(game.commence_time).toLocaleString();

    card.innerHTML = `
        <div class="game-teams">
            <span>${game.home_team}</span>
            <span>vs</span>
            <span>${game.away_team}</span>
        </div>
        <div class="game-time">${kickoffTime}</div>
        <div class="odds-row">
            <button class="odds-btn" data-pick="${game.home_team}" data-odds="${game.odds.home}">
                Home<br>${game.odds.home ?? "-"}
            </button>
            <button class="odds-btn" data-pick="Draw" data-odds="${game.odds.draw}">
                Draw<br>${game.odds.draw ?? "-"}
            </button>
            <button class="odds-btn" data-pick="${game.away_team}" data-odds="${game.odds.away}">
                Away<br>${game.odds.away ?? "-"}
            </button>
        </div>
    `;

    // Attach a click handler to each of the 3 odds buttons
    const oddsButtons = card.querySelectorAll(".odds-btn");
    oddsButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            addSelection({
                league: "EPL",
                home_team: game.home_team,
                away_team: game.away_team,
                pick: btn.dataset.pick,
                odds: parseFloat(btn.dataset.odds)
            });
            btn.classList.add("selected");
        });
    });

    return card;
}

function addSelection(selection) {
    betslipSelections.push(selection);
    renderBetslip();
    document.getElementById("betslip-drawer").classList.remove("hidden");
}

function renderBetslip() {
    const container = document.getElementById("betslip-selections");
    container.innerHTML = "";

    betslipSelections.forEach((sel, index) => {
        const line = document.createElement("div");
        line.textContent = `${sel.pick} @ ${sel.odds}`;
        container.appendChild(line);
    });

    updatePayout();
}

function updatePayout() {
    const stakeInput = document.getElementById("stake-input");
    const stake = parseFloat(stakeInput.value) || 0;

    let totalOdds = 1;
    betslipSelections.forEach(sel => {
        totalOdds *= sel.odds;
    });

    const payout = (stake * totalOdds).toFixed(2);
    document.getElementById("potential-payout").textContent = `₦${payout}`;
}

document.getElementById("stake-input").addEventListener("input", updatePayout);

document.getElementById("close-betslip").addEventListener("click", () => {
    document.getElementById("betslip-drawer").classList.add("hidden");
});

document.getElementById("place-bet-btn").addEventListener("click", async () => {
    const stake = parseFloat(document.getElementById("stake-input").value);

       if (!stake || betslipSelections.length === 0) {
        showToast("Enter a stake and pick at least one game.", true);
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/place-bet`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ stake, selections: betslipSelections })
        });

        const data = await response.json();

      
        if (!response.ok) {
            showToast(data.error || "Something went wrong.", true);
            return;
        }

        showToast(`Bet placed! Potential payout: ₦${data.potential_payout}`);
     
        betslipSelections = [];
        document.getElementById("betslip-drawer").classList.add("hidden");
        document.getElementById("stake-input").value = "";

        } catch (error) {
        showToast("Couldn't reach the server.", true);
        console.error(error);
    }
});