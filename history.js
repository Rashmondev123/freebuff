loadHistory();

async function loadHistory() {
    const container = document.getElementById("bets-container");

    try {
        const response = await fetch(`${API_BASE}/bet-history`, {
            credentials: "include"
        });

        if (!response.ok) {
            window.location.href = "auth.html";
            return;
        }

        const data = await response.json();
        renderBetCards(data.bets, "bets-container", "No settled bets yet. Once a slip finishes, it'll show up here.");

    } catch (error) {
        container.innerHTML = `<p class="loading-text">Couldn't load your history.</p>`;
    }
}