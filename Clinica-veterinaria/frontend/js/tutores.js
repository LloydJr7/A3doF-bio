const API_URL = "http://127.0.0.1:8000";

function exibirAlerta(mensagem, tipo) {
    const alerta = document.getElementById("mensagem-alerta");
    alerta.textContent = mensagem;
    alerta.className = `alerta ${tipo}`;
    alerta.style.display = "block";
    setTimeout(() => {
        alerta.style.display = "none";
    }, 5000);
}

async function buscarCep() {
    const cepInput = document.getElementById("cep").value.replace(/\D/g, "");
    if (cepInput.length !== 8) {
        exibirAlerta("Informe um CEP válido com 8 dígitos.", "erro");
        return;
    }

    try {
        const resposta = await fetch(`${API_URL}/cep/${cepInput}`);
        const dados = await resposta.json();

        if (!resposta.ok) {
            exibirAlerta(dados.detail || "CEP não encontrado.", "erro");
            return;
        }

        document.getElementById("endereco-id").value = dados.endereco_id;
        document.getElementById("logradouro").value = dados.dados.logradouro || "";
        document.getElementById("bairro").value = dados.dados.bairro || "";
        document.getElementById("cidade").value = dados.dados.localidade || "";
        document.getElementById("uf").value = dados.dados.uf || "";
        exibirAlerta(dados.mensagem, "sucesso");
    } catch (erro) {
        exibirAlerta("Erro ao consultar CEP na API.", "erro");
    }
}

