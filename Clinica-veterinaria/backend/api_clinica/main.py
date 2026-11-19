import secrets
from datetime import date, datetime
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from passlib.context import CryptContext
from sqlalchemy import text
import httpx
from conexao import get_connection
from database import engine

app = FastAPI(
    title="Sistema de Clinica Veterinaria",
    description="API unificada da Clínica Veterinária",
    version="1.0.0"
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessoes_ativas: dict[str, int] = {}


def verificar_autenticacao(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Acesso negado. Faça login para continuar.")
    token = authorization.replace("Bearer ", "").strip()
    if token not in sessoes_ativas:
        raise HTTPException(status_code=401, detail="Sessão inválida ou expirada. Faça login novamente.")
    return sessoes_ativas[token]


@app.get("/")
def home():
    return {"status": "API da Clínica Veterinária está funcionando com sucesso!"}


@app.get("/teste-banco")
def teste_banco():
    conn = get_connection()
    if conn:
        conn.close()
        return {"status": "Conexão com o PostgreSQL funcionando com sucesso!"}
    return {"error": "Não foi possível conectar ao banco de dados."}


@app.get("/cep/{cep}", dependencies=[Depends(verificar_autenticacao)])
def buscar_e_salvar_cep(cep: str):
    cep_limpo = cep.replace("-", "").replace(" ", "")

    if len(cep_limpo) != 8:
        raise HTTPException(status_code=400, detail="CEP inválido. Por favor, informe 8 dígitos.")

    url_viacep = f"https://viacep.com.br/ws/{cep_limpo}/json/"
    try:
        response = httpx.get(url_viacep, timeout=8.0)
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Serviço ViaCEP indisponível no momento.")

    if response.status_code != 200 or "erro" in response.json():
        raise HTTPException(status_code=404, detail="CEP não encontrado no ViaCEP.")

    dados_cep = response.json()

    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Erro de conexão com o banco de dados.")

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM endereco WHERE cep = %s", (dados_cep["cep"],))
        endereco_existente = cursor.fetchone()

        if endereco_existente:
            conn.close()
            return {
                "mensagem": "Endereço já cadastrado no banco!",
                "endereco_id": endereco_existente["id"],
                "dados": dados_cep
            }

        query = """
            INSERT INTO endereco (logradouro, numero, bairro, cidade, uf, cep, codigo_ibge)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """
        cursor.execute(query, (
            dados_cep.get("logradouro", ""),
            "S/N",
            dados_cep.get("bairro", ""),
            dados_cep.get("localidade", ""),
            dados_cep.get("uf", ""),
            dados_cep.get("cep", ""),
            dados_cep.get("ibge", "")
        ))
        novo_id = cursor.fetchone()["id"]
        conn.commit()
        conn.close()

        return {
            "mensagem": "Endereço buscado no ViaCEP e salvo com sucesso no banco!",
            "endereco_id": novo_id,
            "dados": dados_cep
        }
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Erro ao salvar endereço no banco: {str(e)}")


class EnderecoUpdate(BaseModel):
    logradouro: str = ""
    bairro: str = ""
    cidade: str = ""
    uf: str = ""


@app.get("/enderecos/{endereco_id}", dependencies=[Depends(verificar_autenticacao)])
def buscar_endereco(endereco_id: int):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Erro de conexão com o banco de dados.")
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id, logradouro, numero, bairro, cidade, uf, cep FROM endereco WHERE id = %s;",
            (endereco_id,)
        )
        endereco = cursor.fetchone()
        conn.close()
        if not endereco:
            raise HTTPException(status_code=404, detail="Endereço não encontrado.")
        return endereco
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Erro ao buscar endereço: {str(e)}")


@app.put("/enderecos/{endereco_id}", dependencies=[Depends(verificar_autenticacao)])
def atualizar_endereco(endereco_id: int, dados: EnderecoUpdate):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Erro de conexão com o banco de dados.")
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE endereco
            SET logradouro = %s, bairro = %s, cidade = %s, uf = %s
            WHERE id = %s
            RETURNING id;
            """,
            (
                dados.logradouro.strip(),
                dados.bairro.strip(),
                dados.cidade.strip(),
                dados.uf.strip().upper(),
                endereco_id
            )
        )
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Endereço não encontrado.")
        conn.commit()
        conn.close()
        return {"mensagem": "Endereço atualizado com sucesso!"}
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar endereço: {str(e)}")


class TutorCreate(BaseModel):
    nome_completo: str
    cpf: str
    data_nascimento: str
    email: str
    telefone: str
    endereco_id: int


class TutorUpdate(BaseModel):
    nome_completo: str
    data_nascimento: str
    email: str
    telefone: str
    endereco_id: int


@app.post("/tutores", dependencies=[Depends(verificar_autenticacao)])
def cadastrar_tutor(tutor: TutorCreate):
    cpf_limpo = tutor.cpf.replace(".", "").replace("-", "").replace(" ", "")

    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Erro de conexão com o banco de dados.")

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM tutor WHERE cpf = %s", (cpf_limpo,))
        if cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail="CPF já cadastrado no sistema.")

        query = """
            INSERT INTO tutor (nome_completo, cpf, data_nascimento, email, telefone, endereco_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id;
        """
        cursor.execute(query, (
            tutor.nome_completo,
            cpf_limpo,
            tutor.data_nascimento,
            tutor.email,
            tutor.telefone,
            tutor.endereco_id
        ))
        novo_id = cursor.fetchone()["id"]
        conn.commit()
        conn.close()

        return {
            "mensagem": "Tutor cadastrado com sucesso!",
            "tutor_id": novo_id
        }
    except HTTPException as http_ex:
        conn.close()
        raise http_ex
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Erro ao cadastrar tutor: {str(e)}")


@app.get("/tutores", dependencies=[Depends(verificar_autenticacao)])
def listar_tutores():
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Erro de conexão com o banco de dados.")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM tutor ORDER BY id;")
        tutores = cursor.fetchall()
        conn.close()
        return tutores
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Erro ao listar tutores: {str(e)}")


@app.get("/tutores/{tutor_id}", dependencies=[Depends(verificar_autenticacao)])
def buscar_tutor(tutor_id: int):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Erro de conexão com o banco de dados.")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM tutor WHERE id = %s;", (tutor_id,))
        tutor = cursor.fetchone()
        conn.close()
        if not tutor:
            raise HTTPException(status_code=404, detail="Tutor não encontrado.")
        return tutor
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Erro ao buscar tutor: {str(e)}")


@app.put("/tutores/{tutor_id}", dependencies=[Depends(verificar_autenticacao)])
def atualizar_tutor(tutor_id: int, dados: TutorUpdate):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Erro de conexão com o banco de dados.")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM tutor WHERE id = %s;", (tutor_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Tutor não encontrado.")

        query = """
            UPDATE tutor 
            SET nome_completo = %s, data_nascimento = %s, email = %s, telefone = %s, endereco_id = %s
            WHERE id = %s;
        """
        cursor.execute(query, (
            dados.nome_completo,
            dados.data_nascimento,
            dados.email,
            dados.telefone,
            dados.endereco_id,
            tutor_id
        ))
        conn.commit()
        conn.close()
        return {"mensagem": "Dados do tutor atualizados com sucesso!"}
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar tutor: {str(e)}")


@app.patch("/tutores/{tutor_id}/inativar", dependencies=[Depends(verificar_autenticacao)])
def inativar_tutor(tutor_id: int):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Erro de conexão com o banco de dados.")
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE tutor SET situacao = 'INATIVO' WHERE id = %s RETURNING id;", (tutor_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Tutor não encontrado.")
        conn.commit()
        conn.close()
        return {"mensagem": "Tutor inativado com sucesso!"}
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Erro ao inativar tutor: {str(e)}")


@app.patch("/tutores/{tutor_id}/ativar", dependencies=[Depends(verificar_autenticacao)])
def ativar_tutor(tutor_id: int):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Erro de conexão com o banco de dados.")
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE tutor SET situacao = 'ATIVO' WHERE id = %s RETURNING id",
            (tutor_id,)
        )
        tutor_atualizado = cursor.fetchone()
        if not tutor_atualizado:
            conn.close()
            raise HTTPException(status_code=404, detail="Tutor não encontrado.")
        conn.commit()
        cursor.close()
        conn.close()
        return {"mensagem": "Tutor reativado com sucesso!"}
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Erro ao ativar tutor: {str(e)}")


@app.delete("/tutores/{tutor_id}", dependencies=[Depends(verificar_autenticacao)])
def excluir_tutor(tutor_id: int):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Erro de conexão com o banco de dados.")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) AS total FROM animais WHERE tutor_id = %s", (tutor_id,))
        resultado = cursor.fetchone()
        qtd_animais = resultado["total"] if isinstance(resultado, dict) else resultado[0]

        if qtd_animais > 0:
            cursor.close()
            conn.close()
            raise HTTPException(
                status_code=400,
                detail="Não é possível excluir este tutor pois ele possui animais vinculados. Inative-o em vez de excluir."
            )

        cursor.execute("DELETE FROM tutor WHERE id = %s RETURNING id", (tutor_id,))
        deletado = cursor.fetchone()
        if not deletado:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Tutor não encontrado.")

        conn.commit()
        cursor.close()
        conn.close()
        return {"mensagem": "Tutor excluído com sucesso!"}
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Erro ao excluir tutor: {str(e)}")


class VeterinarioCreate(BaseModel):
    nome_completo: str
    cpf: str
    crmv: str
    uf_crmv: str
    email: str
    telefone: str
    senha: str


class LoginRequest(BaseModel):
    email: str
    senha: str


@app.post("/veterinarios")
def cadastrar_veterinario(vet: VeterinarioCreate):
    cpf_limpo = vet.cpf.replace(".", "").replace("-", "").replace(" ", "")
    senha_criptografada = pwd_context.hash(vet.senha)

    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Erro de conexão com o banco de dados.")

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM veterinario WHERE cpf = %s OR email = %s", (cpf_limpo, vet.email))
        if cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail="CPF ou E-mail já cadastrado.")

        query = """
            INSERT INTO veterinario (nome_completo, cpf, crmv, uf_crmv, email, telefone, senha_hash, senha_confirmada)
            VALUES (%s, %s, %s, %s, %s, %s, %s, FALSE)
            RETURNING id;
        """
        cursor.execute(query, (
            vet.nome_completo,
            cpf_limpo,
            vet.crmv,
            vet.uf_crmv.upper(),
            vet.email,
            vet.telefone,
            senha_criptografada
        ))
        novo_id = cursor.fetchone()["id"]
        conn.commit()
        conn.close()

        return {
            "mensagem": "Veterinário cadastrado! Confirme a senha para liberar o acesso.",
            "veterinario_id": novo_id
        }
    except HTTPException as http_ex:
        conn.close()
        raise http_ex
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Erro ao cadastrar veterinário: {str(e)}")


@app.patch("/veterinarios/{veterinario_id}/confirmar-senha")
def confirmar_senha_veterinario(veterinario_id: int):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Erro de conexão com o banco de dados.")

    cursor = conn.cursor()
    try:
        query = """
            UPDATE veterinario 
            SET senha_confirmada = TRUE, data_confirmacao = CURRENT_TIMESTAMP 
            WHERE id = %s 
            RETURNING id;
        """
        cursor.execute(query, (veterinario_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Veterinário não encontrado.")
        conn.commit()
        conn.close()
        return {"mensagem": "Senha confirmada com sucesso! Acesso liberado."}
    except HTTPException as http_ex:
        conn.close()
        raise http_ex
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Erro ao confirmar senha: {str(e)}")


@app.post("/login")
def login_veterinario(dados: LoginRequest):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Erro de conexão com o banco de dados.")

    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id, nome_completo, crmv, uf_crmv, senha_hash, senha_confirmada, situacao FROM veterinario WHERE email = %s",
            (dados.email,)
        )
        vet = cursor.fetchone()

        if not vet or not pwd_context.verify(dados.senha, vet["senha_hash"]):
            conn.close()
            raise HTTPException(status_code=401, detail="E-mail ou senha incorretos.")

        if vet["situacao"] != "ATIVO":
            conn.close()
            raise HTTPException(status_code=403, detail="Conta de veterinário inativa.")

        if not vet["senha_confirmada"]:
            conn.close()
            raise HTTPException(status_code=403, detail="Acesso bloqueado. Confirme sua senha antes de entrar.")

        cursor.execute("UPDATE veterinario SET ultimo_acesso = CURRENT_TIMESTAMP WHERE id = %s", (vet["id"],))
        conn.commit()
        conn.close()

        token = secrets.token_hex(32)
        sessoes_ativas[token] = vet["id"]

        return {
            "mensagem": "Login realizado com sucesso!",
            "token": token,
            "veterinario": {
                "id": vet["id"],
                "nome_completo": vet["nome_completo"],
                "crmv": f"{vet['crmv']}-{vet['uf_crmv']}"
            }
        }
    except HTTPException as http_ex:
        conn.close()
        raise http_ex
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Erro ao realizar login: {str(e)}")


@app.post("/logout")
def logout_veterinario(authorization: str = Header(None)):
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "").strip()
        sessoes_ativas.pop(token, None)
    return {"mensagem": "Sessão encerrada com sucesso."}


class AnimalCadastro(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    especie_id: int = Field(gt=0)
    raca_id: int | None = Field(default=None, gt=0)
    tutor_id: int | None = Field(default=None, gt=0)
    sexo: str | None = None
    cor: str | None = None
    peso_atual: float | None = Field(default=None, gt=0)


@app.post("/animais", status_code=201, dependencies=[Depends(verificar_autenticacao)])
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


@app.get("/animais", dependencies=[Depends(verificar_autenticacao)])
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


@app.get("/animais/{animal_id}", dependencies=[Depends(verificar_autenticacao)])
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


@app.put("/animais/{animal_id}", dependencies=[Depends(verificar_autenticacao)])
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


@app.delete("/animais/{animal_id}", dependencies=[Depends(verificar_autenticacao)])
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


@app.post("/microchips", status_code=201, dependencies=[Depends(verificar_autenticacao)])
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


@app.get("/microchips", dependencies=[Depends(verificar_autenticacao)])
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


@app.get("/microchips/codigo/{codigo}", dependencies=[Depends(verificar_autenticacao)])
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


@app.post("/consultas", status_code=201, dependencies=[Depends(verificar_autenticacao)])
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


@app.get("/consultas", dependencies=[Depends(verificar_autenticacao)])
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


@app.get("/consultas/{consulta_id}", dependencies=[Depends(verificar_autenticacao)])
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


@app.put("/consultas/{consulta_id}", dependencies=[Depends(verificar_autenticacao)])
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


@app.delete("/consultas/{consulta_id}", dependencies=[Depends(verificar_autenticacao)])
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