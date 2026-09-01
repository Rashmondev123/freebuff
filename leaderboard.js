loadLeaderboard();
loadCurrentName();

async function loadCurrentName() {
    try {
        const response = await fetch(`${API_BASE}/me`, { credentials: "include" });
        if (!response.ok) return; // not logged in — that's fine, leaderboard is still viewable

        const data = await response.json();
        document.getElementById("display-name-input").value = data.display_name;
    } catch (error) {
        console.error("Couldn't load current name");
    }
}

document.getElementById("save-name-btn").addEventListener("click", async () => {
    const input = document.getElementById("display-name-input");
    const newName = input.value.trim();

    if (!newName) {
        showToast("Enter a display name", true);
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/update-display-name`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ display_name: newName })
        });

        const data = await response.json();

        if (!response.ok) {
            showToast(data.error, true);
            return;
        }

        showToast("Display name updated!");
        loadLeaderboard(); // refresh so the new name shows immediately

    } catch (error) {
        showToast("Couldn't reach the server.", true);
    }
});

async function loadLeaderboard() {
    const container = document.getElementById("leaderboard-container");

    try {
        const response = await fetch(`${API_BASE}/leaderboard`);
        const data = await response.json();

        if (data.leaderboard.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>No one's qualified yet — place and settle at least 3 bets to be the first on the board.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = "";

        data.leaderboard.forEach((entry, index) => {
            const rank = index + 1;
            const row = document.createElement("div");
            row.className = "leaderboard-row";
            if (rank <= 3) row.classList.add("top-three");

            const profitClass = entry.net_profit >= 0 ? "profit-positive" : "profit-negative";
            const profitSign = entry.net_profit >= 0 ? "+" : "";

            row.innerHTML = `
                <span class="leaderboard-rank">${rank}</span>
                <div class="leaderboard-info">
                    <div class="leaderboard-name">${entry.display_name}</div>
                    <div class="leaderboard-meta">${entry.total_bets} bets settled</div>
                </div>
                <div class="leaderboard-stats">
                    <span class="leaderboard-winrate">${entry.win_rate}%</span>
                    <span class="leaderboard-profit ${profitClass}">${profitSign}₦${entry.net_profit.toFixed(2)}</span>
                </div>
            `;

            container.appendChild(row);
        });

    } catch (error) {
        container.innerHTML = `<p class="loading-text">Couldn't load the leaderboard.</p>`;
    }
}