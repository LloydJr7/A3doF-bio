const API_URL = "http://127.0.0.1:8000";


async function carregarAnimais() {
    const seletor = document.getElementById("animal_id");

    try {
        const resposta = await fetch(`${API_URL}/animais`);

        if (!resposta.ok) {
            throw new Error("Erro ao buscar animais");
        }

        const animais = await resposta.json();

        seletor.innerHTML = '<option value="">Selecione um animal...</option>';

        animais.forEach(animal => {
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


async function editarConsulta(consulta) {
    const novoMotivo = prompt(
        "Novo motivo da consulta:",
        consulta.motivo ?? ""
    );

    if (novoMotivo === null) return;

    if (!novoMotivo.trim()) {
        alert("O motivo da consulta não pode ficar vazio.");
        return;
    }

    const novasObservacoes = prompt(
        "Novas observações:",
        consulta.observacoes ?? ""
    );

    if (novasObservacoes === null) return;

    const dadosAtualizados = {
        motivo: novoMotivo.trim(),
        observacoes: novasObservacoes.trim()
    };

    try {
        const resposta = await fetch(
            `${API_URL}/consultas/${consulta.id}`,
            {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(dadosAtualizados)
            }
        );

        const resultado = await resposta.json();

        if (!resposta.ok) {
            alert(
                "Erro ao editar consulta: " +
                JSON.stringify(resultado.detail ?? resultado)
            );
            return;
        }

        alert("Consulta atualizada com sucesso!");
        await carregarConsultas();

    } catch (erro) {
        console.error("Erro ao editar consulta:", erro);
        alert("Não foi possível conectar ao servidor.");
    }
}


async function cancelarConsulta(consulta) {
    const confirmar = confirm(
        `Deseja realmente cancelar a consulta de ID ${consulta.id}?`
    );

    if (!confirmar) return;

    try {
        const resposta = await fetch(
            `${API_URL}/consultas/${consulta.id}`,
            {
                method: "DELETE"
            }
        );

        if (!resposta.ok) {
            const resultado = await resposta.json();

            alert(
                "Erro ao cancelar consulta: " +
                JSON.stringify(resultado.detail ?? resultado)
            );
            return;
        }

        alert("Consulta cancelada com sucesso!");
        await carregarConsultas();

    } catch (erro) {
        console.error("Erro ao cancelar consulta:", erro);
        alert("Não foi possível conectar ao servidor.");
    }
}


async function carregarConsultas() {
    const tabela = document.getElementById("lista-consultas");

    try {
        const resposta = await fetch(`${API_URL}/consultas`);

        if (!resposta.ok) {
            throw new Error("Erro ao buscar consultas");
        }

        const consultas = await resposta.json();

        tabela.innerHTML = "";

        if (consultas.length === 0) {
            const linha = document.createElement("tr");
            const coluna = document.createElement("td");

            coluna.colSpan = 7;
            coluna.textContent = "Nenhuma consulta cadastrada.";

            linha.appendChild(coluna);
            tabela.appendChild(linha);
            return;
        }

        consultas.forEach(consulta => {
            const linha = document.createElement("tr");

            const dataFormatada = consulta.data_hora
                ? new Date(consulta.data_hora).toLocaleString("pt-BR")
                : "-";

            const valores = [
                consulta.id,
                consulta.animal,
                consulta.veterinario_id,
                dataFormatada,
                consulta.motivo,
                consulta.status
            ];

            valores.forEach(valor => {
                const coluna = document.createElement("td");
                coluna.textContent = valor ?? "-";
                linha.appendChild(coluna);
            });

            const colunaAcoes = document.createElement("td");
            colunaAcoes.className = "acoes-consulta";

            if (consulta.status === "agendada") {
                const botaoEditar = document.createElement("button");
                botaoEditar.type = "button";
                botaoEditar.textContent = "Editar";
                botaoEditar.className = "btn-editar";

                botaoEditar.addEventListener("click", () => {
                    editarConsulta(consulta);
                });

                const botaoCancelar = document.createElement("button");
                botaoCancelar.type = "button";
                botaoCancelar.textContent = "Cancelar";
                botaoCancelar.className = "btn-cancelar";

                botaoCancelar.addEventListener("click", () => {
                    cancelarConsulta(consulta);
                });

                colunaAcoes.appendChild(botaoEditar);
                colunaAcoes.appendChild(botaoCancelar);

            } else {
                colunaAcoes.textContent = "-";
            }

            linha.appendChild(colunaAcoes);
            tabela.appendChild(linha);
        });

        console.log("Consultas carregadas:", consultas);

    } catch (erro) {
        console.error("Erro ao carregar consultas:", erro);
        alert("Não foi possível carregar as consultas.");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    carregarAnimais();
    carregarConsultas();

    document
        .getElementById("btn-atualizar")
        .addEventListener("click", carregarConsultas);

    const formularioConsulta = document.getElementById("form-consulta");

    formularioConsulta.addEventListener("submit", async (evento) => {
        evento.preventDefault();

        const animalId = Number(
            document.getElementById("animal_id").value
        );

        const veterinarioId = Number(
            document.getElementById("veterinario_id").value
        );

        const dataHora = document.getElementById("data_hora").value;

        const motivo = document
            .getElementById("motivo")
            .value.trim();

        const observacoes = document
            .getElementById("observacoes")
            .value.trim();

        const novaConsulta = {
            animal_id: animalId,
            veterinario_id: veterinarioId,
            data_hora: dataHora,
            motivo: motivo,
            observacoes: observacoes || null
        };

        try {
            const resposta = await fetch(`${API_URL}/consultas`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(novaConsulta)
            });

            const resultado = await resposta.json();

            if (!resposta.ok) {
                alert(
                    "Erro ao agendar consulta: " +
                    JSON.stringify(resultado.detail ?? resultado)
                );
                return;
            }

            alert("Consulta agendada com sucesso!");

            formularioConsulta.reset();
            await carregarConsultas();

        } catch (erro) {
            console.error("Erro ao agendar consulta:", erro);
            alert("Não foi possível conectar ao servidor.");
        }
    });
});