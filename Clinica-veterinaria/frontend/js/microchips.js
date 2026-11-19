
const API_URL = "http://127.0.0.1:8000";

async function carregarAnimaisSelect() {
    const select = document.getElementById("animal_id");

    try {
        const resposta = await fetch(`${API_URL}/animais`);

        if (!resposta.ok) {
            throw new Error("Erro ao buscar animais");
        }

        const animais = await resposta.json();

        select.innerHTML = '<option value="">Selecione um animal...</option>';

        animais.forEach(animal => {
            const opcao = document.createElement("option");

            opcao.value = animal.id;
            opcao.textContent = `${animal.nome} (ID: ${animal.id})`;

            select.appendChild(opcao);
        });

    } catch (erro) {
        console.error("Erro ao carregar animais:", erro);
        alert("Não foi possível carregar a lista de animais.");
    }
}

async function carregarMicrochips() {
    const tabela = document.getElementById("lista-microchips");

    try {
        const resposta = await fetch(`${API_URL}/microchips`);

        if (!resposta.ok) {
            throw new Error("Erro ao buscar microchips");
        }

        
        const microchips = await resposta.json();


        const respostaAnimais = await fetch(`${API_URL}/animais`);

        if (!respostaAnimais.ok) {
            throw new Error("Erro ao buscar animais");
}

const animais = await respostaAnimais.json();

tabela.innerHTML = "";
    

        microchips.forEach(microchip => {
            const linha = document.createElement("tr");

            const animal = animais.find(
                a => a.id === microchip.animal_id
);

const nomeAnimal = animal
    ? `${animal.nome} (ID: ${animal.id})`
    : `Animal ID: ${microchip.animal_id}`;

const valores = [
    microchip.id,
    nomeAnimal,
    microchip.codigo,
    microchip.data_implantacao,
    microchip.observacoes
];

            valores.forEach(valor => {
                const coluna = document.createElement("td");
                coluna.textContent = valor ?? "-";
                linha.appendChild(coluna);
            });

            tabela.appendChild(linha);
        });

        console.log("Microchips carregados:", microchips);

    } catch (erro) {
        console.error("Erro ao carregar microchips:", erro);
        alert("Não foi possível carregar os microchips.");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    carregarMicrochips();
    carregarAnimaisSelect();

    document
        .getElementById("btn-atualizar")
        .addEventListener("click", carregarMicrochips);
});


const formularioMicrochip = document.getElementById("form-microchip");

formularioMicrochip.addEventListener("submit", async (evento) => {
    evento.preventDefault();

    const animalId = Number(document.getElementById("animal_id").value);
    const codigo = document.getElementById("codigo").value.trim();
    const data = document.getElementById("data_implantacao").value;
    const observacoes = document.getElementById("observacoes").value.trim();

    const novoMicrochip = {
        animal_id: animalId,
        codigo: codigo,
        data_implantacao: data || null,
        observacoes: observacoes || null
    };

    try {
        const resposta = await fetch(`${API_URL}/microchips`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(novoMicrochip)
        });

        const resultado = await resposta.json();

        if (!resposta.ok) {
            alert("Erro ao cadastrar microchip: " + JSON.stringify(resultado.detail));
            return;
        }

        alert("Microchip cadastrado com sucesso!");

        formularioMicrochip.reset();
        carregarMicrochips();

    } catch (erro) {
        console.error("Erro ao cadastrar microchip:", erro);
        alert("Não foi possível conectar ao servidor.");
    }
});
