const API_URL = "http://127.0.0.1:8000";

function dataLocalHoje() {
    const agora = new Date();
    agora.setMinutes(agora.getMinutes() - agora.getTimezoneOffset());
    return agora.toISOString().slice(0, 10);
}

document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("form-vacina").addEventListener("submit", cadastrarVacina);
    document.getElementById("btn-atualizar").addEventListener("click", carregarVacinas);
    document.getElementById("data_aplicacao").value = dataLocalHoje();
    carregarAnimais();
    carregarVacinas();
});

async function carregarAnimais() {
    const seletor = document.getElementById("animal_id");

    try {
        const resposta = await fetch(`${API_URL}/animais`);
        if (!resposta.ok) {
            throw new Error("Não foi possível carregar os animais.");
        }

        const animais = await resposta.json();
        seletor.innerHTML = '<option value="">Selecione um animal...</option>';
        animais.forEach((animal) => {
            const opcao = document.createElement("option");
            opcao.value = animal.id;
            opcao.textContent = `${animal.nome} (ID: ${animal.id})`;
            seletor.appendChild(opcao);
        });
    } catch (erro) {
        console.error("Erro ao carregar animais:", erro);
        alert("Não foi possível carregar os animais.");
    }
}

function adicionarCelula(linha, valor) {
    const celula = document.createElement("td");
    celula.textContent = valor || "-";
    linha.appendChild(celula);
    return celula;
}

function rotuloStatus(vacina) {
    if (!vacina.antirrabica) return "Não se aplica";
    const tentativas = vacina.integracao_tentativas ?? 0;
    const protocolo = vacina.integracao_protocolo
        ? ` · Protocolo: ${vacina.integracao_protocolo}`
        : "";
    const erro = vacina.integracao_erro ? ` · ${vacina.integracao_erro}` : "";
    return `${vacina.integracao_status || "pendente"} · ${tentativas} tentativa(s)${protocolo}${erro}`;
}

function podeReenviar(vacina) {
    if (["erro", "pendente"].includes(vacina.integracao_status)) return true;
    if (vacina.integracao_status !== "enviando" || !vacina.integracao_ultima_tentativa) return false;
    return Date.now() - new Date(vacina.integracao_ultima_tentativa).getTime() >= 5 * 60 * 1000;
}

async function carregarVacinas() {
    const tabela = document.getElementById("lista-vacinas");

    try {
        const resposta = await fetch(`${API_URL}/vacinas`);
        if (!resposta.ok) {
            throw new Error("Não foi possível carregar o histórico.");
        }

        const vacinas = await resposta.json();
        tabela.replaceChildren();
        if (!vacinas.length) {
            const linha = document.createElement("tr");
            const celula = adicionarCelula(linha, "Nenhuma vacinação registrada.");
            celula.colSpan = 7;
            tabela.appendChild(linha);
            return;
        }

        vacinas.forEach((vacina) => {
            const linha = document.createElement("tr");
            adicionarCelula(linha, vacina.data_aplicacao);
            adicionarCelula(linha, `${vacina.animal} (ID: ${vacina.animal_id})`);
            adicionarCelula(
                linha,
                `${vacina.nome}${vacina.antirrabica ? " (antirrábica)" : ""} · ${vacina.dose}`
            );
            adicionarCelula(linha, vacina.lote);
            adicionarCelula(linha, vacina.data_proxima_dose);
            adicionarCelula(linha, vacina.veterinario);
            const celulaIntegracao = adicionarCelula(linha, rotuloStatus(vacina));

            if (vacina.antirrabica && podeReenviar(vacina)) {
                const botao = document.createElement("button");
                botao.type = "button";
                botao.textContent = "Reenviar";
                botao.addEventListener("click", () => reenviarVacina(vacina.id, botao));
                celulaIntegracao.appendChild(document.createElement("br"));
                celulaIntegracao.appendChild(botao);
            }

            tabela.appendChild(linha);
        });
    } catch (erro) {
        console.error("Erro ao carregar histórico de vacinação:", erro);
        tabela.replaceChildren();
        const linha = document.createElement("tr");
        const celula = adicionarCelula(linha, "Erro ao carregar o histórico de vacinação.");
        celula.colSpan = 7;
        tabela.appendChild(linha);
    }
}

async function cadastrarVacina(evento) {
    evento.preventDefault();
    const formulario = document.getElementById("form-vacina");
    const payload = {
        animal_id: Number(document.getElementById("animal_id").value),
        nome: document.getElementById("nome").value.trim(),
        antirrabica: document.getElementById("antirrabica").checked,
        fabricante: document.getElementById("fabricante").value.trim() || null,
        lote: document.getElementById("lote").value.trim(),
        dose: document.getElementById("dose").value.trim(),
        data_aplicacao: document.getElementById("data_aplicacao").value,
        data_proxima_dose: document.getElementById("data_proxima_dose").value || null,
        observacoes: document.getElementById("observacoes").value.trim() || null
    };

    try {
        const resposta = await fetch(`${API_URL}/vacinas`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const resultado = await resposta.json();
        if (!resposta.ok) {
            alert(resultado.detail || "Não foi possível registrar a vacinação.");
            return;
        }

        if (resultado.integracao && resultado.integracao.status !== "enviado") {
            alert(`Vacinação registrada. Integração: ${resultado.integracao.ultimo_erro || resultado.integracao.status}.`);
        } else {
            alert("Vacinação registrada com sucesso!");
        }

        formulario.reset();
        document.getElementById("data_aplicacao").value = dataLocalHoje();
        await carregarVacinas();
    } catch (erro) {
        console.error("Erro ao registrar vacinação:", erro);
        alert("Não foi possível conectar ao servidor.");
    }
}

async function reenviarVacina(vacinaId, botao) {
    botao.disabled = true;
    botao.textContent = "Enviando...";

    try {
        const resposta = await fetch(`${API_URL}/vacinas/${vacinaId}/reenviar`, {
            method: "POST"
        });
        const resultado = await resposta.json();
        if (!resposta.ok) {
            throw new Error(resultado.detail || "Não foi possível reenviar a vacinação.");
        }

        alert(
            resultado.status === "enviado"
                ? "Vacinação enviada à integração governamental."
                : `Envio não concluído: ${resultado.ultimo_erro || resultado.status}.`
        );
        await carregarVacinas();
    } catch (erro) {
        console.error("Erro ao reenviar vacinação:", erro);
        alert(erro.message || "Falha de comunicação ao reenviar a vacinação.");
        botao.disabled = false;
        botao.textContent = "Reenviar";
    }
}
