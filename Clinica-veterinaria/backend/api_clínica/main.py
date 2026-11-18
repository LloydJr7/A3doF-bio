from datetime import date, datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from database import engine
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="Sistema de Clinica Veterinaria",
    description="API para gerenciamento de animais, microchips e consultas",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["null"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def inicio():
    return {
        "mensagem": "API da Clinica Veterinaria funcionando"
    }


class AnimalCadastro(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    especie_id: int = Field(gt=0)
    raca_id: int | None = Field(default=None, gt=0)
    tutor_id: int | None = Field(default=None, gt=0)
    sexo: str | None = None
    cor: str | None = None
    peso_atual: float | None = Field(default=None, gt=0)


@app.post("/animais", status_code=201)
def cadastrar_animal(animal: AnimalCadastro):
    with engine.begin() as conexao:
        resultado = conexao.execute(
            text("""
                INSERT INTO animais
                    (
                        nome,
                        especie_id,
                        raca_id,
                        tutor_id,
                        sexo,
                        cor,
                        peso_atual
                    )
                VALUES
                    (
                        :nome,
                        :especie_id,
                        :raca_id,
                        :tutor_id,
                        :sexo,
                        :cor,
                        :peso_atual
                    )
                RETURNING id
            """),
            animal.model_dump()
        )

        animal_id = resultado.scalar_one()

    return {
        "mensagem": "Animal cadastrado com sucesso!",
        "id": animal_id
    }
@app.get("/animais")
def listar_animais():
    with engine.connect() as conexao:
        resultado = conexao.execute(
            text("""
                SELECT
                a.id,
                a.nome,
                e.nome AS especie,
                r.nome AS raca,
                a.tutor_id,
                t.nome_completo AS tutor,
                a.sexo,
                a.cor,
                a.peso_atual
                FROM animais a
                JOIN especies e
                ON a.especie_id = e.id
                LEFT JOIN racas r
                ON a.raca_id = r.id
                LEFT JOIN tutor t
                ON a.tutor_id = t.id
                WHERE a.ativo = TRUE
                ORDER BY a.id
            """)
        )

        animais = resultado.mappings().all()

    return [dict(animal) for animal in animais]



@app.get("/animais/{animal_id}")
def buscar_animal(animal_id: int):
    with engine.connect() as conexao:
        resultado = conexao.execute(
            text("""
                SELECT
                    a.id,
                    a.nome,
                    e.nome AS especie,
                    r.nome AS raca,
                    a.sexo,
                    a.cor,
                    a.peso_atual
                FROM animais a
                JOIN especies e
                    ON a.especie_id = e.id
                LEFT JOIN racas r
                    ON a.raca_id = r.id
                WHERE a.id = :animal_id
                  AND a.ativo = TRUE
            """),
            {"animal_id": animal_id}
        )

        animal = resultado.mappings().first()
        

    if animal is None:
        raise HTTPException(
            status_code=404,
            detail="Animal não encontrado"
        )

    return dict(animal)


class AnimalAtualizacao(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=100)
    sexo: str | None = None
    cor: str | None = None
    peso_atual: float | None = Field(default=None, gt=0)


@app.put("/animais/{animal_id}")
def atualizar_animal(animal_id: int, animal: AnimalAtualizacao):
    dados = animal.model_dump(exclude_unset=True)

    if not dados:
        raise HTTPException(
            status_code=400,
            detail="Informe pelo menos um campo para atualizar"
        )

    if any(valor is None for valor in dados.values()):
        raise HTTPException(
            status_code=400,
            detail="Os campos enviados não podem ser nulos"
        )

    campos = ", ".join(
        f"{campo} = :{campo}" for campo in dados
    )

    dados["animal_id"] = animal_id

    with engine.begin() as conexao:
        resultado = conexao.execute(
            text(f"""
                UPDATE animais
                SET {campos}
                WHERE id = :animal_id
                  AND ativo = TRUE
                RETURNING id
            """),
            dados
        )
        id_atualizado = resultado.scalar_one_or_none()

    if id_atualizado is None:
        raise HTTPException(status_code=404, detail="Animal não encontrado ou desativado")

    return {
        "mensagem": "Animal atualizado com sucesso!",
        "id": id_atualizado
    }


@app.delete("/animais/{animal_id}")
def desativar_animal(animal_id: int):
    with engine.begin() as conexao:
        resultado = conexao.execute(
            text("""
                UPDATE animais
                SET ativo = FALSE
                WHERE id = :animal_id
                  AND ativo = TRUE
                RETURNING id
            """),
            {"animal_id": animal_id}
        )

        id_desativado = resultado.scalar_one_or_none()

    if id_desativado is None:
        raise HTTPException(
            status_code=404,
            detail="Animal não encontrado ou já desativado"
        )

    return {
        "mensagem": "Animal desativado com sucesso!",
        "id": id_desativado
    }


class MicrochipCadastro(BaseModel):
    animal_id: int = Field(gt=0)
    codigo: str = Field(min_length=1, max_length=50)
    data_implantacao: date | None = None
    observacoes: str | None = None


@app.post("/microchips", status_code=201)
def cadastrar_microchip(microchip: MicrochipCadastro):
    with engine.begin() as conexao:
        animal = conexao.execute(
            text("""
                SELECT id
                FROM animais
                WHERE id = :animal_id AND ativo = TRUE
            """),
            {"animal_id": microchip.animal_id}
        ).first()

        if animal is None:
            raise HTTPException(
                status_code=404,
                detail="Animal não encontrado ou desativado"
            )

        existente = conexao.execute(
            text("""
                SELECT id
                FROM microchips
                WHERE animal_id = :animal_id
                   OR codigo = :codigo
            """),
            {
                "animal_id": microchip.animal_id,
                "codigo": microchip.codigo
            }
        ).first()

        if existente is not None:
            raise HTTPException(
                status_code=409,
                detail="Animal ou código já possui microchip cadastrado"
            )

        resultado = conexao.execute(
            text("""
                INSERT INTO microchips
                    (animal_id, codigo, data_implantacao, observacoes)
                VALUES
                    (:animal_id, :codigo, :data_implantacao, :observacoes)
                RETURNING id
            """),
            microchip.model_dump()
        )

        microchip_id = resultado.scalar_one()

    return {
        "mensagem": "Microchip cadastrado com sucesso!",
        "id": microchip_id
    }


@app.get("/microchips")
def listar_microchips():
    with engine.connect() as conexao:
        resultado = conexao.execute(
            text("""
                SELECT m.id, m.animal_id, a.nome AS animal,
                       m.codigo, m.data_implantacao, m.observacoes, m.ativo
                FROM microchips m
                JOIN animais a ON m.animal_id = a.id
                ORDER BY m.id
            """)
        )
        microchips = resultado.mappings().all()
    return [dict(microchip) for microchip in microchips]


@app.get("/microchips/codigo/{codigo}")
def buscar_microchip_por_codigo(codigo: str):
    with engine.connect() as conexao:
        resultado = conexao.execute(
            text("""
                SELECT m.id AS microchip_id, m.codigo,
                       m.data_implantacao, m.observacoes,
                       a.id AS animal_id, a.nome AS animal,
                       e.nome AS especie, r.nome AS raca,
                       a.sexo, a.cor, a.peso_atual
                FROM microchips m
                JOIN animais a ON m.animal_id = a.id
                JOIN especies e ON a.especie_id = e.id
                LEFT JOIN racas r ON a.raca_id = r.id
                WHERE m.codigo = :codigo
                  AND m.ativo = TRUE AND a.ativo = TRUE
            """),
            {"codigo": codigo}
        )
        microchip = resultado.mappings().first()

    if microchip is None:
        raise HTTPException(status_code=404, detail="Microchip não encontrado ou inativo")
    return dict(microchip)


class ConsultaCadastro(BaseModel):
    animal_id: int = Field(gt=0)
    veterinario_id: int | None = Field(default=None, gt=0)
    data_hora: datetime
    motivo: str | None = None
    observacoes: str | None = None


@app.post("/consultas", status_code=201)
def cadastrar_consulta(consulta: ConsultaCadastro):
    with engine.begin() as conexao:

       
        animal = conexao.execute(
            text("""
                SELECT id
                FROM animais
                WHERE id = :animal_id
                  AND ativo = TRUE
            """),
            {"animal_id": consulta.animal_id}
        ).first()

        if animal is None:
            raise HTTPException(
                status_code=404,
                detail="Animal não encontrado ou desativado"
            )

        
        resultado = conexao.execute(
            text("""
                INSERT INTO consultas
                    (
                        animal_id,
                        veterinario_id,
                        data_hora,
                        motivo,
                        observacoes
                    )
                     VALUES
                    (
                        :animal_id,
                        :veterinario_id,
                        :data_hora,
                        :motivo,
                        :observacoes
                    )
                RETURNING id
            """),
            consulta.model_dump()
        )

        consulta_id = resultado.scalar_one()

    return {
        "mensagem": "Consulta cadastrada com sucesso!",
        "id": consulta_id
    }

@app.get("/consultas")
def listar_consultas():
    with engine.connect() as conexao:
        resultado = conexao.execute(
            text("""
                SELECT
                    c.id,
                    a.nome AS animal,
                    c.veterinario_id,
                    c.data_hora,
                    c.motivo,
                    c.status,
                    c.observacoes
                FROM consultas c
                JOIN animais a
                    ON c.animal_id = a.id
                WHERE c.ativo = TRUE
                ORDER BY c.data_hora
            """)
        )

        consultas = resultado.mappings().all()

    return [dict(consulta) for consulta in consultas]

@app.get("/consultas/{consulta_id}")
def buscar_consulta(consulta_id: int):
    with engine.connect() as conexao:
        resultado = conexao.execute(
            text("""
                SELECT
                    c.id,
                    c.animal_id,
                    a.nome AS animal,
                    c.veterinario_id,
                    c.data_hora,
                    c.motivo,
                    c.status,
                    c.observacoes
                FROM consultas c
                JOIN animais a
                    ON c.animal_id = a.id
                WHERE c.id = :consulta_id
                  AND c.ativo = TRUE
            """),
            {"consulta_id": consulta_id}
        )

        consulta = resultado.mappings().first()

    if consulta is None:
        raise HTTPException(
            status_code=404,
            detail="Consulta não encontrada"
        )

    return dict(consulta)

class ConsultaAtualizacao(BaseModel):
    data_hora: datetime | None = None
    motivo: str | None = None
    status: str | None = None
    observacoes: str | None = None


@app.put("/consultas/{consulta_id}")
def atualizar_consulta(consulta_id: int, consulta: ConsultaAtualizacao):
    dados = consulta.model_dump(exclude_unset=True)

    if not dados:
        raise HTTPException(
            status_code=400,
            detail="Informe pelo menos um campo para atualizar"
        )

    if any(valor is None for valor in dados.values()):
        raise HTTPException(
            status_code=400,
            detail="Os campos enviados não podem ser nulos"
        )

    if "status" in dados and dados["status"] not in (
        "agendada", "realizada", "cancelada"
    ):
        raise HTTPException(
            status_code=400,
            detail="Status inválido"
        )

    campos = ", ".join(
        f"{campo} = :{campo}" for campo in dados
    )

    dados["consulta_id"] = consulta_id

    with engine.begin() as conexao:
        resultado = conexao.execute(
            text(f"""
                UPDATE consultas
                SET {campos}
                WHERE id = :consulta_id
                  AND ativo = TRUE
                RETURNING id
            """),
            dados
        )

        id_atualizado = resultado.scalar_one_or_none()

    if id_atualizado is None:
        raise HTTPException(
            status_code=404,
            detail="Consulta não encontrada"
        )

    return {
        "mensagem": "Consulta atualizada com sucesso!",
        "id": id_atualizado
    }


@app.delete("/consultas/{consulta_id}")
def cancelar_consulta(consulta_id: int):
    with engine.begin() as conexao:
        resultado = conexao.execute(
            text("""
                UPDATE consultas
                SET status = 'cancelada'
                WHERE id = :consulta_id
                  AND ativo = TRUE
                  AND status = 'agendada'
                RETURNING id
            """),
            {"consulta_id": consulta_id}
        )

        id_cancelado = resultado.scalar_one_or_none()

    if id_cancelado is None:
        raise HTTPException(
            status_code=404,
            detail="Consulta não encontrada ou não pode ser cancelada"
        )

    return {
        "mensagem": "Consulta cancelada com sucesso!",
        "id": id_cancelado
    }