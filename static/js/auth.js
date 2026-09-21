(async function initializeClerk() {
    const root = document.getElementById("clerk-auth-root");
    const publishableKey = document.querySelector('meta[name="clerk-publishable-key"]')?.content;
    if (!publishableKey || !window.Clerk) {
        if (root) root.innerHTML = '<div class="alert alert-danger">Authentication could not be loaded.</div>';
        return;
    }

    const proxyUrl = document.querySelector('meta[name="clerk-proxy-url"]')?.content || undefined;
    await window.Clerk.load({ publishableKey, proxyUrl });

    if (root) {
        const mode = root.dataset.mode;
        const requestedNext = new URLSearchParams(window.location.search).get("next") || "/";
        const next = requestedNext.startsWith("/") && !requestedNext.startsWith("//")
            ? requestedNext
            : "/";
        const appearance = {
            variables: {
                colorPrimary: "#0d6efd",
                colorForeground: "#172033",
                colorMutedForeground: "#687386",
                colorBackground: "#ffffff",
                colorInput: "#f8fafc",
                colorInputForeground: "#172033",
                colorDanger: "#dc3545",
                colorNeutral: "#d8dee8",
                fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
                borderRadius: "0.75rem"
            },
            elements: {
                rootBox: { width: "100%" },
                cardBox: { width: "100%", boxShadow: "none" },
                card: { boxShadow: "none", border: "0" },
                formButtonPrimary: { backgroundColor: "#0d6efd" },
                footerActionLink: { color: "#0d6efd" }
            }
        };

        const options = {
            appearance,
            routing: "path",
            fallbackRedirectUrl: next
        };

        if (mode === "sign-up") {
            window.Clerk.mountSignUp(root, { ...options, path: "/sign-up", signInUrl: "/sign-in" });
        } else {
            window.Clerk.mountSignIn(root, { ...options, path: "/sign-in", signUpUrl: "/sign-up" });
        }
    }

    document.querySelectorAll("[data-clerk-sign-out]").forEach((button) => {
        button.addEventListener("click", () => window.Clerk.signOut({ redirectUrl: "/" }));
    });
})();