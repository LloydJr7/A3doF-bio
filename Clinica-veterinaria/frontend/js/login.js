const API_URL = "http://127.0.0.1:8000";
let ultimoVeterinarioId = null;

function exibirAlerta(mensagem, tipo) {
    const alerta = document.getElementById("mensagem-alerta");
    alerta.textContent = mensagem;
    alerta.className = `alerta ${tipo}`;
    alerta.style.display = "block";
}

document.getElementById("form-login").addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("login-email").value;
    const senha = document.getElementById("login-senha").value;

    try {
        const resposta = await fetch(`${API_URL}/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, senha })
        });

        const dados = await resposta.json();

        if (!resposta.ok) {
            exibirAlerta(dados.detail || "Erro ao realizar login.", "erro");
            return;
        }

        localStorage.setItem("tokenVeterinario", dados.token);
        localStorage.setItem("veterinarioLogado", JSON.stringify(dados.veterinario));
        exibirAlerta("Login realizado com sucesso! Redirecionando...", "sucesso");
        setTimeout(() => {
            window.location.href = "index.html";
        }, 1000);
    } catch (erro) {
        exibirAlerta("Não foi possível conectar ao servidor da API.", "erro");
    }
});

document.getElementById("form-cadastro-vet").addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
        nome_completo: document.getElementById("vet-nome").value,
        cpf: document.getElementById("vet-cpf").value,
        crmv: document.getElementById("vet-crmv").value,
        uf_crmv: document.getElementById("vet-uf").value,
        email: document.getElementById("vet-email").value,
        telefone: document.getElementById("vet-telefone").value,
        senha: document.getElementById("vet-senha").value
    };

    try {
        const resposta = await fetch(`${API_URL}/veterinarios`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const dados = await resposta.json();

        if (!resposta.ok) {
            exibirAlerta(dados.detail || "Erro ao cadastrar veterinário.", "erro");
            return;
        }

        ultimoVeterinarioId = dados.veterinario_id;
        exibirAlerta(dados.mensagem, "sucesso");
        document.getElementById("form-cadastro-vet").reset();

        const box = document.getElementById("box-confirmacao");
        const inputCodigo = document.getElementById("codigo-confirmacao");
        inputCodigo.value = "";
        document.getElementById("texto-confirmacao").textContent =
            `Enviamos um código de 6 dígitos para ${payload.email}. Digite-o abaixo para confirmar sua senha e liberar o login:`;
        box.style.display = "block";
        inputCodigo.focus();
    } catch (erro) {
        exibirAlerta("Erro de comunicação com o servidor.", "erro");
    }
});

document.getElementById("btn-confirmar-senha").addEventListener("click", async () => {
    if (!ultimoVeterinarioId) return;

    const codigo = document.getElementById("codigo-confirmacao").value.trim();

    if (!/^\d{6}$/.test(codigo)) {
        exibirAlerta("Por favor, digite um código válido de 6 dígitos numéricos.", "erro");
        return;
    }

    try {
        const resposta = await fetch(`${API_URL}/veterinarios/${ultimoVeterinarioId}/confirmar-senha`, {
            method: "PATCH"
        });

        const dados = await resposta.json();

        if (!resposta.ok) {
            exibirAlerta(dados.detail || "Erro ao confirmar senha.", "erro");
            return;
        }

        exibirAlerta(dados.mensagem, "sucesso");
        document.getElementById("box-confirmacao").style.display = "none";
        document.getElementById("codigo-confirmacao").value = "";
    } catch (erro) {
        exibirAlerta("Erro ao confirmar senha na API.", "erro");
    }
});