7. Documentação dos endpoints

Nesta seção, apresentamos as rotas disponíveis na API privada da clínica, o que cada uma faz e quais dados precisam ser enviados. A documentação foi baseada no arquivo OpenAPI gerado pelo próprio sistema.

- Versão da API: 1.0.0.
- Versão OpenAPI: 3.1.0.
- Endereço base: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- Especificação OpenAPI: http://127.0.0.1:8000/openapi.json
- Total de operações: 32.

7.1 Endpoints gerais

Essas duas rotas servem para verificar se a API está funcionando e se consegue se conectar ao banco de dados.

| Método | Endpoint | Descrição | Sucesso |
|---|---|---|---|
| GET | / | Rota inicial da API | 200 |
| GET | /teste-banco | Verificar conexão com o banco | 200 |

7.2 Endereços e integração ViaCEP

Nesta parte, o sistema permite consultar endereços pelo CEP, buscar endereços já cadastrados e atualizar seus dados.

| Método | Endpoint | Descrição | Sucesso |
|---|---|---|---|
| GET | /cep/{cep} | Consultar e salvar endereço pelo CEP | 200 |
| GET | /enderecos/{endereco_id} | Buscar endereço | 200 |
| PUT | /enderecos/{endereco_id} | Atualizar endereço | 200 |

Parâmetros: cep (texto obrigatório) e endereco_id (inteiro obrigatório).

Modelo EnderecoUpdate:

| Campo | Tipo | Obrigatório |
|---|---|---|
| logradouro | Texto | Não |
| bairro | Texto | Não |
| cidade | Texto | Não |
| uf | Texto | Não |

Os campos possuem valor padrão vazio na especificação.

7.3 Gerenciamento de tutores

As rotas de tutores permitem cadastrar, consultar, atualizar, excluir, inativar e reativar os responsáveis pelos animais.

| Método | Endpoint | Descrição | Sucesso |
|---|---|---|---|
| POST | /tutores | Cadastrar tutor | 200 |
| GET | /tutores | Listar tutores | 200 |
| GET | /tutores/{tutor_id} | Buscar tutor | 200 |
| PUT | /tutores/{tutor_id} | Atualizar tutor | 200 |
| DELETE | /tutores/{tutor_id} | Excluir tutor | 200 |
| PATCH | /tutores/{tutor_id}/inativar | Inativar tutor | 200 |
| PATCH | /tutores/{tutor_id}/ativar | Reativar tutor | 200 |

Modelo TutorCreate:

| Campo | Tipo | Obrigatório |
|---|---|---|
| nome_completo | Texto | Sim |
| cpf | Texto | Sim |
| data_nascimento | Texto | Sim |
| email | Texto | Sim |
| telefone | Texto | Sim |
| endereco_id | Inteiro | Sim |

Modelo TutorUpdate:

| Campo | Tipo | Obrigatório |
|---|---|---|
| nome_completo | Texto | Sim |
| data_nascimento | Texto | Sim |
| email | Texto | Sim |
| telefone | Texto | Sim |
| endereco_id | Inteiro | Sim |

O modelo TutorUpdate utiliza os mesmos campos obrigatórios, exceto o CPF, que não está presente no modelo de atualização.

7.4 Veterinários e autenticação

Este módulo reúne o cadastro dos veterinários e as operações de entrada e saída do sistema.

| Método | Endpoint | Descrição | Sucesso |
|---|---|---|---|
| POST | /veterinarios | Cadastrar veterinário | 200 |
| PATCH | /veterinarios/{veterinario_id}/confirmar-senha | Confirmar senha | 200 |
| POST | /login | Autenticar veterinário | 200 |
| POST | /logout | Encerrar sessão | 200 |

Modelo VeterinarioCreate:

| Campo | Tipo | Obrigatório |
|---|---|---|
| nome_completo | Texto | Sim |
| cpf | Texto | Sim |
| crmv | Texto | Sim |
| uf_crmv | Texto | Sim |
| email | Texto | Sim |
| telefone | Texto | Sim |
| senha | Texto | Sim |

Modelo LoginRequest:

| Campo | Tipo | Obrigatório |
|---|---|---|
| email | Texto | Sim |
| senha | Texto | Sim |

Exemplo de requisição de login com dados fictícios:

{
  "email": "veterinario@exemplo.com",
  "senha": "senha_de_teste"
}

7.5 Gerenciamento de animais

Aqui ficam as operações de cadastro, consulta, atualização e desativação dos animais atendidos pela clínica.

| Método | Endpoint | Descrição | Sucesso |
|---|---|---|---|
| POST | /animais | Cadastrar animal | 201 |
| GET | /animais | Listar animais | 200 |
| GET | /animais/{animal_id} | Buscar animal | 200 |
| PUT | /animais/{animal_id} | Atualizar animal | 200 |
| DELETE | /animais/{animal_id} | Desativar animal | 200 |

Modelo AnimalCadastro:

| Campo | Tipo | Obrigatório |
|---|---|---|
| nome | Texto | Sim |
| especie_id | Inteiro | Sim |
| raca_id | Inteiro | Não |
| tutor_id | Inteiro | Não |
| sexo | Texto | Não |
| cor | Texto | Não |
| peso_atual | Decimal | Não |

Modelo AnimalAtualizacao:

