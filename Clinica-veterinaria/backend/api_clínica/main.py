
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
