from fastapi import FastAPI, HTTPException
import httpx
from conexao import get_connection

app = FastAPI(title="API Clínica Veterinária - Teste")

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