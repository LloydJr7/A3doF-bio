import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(
    title="API Governamental Simulada - Registro Animal e Antirrábica",
    description="Serviço externo simulado para controle de microchips RFID e vacinação antirrábica",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = Path(__file__).resolve().parent / "governo.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS animais_governo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            microchip TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            especie TEXT NOT NULL,
            raca TEXT,
            tutor_cpf TEXT,
            data_cadastro TEXT NOT NULL,
            data_atualizacao TEXT
        );

        CREATE TABLE IF NOT EXISTS vacinacoes_governo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            protocolo TEXT UNIQUE NOT NULL,
            idempotency_key TEXT UNIQUE NOT NULL,
            id_vacinacao_clinica INTEGER,
            microchip TEXT,
            animal_nome TEXT NOT NULL,
            especie TEXT NOT NULL,
            vacina_nome TEXT NOT NULL,
            fabricante TEXT,
            lote TEXT NOT NULL,
            dose TEXT NOT NULL,
            data_aplicacao TEXT NOT NULL,
            veterinario_crmv TEXT NOT NULL,
            veterinario_uf TEXT NOT NULL,
            data_recebimento TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()


init_db()


class AnimalGovernoCreate(BaseModel):
    microchip: str = Field(min_length=1, max_length=50)
    nome: str = Field(min_length=1, max_length=100)
    especie: str = Field(min_length=1, max_length=50)
    raca: str | None = None
    tutor_cpf: str | None = None


class AnimalGovernoUpdate(BaseModel):
    nome: str | None = None
    especie: str | None = None
    raca: str | None = None
    tutor_cpf: str | None = None


class AnimalPayload(BaseModel):
    id_clinica: int
    nome: str
    especie: str
    microchip: str | None = None


class VacinaPayload(BaseModel):
    nome: str
    fabricante: str | None = None
    lote: str
    dose: str
    data_aplicacao: str
    data_proxima_dose: str | None = None


class VeterinarioPayload(BaseModel):
    crmv: str
    uf_crmv: str


class VacinacaoAntirrabicaRequest(BaseModel):
    id_vacinacao_clinica: int
    animal: AnimalPayload
    vacina: VacinaPayload
    veterinario: VeterinarioPayload


@app.get("/")
def health():
    return {"status": "API Governamental Simulada online"}


@app.post("/api/governo/animais", status_code=201)
def cadastrar_animal_governo(dados: AnimalGovernoCreate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM animais_governo WHERE microchip = ?", (dados.microchip.strip(),))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=409, detail="Microchip já cadastrado na base governamental.")

    agora = datetime.now().isoformat()
    cursor.execute(
        """
        INSERT INTO animais_governo (microchip, nome, especie, raca, tutor_cpf, data_cadastro)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (dados.microchip.strip(), dados.nome.strip(), dados.especie.strip(), dados.raca, dados.tutor_cpf, agora)
    )
    conn.commit()
    conn.close()
    return {"mensagem": "Animal registrado na base governamental.", "microchip": dados.microchip.strip()}


@app.get("/api/governo/animais/{microchip}")
def consultar_animal_governo(microchip: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM animais_governo WHERE microchip = ?", (microchip.strip(),))
    animal = cursor.fetchone()
    conn.close()
    if not animal:
        raise HTTPException(status_code=404, detail="Animal não encontrado na base governamental.")
    return dict(animal)


@app.put("/api/governo/animais/{microchip}")
def atualizar_animal_governo(microchip: str, dados: AnimalGovernoUpdate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM animais_governo WHERE microchip = ?", (microchip.strip(),))
    atual = cursor.fetchone()
    if not atual:
        conn.close()
        raise HTTPException(status_code=404, detail="Animal não encontrado na base governamental.")

    novo_nome = dados.nome if dados.nome is not None else atual["nome"]
    nova_especie = dados.especie if dados.especie is not None else atual["especie"]
    nova_raca = dados.raca if dados.raca is not None else atual["raca"]
    novo_cpf = dados.tutor_cpf if dados.tutor_cpf is not None else atual["tutor_cpf"]
    agora = datetime.now().isoformat()

    cursor.execute(
        """
        UPDATE animais_governo
        SET nome = ?, especie = ?, raca = ?, tutor_cpf = ?, data_atualizacao = ?
        WHERE microchip = ?
        """,
        (novo_nome, nova_especie, nova_raca, novo_cpf, agora, microchip.strip())
    )
    conn.commit()
    conn.close()
    return {"mensagem": "Dados do animal atualizados na base governamental.", "microchip": microchip.strip()}


@app.post("/api/governo/vacinacoes-antirrabicas", status_code=201)
def registrar_vacinacao_antirrabica(
    dados: VacinacaoAntirrabicaRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")
):
    if not dados.animal.microchip or not dados.animal.microchip.strip():
        raise HTTPException(
            status_code=422,
            detail="Validação governamental: o animal precisa possuir microchip RFID vinculado."
        )

    chave = (idempotency_key or f"clinica-{dados.id_vacinacao_clinica}").strip()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT protocolo, data_recebimento FROM vacinacoes_governo WHERE idempotency_key = ?", (chave,))
    existente = cursor.fetchone()
    if existente:
        conn.close()
        return {
            "mensagem": "Solicitação já processada anteriormente (idempotência garantida).",
            "protocolo": existente["protocolo"],
            "data_recebimento": existente["data_recebimento"]
        }

    protocolo = f"GOV-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    agora = datetime.now().isoformat()

    cursor.execute(
        """
        INSERT INTO vacinacoes_governo (
            protocolo, idempotency_key, id_vacinacao_clinica, microchip,
            animal_nome, especie, vacina_nome, fabricante, lote, dose,
            data_aplicacao, veterinario_crmv, veterinario_uf, data_recebimento
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            protocolo, chave, dados.id_vacinacao_clinica, dados.animal.microchip.strip(),
            dados.animal.nome, dados.animal.especie, dados.vacina.nome, dados.vacina.fabricante,
            dados.vacina.lote, dados.vacina.dose, dados.vacina.data_aplicacao,
            dados.veterinario.crmv, dados.veterinario.uf_crmv, agora
        )
    )
    conn.commit()
    conn.close()

    return {
        "mensagem": "Vacinação antirrábica registrada com sucesso no sistema governamental.",
        "protocolo": protocolo,
        "data_recebimento": agora
    }


@app.get("/api/governo/operacoes/{protocolo}")
def consultar_operacao_governo(protocolo: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vacinacoes_governo WHERE protocolo = ?", (protocolo.strip(),))
    operacao = cursor.fetchone()
    conn.close()
    if not operacao:
        raise HTTPException(status_code=404, detail="Protocolo não encontrado.")
    return dict(operacao)