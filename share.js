const API_BASE = "https://freebuff-backend.onrender.com";

loadSharedSlip();

async function loadSharedSlip() {
    const container = document.getElementById("slip-container");

    // Reads the ?code=xxxx part from the current page's URL
    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");

    if (!code) {
        container.innerHTML = `<p class="loading-text">No slip code provided.</p>`;
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/slip/${code}`);

        if (!response.ok) {
            container.innerHTML = `<p class="loading-text">This slip couldn't be found.</p>`;
            return;
        }

        const bet = await response.json();

        let stampHTML = "";
        if (bet.status === "won") {
            stampHTML = `<div class="stamp stamp-won">Won</div>`;
        } else if (bet.status === "lost") {
            stampHTML = `<div class="stamp stamp-lost">Lost</div>`;
        }

        const selectionsHTML = bet.selections.map(sel => `
            <div class="bet-selection-line">
                <span class="bet-selection-pick">${sel.pick} @ ${sel.odds}</span>
                <span class="bet-selection-result result-${sel.result}">${sel.result}</span>
            </div>
        `).join("");

        container.innerHTML = `
            <div class="bet-card">
                ${stampHTML}
                <div class="bet-card-header">
                    <span>${bet.selections.length}-Game Slip</span>
                    <span>${new Date(bet.date_placed).toLocaleDateString()}</span>
                </div>
                ${selectionsHTML}
                <div class="bet-card-footer">
                    <span>Stake: ₦${bet.stake.toFixed(2)}</span>
                    <span>Payout: ₦${bet.potential_payout.toFixed(2)}</span>
                </div>
            </div>
        `;

    } catch (error) {
        container.innerHTML = `<p class="loading-text">Couldn't load this slip.</p>`;
    }
}