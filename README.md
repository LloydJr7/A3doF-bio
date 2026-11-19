# 🐾 Sistema de Gestão de Clínica Veterinária (A3 - SDM)

Sistema web full-stack para gerenciamento de clínica veterinária, Integrando controle de acesso de veterinários, cadastro de tutores com integração à API pública ViaCEP, gerenciamento de animais, implementação e busca de microchips e agendamento de consultas.

---

## 🛠️ Tecnologias Utilizadas

- **Backend:** Python 3, FastAPI, Uvicorn, Pydantic, Passlib (bcrypt), HTTPX, SQLAlchemy e Psycopg2.
- **Banco de Dados:** PostgreSQL (`clinica_db`).
- **Frontend:** HTML5, CSS3 e JavaScript (Fetch API com interceptação global de autenticação).
- **Integração Externa:** API Pública [ViaCEP](https://viacep.com.br/).

---

## 📁 Estrutura do Repositório

```text
├── README.md
└── Clinica-veterinaria/
    ├── banco/
    │   └── db.sql                       # Script de criação das tabelas no PostgreSQL
    ├── backend/
    │   ├── api_clinica/
    │   │   ├── main.py                  # API RESTful FastAPI, regras de negócio e autenticação
    │   │   ├── conexao.py               # Conexão direta com PostgreSQL (psycopg2)
    │   │   └── database.py              # Engine SQLAlchemy
    │   └── api_governamental/           # Módulo de integração governamental e vacinas
    └── frontend/
        ├── css/                         # Folhas de estilo padronizadas por módulo
        ├── js/
        │   ├── auth.js                  # Interceptador global de requisições e controle de sessão
        │   ├── login.js                 # Cadastro, confirmação de senha e login de veterinários
        │   ├── index.js                 # Painel principal com indicadores em tempo real
        │   ├── tutores.js               # CRUD de tutores e integração ViaCEP
        │   ├── animais.js               # CRUD de animais
        │   ├── microchips.js            # Cadastro e consulta rápida por código de microchip
        │   └── consultas.js             # Agendamento, atualização e cancelamento de consultas
        └── pages/
            ├── login.html               # Tela de autenticação e registro de veterinário
            ├── index.html               # Dashboard inicial
            ├── tutores.html             # Gestão de tutores e endereços
            ├── animais.html             # Gestão de animais
            ├── microchips.html          # Gestão de microchips
            └── consultas.html           # Gestão de consultas

⚙️ Pré-requisitos e Instalação

1. Banco de Dados PostgreSQL:

    • Crie o banco clinica_db no PostgreSQL e execute o script Clinica-veterinaria/banco/db.sql para criar todas as tabelas e relacionamentos.

    • Configure as credenciais de acesso no arquivo .env dentro de Clinica-veterinaria/backend/api_clinica/.

2. Ambiente Virtual e Dependências Python:
    cd Clinica-veterinaria/backend/api_clinica
    python -m venv venv
    # Windows:
    venv\Scripts\activate
    # Linux/Mac:
    source venv/bin/activate

    pip install fastapi uvicorn psycopg2-binary sqlalchemy pydantic passlib[bcrypt] httpx python-dotenv

▶️ Como Executar o Sistema

1. Iniciar o Backend (API):
Dentro de Clinica-veterinaria/backend/api_clinica (com o venv ativado), execute:
    uvicorn main:app --reload
    • API disponível em: http://127.0.0.1:8000
    • Documentação interativa (Swagger UI): http://127.0.0.1:8000/docs

2. Iniciar o Frontend:
    • Abra Clinica-veterinaria/frontend/pages/login.html utilizando a extensão Live Server no VS Code (ou diretamente no navegador).

🔐 Regras de Negócio e Segurança
    •Autenticação e Controle de Acesso: Senhas armazenadas com hash bcrypt, fluxo de confirmação de cadastro em 6 dígitos e proteção de todas as rotas privadas via token Bearer (auth.js + Depends(verificar_autenticacao)).

    •Integração ViaCEP: Preenchimento automático de endereço a partir do CEP, com suporte a complementação manual de logradouro, bairro, cidade e UF persistida no PostgreSQL.

    •Integridade Referencial: Impede a exclusão física de tutores que possuam animais vinculados (exigindo inativação). Animais e consultas utilizam exclusão lógica (ativo = FALSE / status cancelada).

    •Microchips: Garante unicidade do código e impede múltiplos microchips ativos para o mesmo animal.