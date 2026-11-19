const tokenSessao = localStorage.getItem("tokenVeterinario");
const vetLogado = localStorage.getItem("veterinarioLogado");

if (!tokenSessao || !vetLogado) {
    window.location.href = "login.html";
}

const fetchOriginal = window.fetch;
window.fetch = async (url, options = {}) => {
    if (
        typeof url === "string" &&
        (url.startsWith("http://127.0.0.1:8000") || url.startsWith("http://localhost:8000"))
    ) {
        options.headers = {
            ...options.headers,
            "Authorization": `Bearer ${localStorage.getItem("tokenVeterinario") || ""}`
        };
    }

    const resposta = await fetchOriginal(url, options);

    if (resposta.status === 401 && !url.includes("/login")) {
        localStorage.removeItem("tokenVeterinario");
        localStorage.removeItem("veterinarioLogado");
        window.location.href = "login.html";
    }

    return resposta;
};

async function fazerLogout() {
    try {
        await fetch("http://127.0.0.1:8000/logout", { method: "POST" });
    } catch (e) {
        // Ignora falha de rede ao encerrar sessão
    } finally {
        localStorage.removeItem("tokenVeterinario");
        localStorage.removeItem("veterinarioLogado");
        window.location.href = "login.html";
    }
}