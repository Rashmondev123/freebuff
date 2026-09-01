const API_BASE = "http://127.0.0.1:5000";

async function loadBalance() {
    try {
        const response = await fetch(`${API_BASE}/me`, { credentials: "include" });
        const data = await response.json();
        const balanceEl = document.getElementById("balance-display");
        if (balanceEl && data.balance !== undefined) {
            balanceEl.textContent = `₦${data.balance.toLocaleString(undefined, {minimumFractionDigits: 2})}`;
        }
    } catch (error) {
        console.error("Couldn't load balance");
    }
}
loadBalance();


function renderBetCards(bets, containerId, emptyMessage) {
    const container = document.getElementById(containerId);
    container.innerHTML = "";

    if (bets.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p>${emptyMessage}</p>
                <a href="index.html" class="landing-cta">Browse Games →</a>
            </div>
        `;
        return;
    }

    bets.forEach(bet => {
        const card = document.createElement("div");
        card.className = "bet-card";

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

             card.innerHTML = `
            ${stampHTML}
            <div class="bet-card-header">
                <span>Slip #${bet.slip_id}</span>
                <span>${new Date(bet.date_placed).toLocaleDateString()}</span>
            </div>
            ${selectionsHTML}
            <div class="bet-card-footer">
                <span>Stake: ₦${bet.stake.toFixed(2)}</span>
                <span>Payout: ₦${bet.potential_payout.toFixed(2)}</span>
            </div>
            <button class="share-btn" data-code="${bet.share_code}">Share Slip</button>
        `;

        const shareBtn = card.querySelector(".share-btn");
        shareBtn.addEventListener("click", () => {
            const shareUrl = `${window.location.origin}/share.html?code=${bet.share_code}`;
            navigator.clipboard.writeText(shareUrl);
            showToast("Share link copied!");
        });
        
        container.appendChild(card);
    });
}


function showToast(message, isError = false) {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = "toast";
    if (isError) toast.classList.add("toast-error");
    toast.textContent = message;

    container.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3000);
}