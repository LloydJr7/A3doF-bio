


const API_URL = "http://127.0.0.1:8000";

async function carregarAnimais() {
    try {
        const resposta = await fetch(`${API_URL}/animais`);

        if (!resposta.ok) {
            throw new Error("Não foi possível buscar os animais.");
        }

        const animais = await resposta.json();

        console.log("Animais cadastrados:", animais);

        const tabela = document.getElementById("lista-animais");

        tabela.innerHTML = "";

        animais.forEach((animal) => {
            const linha = document.createElement("tr");

            const valores = [
                animal.id,
                animal.nome,
                animal.especie,
                animal.raca,
                animal.tutor,
                animal.sexo,
                animal.cor,
                animal.peso_atual
            ];

            valores.forEach((valor) => {
                const celula = document.createElement("td");
                celula.textContent = valor ?? "-";
                linha.appendChild(celula);
            });

            const acoes = document.createElement("td");
            acoes.textContent = "Em breve";
            linha.appendChild(acoes);

            tabela.appendChild(linha);
        });

    } catch (erro) {
        console.error("Erro ao carregar animais:", erro);
    }
}

document.addEventListener("DOMContentLoaded", carregarAnimais);


async function cadastrarAnimal(evento) {
    evento.preventDefault();

    const nome = document.getElementById("nome").value.trim();
    const especie = document.getElementById("especie").value;
    const raca = document.getElementById("raca").value;
    const tutor = document.getElementById("tutor").value;
    const sexo = document.getElementById("sexo").value;
    const cor = document.getElementById("cor").value.trim();
    const peso = document.getElementById("peso").value;

    const animal = {
        nome: nome,
        especie_id: Number(especie),
        raca_id: raca ? Number(raca) : null,
        tutor_id: tutor ? Number(tutor) : null,
        sexo: sexo || null,
        cor: cor || null,
        peso_atual: peso ? Number(peso) : null
    };

    try {
        const resposta = await fetch(`${API_URL}/animais`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(animal)
        });

        if (!resposta.ok) {
            const erro = await resposta.json();
            throw new Error(JSON.stringify(erro));
        }

        const resultado = await resposta.json();

        alert(`Animal cadastrado com sucesso! ID: ${resultado.id}`);

        document.getElementById("form-animal").reset();

        await carregarAnimais();

    } catch (erro) {
        console.error("Erro ao cadastrar animal:", erro);
        alert("Não foi possível cadastrar o animal. Verifique os dados.");
    }
}

document.getElementById("form-animal").addEventListener("submit", cadastrarAnimal);
