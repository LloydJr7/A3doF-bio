
from datetime import date
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from database import engine


app = FastAPI(
    title="Sistema de Clinica Veterinaria",
    description="API para gerenciamento de animais, microchips e consultas",
    version="1.0.0"
)


# Rota inicial
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
                    a.sexo,
                    a.cor,
                    a.peso_atual
                FROM animais a
                JOIN especies e
                    ON a.especie_id = e.id
                LEFT JOIN racas r
                    ON a.raca_id = r.id
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


# modelo para atualizar os dados de um animal
class AnimalAtualizacao(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=100)
    sexo: str | None = None
    cor: str | None = None
    peso_atual: float | None = Field(default=None, gt=0)


# atualizar os dados de um animal
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
                RETURNING id
            """),
            dados
        )

        id_atualizado = resultado.scalar_one_or_none()

    if id_atualizado is None:
        raise HTTPException(
            status_code=404,
            detail="Animal não encontrado"
        )

    return {
        "mensagem": "Animal atualizado com sucesso!",
        "id": id_atualizado
    }


#desativar um animal sem apagar seu cadastro
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


# Modelo para cadastrar microchips
class MicrochipCadastro(BaseModel):
    animal_id: int = Field(gt=0)
    codigo: str = Field(min_length=1, max_length=50)
    data_implantacao: date | None = None
    observacoes: str | None = None


# Cadastrar microchip em um animal
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


# Listar todos os microchips cadastrados
@app.get("/microchips")
def listar_microchips():
    with engine.connect() as conexao:
        resultado = conexao.execute(
            text("""
                SELECT
                    m.id,
                    m.animal_id,
                    a.nome AS animal,
                    m.codigo,
                    m.data_implantacao,
                    m.observacoes,
                    m.ativo
                FROM microchips m
                JOIN animais a
                    ON m.animal_id = a.id
                ORDER BY m.id
            """)
        )

        microchips = resultado.mappings().all()

    return [dict(microchip) for microchip in microchips]


# Buscar um animal pelo código do microchip
@app.get("/microchips/codigo/{codigo}")
def buscar_microchip_por_codigo(codigo: str):
    with engine.connect() as conexao:
        resultado = conexao.execute(
            text("""
                SELECT
                    m.id AS microchip_id,
                    m.codigo,
                    m.data_implantacao,
                    m.observacoes,
                    a.id AS animal_id,
                    a.nome AS animal,
                    e.nome AS especie,
                    r.nome AS raca,
                    a.sexo,
                    a.cor,
                    a.peso_atual
                FROM microchips m
                JOIN animais a
                    ON m.animal_id = a.id
                JOIN especies e
                    ON a.especie_id = e.id
                LEFT JOIN racas r
                    ON a.raca_id = r.id
                WHERE m.codigo = :codigo
                  AND m.ativo = TRUE
                  AND a.ativo = TRUE
            """),
            {"codigo": codigo}
        )

        microchip = resultado.mappings().first()

    if microchip is None:
        raise HTTPException(
            status_code=404,
            detail="Microchip não encontrado ou inativo"
        )

    return dict(microchip)

