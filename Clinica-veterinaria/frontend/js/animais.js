


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

const botaoDesativar = document.createElement("button");
botaoDesativar.textContent = "Desativar";

botaoDesativar.addEventListener("click", async () => {
    const confirmar = confirm(
        `Deseja realmente desativar o animal ${animal.nome}?`
    );

    if (!confirmar) {
        return;
    }

    try {
        const resposta = await fetch(`${API_URL}/animais/${animal.id}`, {
            method: "DELETE"
        });

        if (!resposta.ok) {
            throw new Error("Não foi possível desativar o animal.");
        }

        alert("Animal desativado com sucesso!");
        await carregarAnimais();

    } catch (erro) {
        console.error("Erro ao desativar animal:", erro);
        alert("Erro ao desativar o animal.");
    }
});
const botaoEditar = document.createElement("button");
botaoEditar.textContent = "Editar";

botaoEditar.addEventListener("click", async () => {
    const novaCor = prompt(
        `Digite a nova cor de ${animal.nome}:`,
        animal.cor ?? ""
    );

    if (novaCor === null) {
        return;
    }

    if (!novaCor.trim()) {
        alert("A cor não pode ficar vazia.");
        return;
    }

    try {
        const resposta = await fetch(`${API_URL}/animais/${animal.id}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                cor: novaCor.trim()
            })
        });

        if (!resposta.ok) {
            throw new Error("Não foi possível atualizar o animal.");
        }

        alert("Animal atualizado com sucesso!");
        await carregarAnimais();

    } catch (erro) {
        console.error("Erro ao editar animal:", erro);
        alert("Erro ao atualizar o animal.");
    }
});

acoes.appendChild(botaoEditar);
acoes.appendChild(botaoDesativar);
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


const racasPorEspecie = {
    1: [
        { id: 1, nome: "Labrador" },
        { id: 2, nome: "Golden Retriever" },
        { id: 3, nome: "Poodle" },
        { id: 4, nome: "Vira-lata" }
    ],
    2: [
        { id: 5, nome: "Siamês" },
        { id: 6, nome: "Persa" },
        { id: 7, nome: "Maine Coon" },
        { id: 8, nome: "Vira-lata" }
    ]
};

const campoEspecie = document.getElementById("especie");
const campoRaca = document.getElementById("raca");

campoEspecie.addEventListener("change", () => {
    const especieId = campoEspecie.value;

    campoRaca.innerHTML =
        '<option value="">Selecione uma raça</option>';

    const racas = racasPorEspecie[especieId] || [];

    racas.forEach((raca) => {
        const opcao = document.createElement("option");

        opcao.value = raca.id;
        opcao.textContent = raca.nome;

        campoRaca.appendChild(opcao);
    });
});


const formularioAnimal = document.getElementById("form-animal");

formularioAnimal.addEventListener("submit", async (evento) => {
    evento.preventDefault();

    const animal = {
        nome: document.getElementById("nome").value.trim(),
        especie_id: Number(document.getElementById("especie").value),
        raca_id: Number(document.getElementById("raca").value),
        tutor_id: document.getElementById("tutor").value
            ? Number(document.getElementById("tutor").value)
            : null,
        sexo: document.getElementById("sexo").value || null,
        cor: document.getElementById("cor").value.trim() || null,
        peso_atual: document.getElementById("peso").value
            ? Number(document.getElementById("peso").value)
            : null
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
            throw new Error(JSON.stringify(erro.detail || erro));
        }

        const resultado = await resposta.json();

        alert("Animal cadastrado com sucesso!");

        console.log("Resultado do cadastro:", resultado);

        formularioAnimal.reset();

        await carregarAnimais();

    } catch (erro) {
        console.error("Erro ao cadastrar animal:", erro);
        alert("Erro ao cadastrar animal. Verifique o console.");
    }
});

