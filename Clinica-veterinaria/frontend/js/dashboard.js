
const API_URL = "http://127.0.0.1:8000";

async function atualizarEstatistica(endpoint, elementoId) {
    const elemento = document.getElementById(elementoId);

    if (!elemento) {
        console.error(`Elemento não encontrado: ${elementoId}`);
        return;
    }

    try {
        const resposta = await fetch(`${API_URL}/${endpoint}`);

        if (!resposta.ok) {
            throw new Error(`Erro ao buscar ${endpoint}`);
        }

        const dados = await resposta.json();

        elemento.textContent = dados.length;

    } catch (erro) {
        console.error(`Erro ao carregar ${endpoint}:`, erro);
        elemento.textContent = "Erro";
    }
}

document.addEventListener("DOMContentLoaded", () => {
    atualizarEstatistica("animais", "total-animais");
    atualizarEstatistica("microchips", "total-microchips");
    atualizarEstatistica("consultas", "total-consultas");
});
