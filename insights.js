loadInsights();

async function loadInsights() {
    const container = document.getElementById("insights-container");

    try {
        const response = await fetch(`${API_BASE}/insights`, {
            credentials: "include"
        });

        if (!response.ok) {
            window.location.href = "auth.html";
            return;
        }

        const data = await response.json();

        if (!data.has_data) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>${data.message}</p>
                    <a href="index.html" class="landing-cta">Place a Bet →</a>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <div class="stats-grid">
                <div class="stat-block">
                    <span class="stat-number">${data.overall_win_rate}%</span>
                    <span class="stat-label">Win Rate</span>
                </div>
                <div class="stat-block">
                    <span class="stat-number">${data.total_bets}</span>
                    <span class="stat-label">Bets Settled</span>
                </div>
                <div class="stat-block">
                    <span class="stat-number">₦${data.average_stake}</span>
                    <span class="stat-label">Avg. Stake</span>
                </div>
                <div class="stat-block">
                    <span class="stat-number">₦${data.average_payout}</span>
                    <span class="stat-label">Avg. Payout (Won)</span>
                </div>
                <div class="stat-block">
                    <span class="stat-number">${data.best_day ?? "-"}</span>
                    <span class="stat-label">Best Day</span>
                </div>
                <div class="stat-block">
                    <span class="stat-number">${data.worst_day ?? "-"}</span>
                    <span class="stat-label">Worst Day</span>
                </div>
            </div>

            <div class="league-breakdown">
                <div class="section-label">Win Rate by League</div>
                <div id="league-list"></div>
            </div>
        `;

        const leagueList = document.getElementById("league-list");
        const leagues = Object.entries(data.win_rate_by_league);

        if (leagues.length === 0) {
            leagueList.innerHTML = `<p class="loading-text">No league data yet.</p>`;
        } else {
            leagues.forEach(([league, rate]) => {
                const row = document.createElement("div");
                row.className = "league-row";
                row.innerHTML = `
                    <span class="league-name">${league}</span>
                    <span class="league-rate">${rate}%</span>
                `;
                leagueList.appendChild(row);
            });
        }

    } catch (error) {
        container.innerHTML = `<p class="loading-text">Couldn't load insights.</p>`;
    }
}