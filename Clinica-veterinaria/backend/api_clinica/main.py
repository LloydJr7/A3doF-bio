from fastapi import FastAPI, HTTPException
import httpx
from conexao import get_connection
from passlib.context import CryptContext


app = FastAPI(title="API Clínica Veterinária - Teste")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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

@app.get("/cep/{cep}")
def buscar_e_salvar_cep(cep: str):
    cep_limpo = cep.replace("-", "").replace(" ", "")
    
    if len(cep_limpo) != 8:
        raise HTTPException(status_code=400, detail="CEP inválido. Por favor, informe 8 dígitos.")

    url_viacep = f"https://viacep.com.br/ws/{cep_limpo}/json/"
    response = httpx.get(url_viacep)

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
            INSERT INTO endereco (logradouro, numero, bairro, cidade, uf, cep)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id;
        """
        cursor.execute(query, (
            dados_cep.get("logradouro", ""),
            "S/N",
            dados_cep.get("bairro", ""),
            dados_cep.get("localidade", ""),
            dados_cep.get("uf", ""),
            dados_cep.get("cep", "")
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



from pydantic import BaseModel

class TutorCreate(BaseModel):
    nome_completo: str
    cpf: str
    data_nascimento: str
    email: str
    telefone: str
    endereco_id: int

@app.post("/tutores")
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

        return {
            "mensagem": "Login realizado com sucesso!",
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

class TutorUpdate(BaseModel):
    nome_completo: str
    data_nascimento: str
    email: str
    telefone: str
    endereco_id: int

@app.get("/tutores")
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

@app.get("/tutores/{tutor_id}")
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

@app.put("/tutores/{tutor_id}")
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

@app.patch("/tutores/{tutor_id}/inativar")
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