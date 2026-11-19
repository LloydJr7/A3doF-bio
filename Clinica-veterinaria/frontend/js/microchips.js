const API_URL = "http://127.0.0.1:8000";

let mapaAnimais = {};
let listaMicrochipsCache = [];

document.addEventListener("DOMContentLoaded", () => {
    carregarAnimais();
    carregarMicrochips();

    document.getElementById("form-microchip").addEventListener("submit", cadastrarMicrochip);
    document.getElementById("btn-atualizar").addEventListener("click", carregarMicrochips);
    document.getElementById("form-busca-microchip").addEventListener("submit", buscarPorCodigo);
    document.getElementById("btn-limpar-busca").addEventListener("click", limparBusca);
});

async function carregarAnimais() {
    try {
        const resposta = await fetch(`${API_URL}/animais`);
        if (!resposta.ok) return;

        const animais = await resposta.json();
        const select = document.getElementById("animal_id");
        select.innerHTML = '<option value="">Selecione um animal...</option>';
        mapaAnimais = {};

        animais.forEach((animal) => {
            const id = animal.animal_id ?? animal.id;
            const nome = animal.nome || `Animal #${id}`;
            mapaAnimais[id] = animal;

            const option = document.createElement("option");
            option.value = id;
            option.textContent = `${nome} (ID: ${id})`;
            select.appendChild(option);
        });
    } catch (erro) {
        console.error("Erro ao carregar animais:", erro);
    }
}

async function carregarMicrochips() {
    try {
        const resposta = await fetch(`${API_URL}/microchips`);
        if (!resposta.ok) {
            throw new Error("Erro ao listar microchips.");
        }

        const microchips = await resposta.json();
        listaMicrochipsCache = microchips;

        const tbody = document.getElementById("lista-microchips");
        tbody.innerHTML = "";

        if (!microchips.length) {
            tbody.innerHTML = '<tr><td colspan="5">Nenhum microchip cadastrado.</td></tr>';
            return;
        }

        microchips.forEach((m) => {
            const id = m.microchip_id ?? m.id;
            const animalObj = mapaAnimais[m.animal_id];
            const nomeAnimal = m.animal_nome || (animalObj ? `${animalObj.nome} (ID: ${m.animal_id})` : `Animal ID: ${m.animal_id}`);

            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${id}</td>
                <td>${nomeAnimal}</td>
                <td><strong>${m.codigo}</strong></td>
                <td>${m.data_implantacao || "-"}</td>
                <td>${m.observacoes || "-"}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (erro) {
        console.error(erro);
    }
}

async function cadastrarMicrochip(event) {
    event.preventDefault();

    const payload = {
        animal_id: Number(document.getElementById("animal_id").value),
        codigo: document.getElementById("codigo").value.trim(),
        data_implantacao: document.getElementById("data_implantacao").value || null,
        observacoes: document.getElementById("observacoes").value.trim() || null
    };

    try {
        const resposta = await fetch(`${API_URL}/microchips`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const dados = await resposta.json().catch(() => ({}));

        if (!resposta.ok) {
            alert(dados.detail || "Não foi possível cadastrar o microchip.");
            return;
        }

        alert("Microchip cadastrado com sucesso!");
        document.getElementById("form-microchip").reset();
        await carregarMicrochips();
    } catch (erro) {
        console.error(erro);
        alert("Erro de comunicação com o servidor.");
    }
}

async function buscarPorCodigo(event) {
    event.preventDefault();

    const codigo = document.getElementById("busca_codigo").value.trim();
    const box = document.getElementById("resultado-busca-microchip");
    if (!codigo) return;

    box.hidden = false;
    box.className = "resultado-busca";
    box.textContent = "Buscando microchip...";

    try {
        let encontrado = null;

        // Tenta o endpoint dedicado por código no backend
        const resDireta = await fetch(`${API_URL}/microchips/codigo/${encodeURIComponent(codigo)}`);
        if (resDireta.ok) {
            encontrado = await resDireta.json();
        } else {
            // Fallback na lista carregada caso o endpoint use outra assinatura
            if (!listaMicrochipsCache.length) {
                await carregarMicrochips();
            }
            encontrado = listaMicrochipsCache.find(
                (m) => String(m.codigo).toLowerCase() === codigo.toLowerCase()
            );
        }

        if (!encontrado) {
            box.className = "resultado-busca erro";
            box.innerHTML = `Nenhum animal encontrado para o microchip <strong>${codigo}</strong>.`;
            return;
        }

        const animal = encontrado.animal || mapaAnimais[encontrado.animal_id] || {};
        const nomeAnimal = encontrado.animal_nome || animal.nome || `Animal ID: ${encontrado.animal_id}`;
        const especie = animal.especie ? ` | <strong>Espécie:</strong> ${animal.especie}` : "";
        const raca = animal.raca ? ` | <strong>Raça:</strong> ${animal.raca}` : "";
        const tutor = encontrado.tutor_nome || animal.tutor_nome
            ? `<br><strong>Tutor:</strong> ${encontrado.tutor_nome || animal.tutor_nome}`
            : "";

        box.className = "resultado-busca";
        box.innerHTML = `
            <strong>Microchip Localizado:</strong> ${encontrado.codigo}<br>
            <strong>Animal:</strong> ${nomeAnimal} (ID: ${encontrado.animal_id})${especie}${raca}${tutor}<br>
            <strong>Data de Implantação:</strong> ${encontrado.data_implantacao || "Não informada"} |
            <strong>Observações:</strong> ${encontrado.observacoes || "Nenhuma"}
        `;
    } catch (erro) {
        console.error(erro);
        box.className = "resultado-busca erro";
        box.textContent = "Erro ao consultar o código do microchip.";
    }
}

function limparBusca() {
    document.getElementById("busca_codigo").value = "";
    const box = document.getElementById("resultado-busca-microchip");
    box.hidden = true;
    box.innerHTML = "";
}