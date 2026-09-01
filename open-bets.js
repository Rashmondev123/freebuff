loadOpenBets();

async function loadOpenBets() {
    const container = document.getElementById("bets-container");

    try {
        const response = await fetch(`${API_BASE}/my-bets`, {
            credentials: "include"
        });

        if (!response.ok) {
            window.location.href = "auth.html";
            return;
        }

        const data = await response.json();
        renderBetCards(data.bets, "bets-container", "No open slips yet. Pick a game and place your first bet.");

    } catch (error) {
        container.innerHTML = `<p class="loading-text">Couldn't load your bets.</p>`;
    }
}