async function salvarComplementoEndereco(enderecoId) {
    const payloadEndereco = {
        logradouro: document.getElementById("logradouro").value,
        bairro: document.getElementById("bairro").value,
        cidade: document.getElementById("cidade").value,
        uf: document.getElementById("uf").value
    };

    const resposta = await fetch(`${API_URL}/enderecos/${enderecoId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payloadEndereco)
    });

    if (!resposta.ok) {
        const dados = await resposta.json();
        throw new Error(dados.detail || "Erro ao salvar dados complementares do endereço.");
    }
}

document.getElementById("btn-buscar-cep").addEventListener("click", buscarCep);
document.getElementById("cep").addEventListener("blur", () => {
    if (document.getElementById("cep").value.replace(/\D/g, "").length === 8) {
        buscarCep();
    }
});

async function carregarTutores() {
    try {
        const resposta = await fetch(`${API_URL}/tutores`);
        const tutores = await resposta.json();

        const tbody = document.getElementById("lista-tutores");
        tbody.innerHTML = "";

        tutores.forEach((tutor) => {
            const tr = document.createElement("tr");
            const classeStatus = tutor.situacao === "ATIVO" ? "status-ativo" : "status-inativo";

            tr.innerHTML = `
                <td>${tutor.id}</td>
                <td>${tutor.nome_completo}</td>
                <td>${tutor.cpf}</td>
                <td>${tutor.email}</td>
                <td>${tutor.telefone}</td>
                <td>${tutor.endereco_id}</td>
                <td class="${classeStatus}">${tutor.situacao}</td>
                <td>
                    <button type="button" class="btn-editar" onclick="prepararEdicao(${tutor.id})">Editar</button>
                    ${tutor.situacao === "ATIVO"
                        ? `<button type="button" class="btn-inativar" onclick="inativarTutor(${tutor.id})">Inativar</button>`
                        : `<button type="button" class="btn-ativar" onclick="ativarTutor(${tutor.id})">Ativar</button>`}
                    <button type="button" class="btn-excluir" onclick="excluirTutor(${tutor.id})">Excluir</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (erro) {
        exibirAlerta("Erro ao carregar lista de tutores.", "erro");
    }
}

document.getElementById("form-tutor").addEventListener("submit", async (e) => {
    e.preventDefault();

    const idEdicao = document.getElementById("tutor-id-edicao").value;
    const enderecoId = parseInt(document.getElementById("endereco-id").value, 10);

    if (!enderecoId) {
        exibirAlerta("Busque um CEP válido antes de salvar o tutor.", "erro");
        return;
    }

    try {
        await salvarComplementoEndereco(enderecoId);
    } catch (erro) {
        exibirAlerta(erro.message, "erro");
        return;
    }

    if (idEdicao) {
        const payloadUpdate = {
            nome_completo: document.getElementById("nome").value,
            data_nascimento: document.getElementById("data-nascimento").value,
            email: document.getElementById("email").value,
            telefone: document.getElementById("telefone").value,
            endereco_id: enderecoId
        };

        try {
            const resposta = await fetch(`${API_URL}/tutores/${idEdicao}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payloadUpdate)
            });

            const dados = await resposta.json();
            if (!resposta.ok) {
                exibirAlerta(dados.detail || "Erro ao atualizar tutor.", "erro");
                return;
            }

            exibirAlerta(dados.mensagem, "sucesso");
            cancelarEdicao();
            carregarTutores();
        } catch (erro) {
            exibirAlerta("Erro de conexão ao atualizar tutor.", "erro");
        }
    } else {
        const payloadCreate = {
            nome_completo: document.getElementById("nome").value,
            cpf: document.getElementById("cpf").value,
            data_nascimento: document.getElementById("data-nascimento").value,
            email: document.getElementById("email").value,
            telefone: document.getElementById("telefone").value,
            endereco_id: enderecoId
        };

        try {
            const resposta = await fetch(`${API_URL}/tutores`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payloadCreate)
            });

            const dados = await resposta.json();
            if (!resposta.ok) {
                exibirAlerta(dados.detail || "Erro ao cadastrar tutor.", "erro");
                return;
            }

            exibirAlerta(dados.mensagem, "sucesso");
            document.getElementById("form-tutor").reset();
            document.getElementById("endereco-id").value = "";
            carregarTutores();
        } catch (erro) {
            exibirAlerta("Erro de conexão ao cadastrar tutor.", "erro");
        }
    }
});

async function prepararEdicao(id) {
    try {
        const resposta = await fetch(`${API_URL}/tutores/${id}`);
        const tutor = await resposta.json();

        document.getElementById("tutor-id-edicao").value = tutor.id;
        document.getElementById("nome").value = tutor.nome_completo;
        document.getElementById("cpf").value = tutor.cpf;
        document.getElementById("cpf").disabled = true;
        document.getElementById("data-nascimento").value = tutor.data_nascimento;
        document.getElementById("email").value = tutor.email;
        document.getElementById("telefone").value = tutor.telefone;
        document.getElementById("endereco-id").value = tutor.endereco_id;
        document.getElementById("cep").required = false;

        if (tutor.endereco_id) {
            const respEnd = await fetch(`${API_URL}/enderecos/${tutor.endereco_id}`);
            if (respEnd.ok) {
                const end = await respEnd.json();
                document.getElementById("cep").value = end.cep || "";
                document.getElementById("logradouro").value = end.logradouro || "";
                document.getElementById("bairro").value = end.bairro || "";
                document.getElementById("cidade").value = end.cidade || "";
                document.getElementById("uf").value = end.uf || "";
            }
        }

        document.getElementById("titulo-form").textContent = `Editar Tutor #${tutor.id}`;
        document.getElementById("btn-salvar").textContent = "Salvar Alterações";
        document.getElementById("btn-cancelar-edicao").style.display = "inline-block";
        window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (erro) {
        exibirAlerta("Erro ao carregar dados do tutor para edição.", "erro");
    }
}

function cancelarEdicao() {
    document.getElementById("form-tutor").reset();
    document.getElementById("tutor-id-edicao").value = "";
    document.getElementById("endereco-id").value = "";
    document.getElementById("cpf").disabled = false;
    document.getElementById("cep").required = true;
    document.getElementById("titulo-form").textContent = "Cadastrar Tutor";
    document.getElementById("btn-salvar").textContent = "Cadastrar Tutor";
    document.getElementById("btn-cancelar-edicao").style.display = "none";
}

document.getElementById("btn-cancelar-edicao").addEventListener("click", cancelarEdicao);
document.getElementById("btn-atualizar").addEventListener("click", carregarTutores);

async function inativarTutor(id) {
    try {
        const resposta = await fetch(`${API_URL}/tutores/${id}/inativar`, {
            method: "PATCH"
        });
        const dados = await resposta.json();

        if (!resposta.ok) {
            exibirAlerta(dados.detail || "Erro ao inativar tutor.", "erro");
            return;
        }

        exibirAlerta(dados.mensagem, "sucesso");
        carregarTutores();
    } catch (erro) {
        exibirAlerta("Erro de conexão ao inativar tutor.", "erro");
    }
}

async function ativarTutor(id) {
    try {
        const resposta = await fetch(`${API_URL}/tutores/${id}/ativar`, {
            method: "PATCH"
        });
        const dados = await resposta.json();

        if (!resposta.ok) {
            exibirAlerta(dados.detail || "Erro ao reativar tutor.", "erro");
            return;
        }

        exibirAlerta(dados.mensagem, "sucesso");
        carregarTutores();
    } catch (erro) {
        exibirAlerta("Erro de conexão ao reativar tutor.", "erro");
    }
}

async function excluirTutor(id) {
    if (!confirm("Tem certeza que deseja excluir permanentemente este tutor?")) return;

    try {
        const resposta = await fetch(`${API_URL}/tutores/${id}`, {
            method: "DELETE"
        });
        const dados = await resposta.json();

        if (!resposta.ok) {
            exibirAlerta(dados.detail || "Erro ao excluir tutor.", "erro");
            return;
        }

        exibirAlerta(dados.mensagem, "sucesso");
        carregarTutores();
    } catch (erro) {
        exibirAlerta("Erro de conexão ao excluir tutor.", "erro");
    }
}

document.addEventListener("DOMContentLoaded", carregarTutores);