| Campo | Tipo | Obrigatório |
|---|---|---|
| nome | Texto | Não |
| sexo | Texto | Não |
| cor | Texto | Não |
| peso_atual | Decimal | Não |

Validações:

- Nome entre 1 e 100 caracteres.
- Identificadores informados devem ser maiores que zero.
- Peso informado deve ser maior que zero.

Nenhum campo de AnimalAtualizacao é individualmente obrigatório no esquema OpenAPI.

7.6 Gerenciamento de microchips RFID

O sistema permite cadastrar microchips vinculados aos animais e localizar registros pelo código do chip.

| Método | Endpoint | Descrição | Sucesso |
|---|---|---|---|
| POST | /microchips | Cadastrar microchip | 201 |
| GET | /microchips | Listar microchips | 200 |
| GET | /microchips/codigo/{codigo} | Buscar microchip pelo código | 200 |

Modelo MicrochipCadastro:

| Campo | Tipo | Obrigatório |
|---|---|---|
| animal_id | Inteiro | Sim |
| codigo | Texto | Sim |
| data_implantacao | Data | Não |
| observacoes | Texto | Não |

Validações:

- Identificador do animal maior que zero.
- Código entre 1 e 50 caracteres.
- Data no formato AAAA-MM-DD.

7.7 Gerenciamento de consultas

As consultas podem ser cadastradas, pesquisadas, atualizadas ou canceladas.

| Método | Endpoint | Descrição | Sucesso |
|---|---|---|---|
| POST | /consultas | Cadastrar consulta | 201 |
| GET | /consultas | Listar consultas | 200 |
| GET | /consultas/{consulta_id} | Buscar consulta | 200 |
| PUT | /consultas/{consulta_id} | Atualizar consulta | 200 |
| DELETE | /consultas/{consulta_id} | Cancelar consulta | 200 |

Modelo ConsultaCadastro:

| Campo | Tipo | Obrigatório |
|---|---|---|
| animal_id | Inteiro | Sim |
| veterinario_id | Inteiro | Não |
| data_hora | Data e hora | Sim |
| motivo | Texto | Não |
| observacoes | Texto | Não |

Modelo ConsultaAtualizacao:

| Campo | Tipo | Obrigatório |
|---|---|---|
| data_hora | Data e hora | Não |
| motivo | Texto | Não |
| status | Texto | Não |
| observacoes | Texto | Não |

Os campos de atualização são individualmente opcionais no esquema OpenAPI.

7.8 Gerenciamento de vacinas e comunicação governamental

Este módulo registra as vacinações, permite consultar o histórico e oferece uma rota para reenviar a comunicação de vacinação.

| Método | Endpoint | Descrição | Sucesso |
|---|---|---|---|
| POST | /vacinas | Registrar vacinação | 201 |
| GET | /vacinas | Listar vacinas | 200 |
| POST | /vacinas/{vacina_id}/reenviar | Reenviar comunicação de vacinação | 200 |

Modelo VacinaCadastro:

| Campo | Tipo | Obrigatório |
|---|---|---|
| animal_id | Inteiro | Sim |
| nome | Texto | Sim |
| antirrabica | Booleano | Não |
| fabricante | Texto | Não |
| lote | Texto | Sim |
| dose | Texto | Sim |
| data_aplicacao | Data | Sim |
| data_proxima_dose | Data | Não |
| observacoes | Texto | Não |

O campo antirrabica possui valor padrão false e permite identificar as vacinas classificadas como antirrábicas.

Parâmetros de consulta: O endpoint GET /vacinas aceita o parâmetro opcional animal_id, permitindo consultar as vacinações relacionadas a um animal específico.

Exemplo: GET /vacinas?animal_id=1.

7.9 Autenticação e controle de acesso

A especificação OpenAPI apresenta o cabeçalho authorization nas operações dos módulos de endereços, tutores, animais, microchips, consultas, vacinas e logout.

Para as requisições autenticadas, utiliza-se o padrão Bearer:

Authorization: Bearer TOKEN_DE_ACESSO

O cabeçalho aparece como opcional na especificação OpenAPI. A obrigatoriedade efetiva da autenticação deve ser verificada nas regras implementadas no backend.

7.10 Códigos de resposta HTTP

Os códigos de resposta explicitamente documentados na especificação OpenAPI são:

| Código | Significado |
|---|---|
| 200 | Operação realizada com sucesso |
| 201 | Registro criado com sucesso |
| 422 | Erro de validação dos dados |

Outros códigos HTTP podem ser retornados pelas regras de negócio do backend, mas não estão detalhados na especificação analisada.

7.11 Documentação interativa

O Swagger UI permite consultar os endpoints, visualizar os modelos de requisição, identificar os campos obrigatórios e executar requisições diretamente pelo navegador.

O arquivo openapi.json disponibiliza a especificação da API em formato estruturado, permitindo sua importação em ferramentas como Postman e facilitando a reprodução dos testes.

7.12 Considerações finais

A API privada possui 32 operações documentadas, distribuídas entre os módulos gerais, endereços, tutores, veterinários, autenticação, animais, microchips, consultas e vacinas.

Com essa documentação, a equipe pode consultar as rotas e entender quais dados são necessários para integrar o frontend e realizar os testes da API.

O escopo deste documento é a API privada; a especificação da API governamental independente e os resultados dos testes não estão incluídos.
