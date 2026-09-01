const API_BASE = "http://127.0.0.1:5000";

const tabLogin = document.getElementById("tab-login");
const tabSignup = document.getElementById("tab-signup");
const loginForm = document.getElementById("login-form");
const signupForm = document.getElementById("signup-form");

tabLogin.addEventListener("click", () => {
    tabLogin.classList.add("active");
    tabSignup.classList.remove("active");
    loginForm.classList.remove("hidden");
    signupForm.classList.add("hidden");
});

tabSignup.addEventListener("click", () => {
    tabSignup.classList.add("active");
    tabLogin.classList.remove("active");
    signupForm.classList.remove("hidden");
    loginForm.classList.add("hidden");
});

loginForm.addEventListener("submit", async (e) => {
    e.preventDefault(); // stops the page from reloading, the browser's default form behavior

    const email = document.getElementById("login-email").value;
    const password = document.getElementById("login-password").value;
    const errorEl = document.getElementById("login-error");

    try {
        const response = await fetch(`${API_BASE}/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (!response.ok) {
            errorEl.textContent = data.error;
            return;
        }

        window.location.href = "index.html";

    } catch (error) {
        errorEl.textContent = "Couldn't reach the server.";
    }
});

signupForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const email = document.getElementById("signup-email").value;
    const password = document.getElementById("signup-password").value;
    const errorEl = document.getElementById("signup-error");

    try {
        const response = await fetch(`${API_BASE}/signup`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (!response.ok) {
            errorEl.textContent = data.error;
            return;
        }

        // Auto-login isn't built into /signup, so send them to log in next
        tabLogin.click();
        document.getElementById("login-email").value = email;

    } catch (error) {
        errorEl.textContent = "Couldn't reach the server.";
    }
});